import json
import uuid

from django.conf import settings
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from psycopg2 import sql

from PyADCSConnector.utils.certificate_fingerprint import certificate_fingerprint

S = settings.DATABASE_SCHEMA


class SharedCertificateStoreMigrationTest(TransactionTestCase):
    """
    Exercises migration 0001_initial -> 0002_shared_certificate_store against
    legacy-shaped discovery_certificate data (raw rows with base64content and a
    plain discovery_id int, as they existed before the shared certificate store).

    Verifies: exact-string fingerprint de-duplication, association preservation,
    dangling discovery_id cleanup, base64content column removal, and the resulting
    schema shape (unique fingerprint index, FKs, index on certificate_id, discovery_id
    now bigint).

    Deliberately a single test method: this app's models declare fully
    schema-qualified db_table values (e.g. '"pyadcs"."certificate"'), which Django's
    introspection-based `flush` (used by TransactionTestCase between test methods)
    fails to match against bare introspected table names, so it silently skips
    flushing them. A single method keeps the whole seed -> migrate -> assert cycle
    self-contained in one setUp, sidestepping that mismatch; individual assertion
    groups are still reported separately via subTest.

    Migration 0002 is intentionally, unambiguously irreversible (its data
    RunPython/RunSQL steps have no reverse_code/reverse_sql), so this fixture cannot
    seed 0001-shaped data by reversing an already-applied 0002 -- that path would now
    raise IrreversibleError, and even before that change it left discovery_id
    physically bigint (only the migration *state* rolled back to int), which would
    have quietly skipped exercising a genuine int->bigint conversion. Instead, this
    test drops and recreates the whole schema so migrating to 0001 is a real forward
    apply from nothing, guaranteeing discovery_id is genuinely a plain integer column
    before the legacy rows go in and 0002 forward-migrates them for real.
    """

    migrate_from = [("PyADCSConnector", "0001_initial")]
    migrate_to = [("PyADCSConnector", "0002_shared_certificate_store")]

    # Legacy discovery_certificate content values, keyed by scenario.
    CERT_SHARED = "U0hBUkVEX0NFUlRfQ09OVEVOVA=="  # shared across two discoveries
    CERT_DUP_ONE = "RFVQTElDQVRFRF9JTl9PTkVfRElTQ09WRVJZ"  # duplicated within one discovery
    CERT_WS_A = "V0hJVEVTUEFDRV9WQVJJQU5UX0E="  # whitespace-sensitive pair:
    CERT_WS_B = CERT_WS_A + " "  # ...differs only by a trailing space, must NOT dedup
    CERT_DANGLING = "REFOR0xJTkdfQ0VSVElGSUNBVEU="  # attached to a non-existent discovery

    def setUp(self):
        # Genuinely fresh start: drop the whole schema (django_migrations included --
        # it lives here too, since the connection's search_path is pinned to this
        # schema) and recreate it empty, so the migrate-to-0001 below is a real
        # forward apply from nothing rather than a reverse of an already-applied 0002.
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(S)))
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(S)))

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        executor.loader.build_graph()

        # Seed two real discoveries using the historical (0001) model state.
        old_apps = executor.loader.project_state(self.migrate_from).apps
        history_model = old_apps.get_model("PyADCSConnector", "DiscoveryHistory")
        discovery_a = history_model.objects.create(
            uuid=uuid.uuid4(), name="disco-a", status="COMPLETED", meta=None
        )
        discovery_b = history_model.objects.create(
            uuid=uuid.uuid4(), name="disco-b", status="COMPLETED", meta=None
        )
        self.discovery_a_id = discovery_a.id
        self.discovery_b_id = discovery_b.id
        # Guaranteed not to exist in discovery_history.
        self.dangling_discovery_id = discovery_b.id + 1000

        # (base64content, discovery_id, meta) legacy rows.
        legacy_rows = [
            (self.CERT_SHARED, self.discovery_a_id, {"scenario": "shared", "side": "a"}),
            (self.CERT_SHARED, self.discovery_b_id, {"scenario": "shared", "side": "b"}),
            (self.CERT_DUP_ONE, self.discovery_a_id, {"scenario": "dup-one", "copy": 1}),
            (self.CERT_DUP_ONE, self.discovery_a_id, {"scenario": "dup-one", "copy": 2}),
            (self.CERT_WS_A, self.discovery_a_id, {"scenario": "ws-a"}),
            (self.CERT_WS_B, self.discovery_b_id, {"scenario": "ws-b"}),
            (self.CERT_DANGLING, self.dangling_discovery_id, {"scenario": "dangling"}),
        ]

        # Track every seeded row by its own uuid so post-migration assertions can
        # verify each surviving discovery_certificate row individually.
        self.seeded_rows = {}
        insert_stmt = sql.SQL(
            "INSERT INTO {}.{} (uuid, base64content, discovery_id, meta) "
            "VALUES (%s, %s, %s, %s)"
        ).format(sql.Identifier(S), sql.Identifier("discovery_certificate"))
        with connection.cursor() as cursor:
            for base64content, discovery_id, meta in legacy_rows:
                row_uuid = uuid.uuid4()
                self.seeded_rows[str(row_uuid)] = {
                    "base64content": base64content,
                    "discovery_id": discovery_id,
                    "meta": meta,
                }
                cursor.execute(
                    insert_stmt,
                    [str(row_uuid), base64content, discovery_id, json.dumps(meta)],
                )

        self.dangling_row_uuid = next(
            row_uuid
            for row_uuid, row in self.seeded_rows.items()
            if row["meta"]["scenario"] == "dangling"
        )

        # Run the migration under test.
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(self.migrate_to)
        self.new_apps = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        # This test seeds real discoveries/certificates/join rows (and 0002's forward
        # RunPython seeds a CertificateCleanupState row) directly against the shared
        # schema, which -- as noted above -- TransactionTestCase's flush cannot clear
        # between runs. setUp's schema drop/recreate already makes this test's own
        # re-run self-cleaning, but delete the seeded rows explicitly anyway: this is
        # the only place they're created, and leaving them around would otherwise be
        # the sole source of leftover data for anything else that inspects this
        # (--keepdb'd) database afterward.
        history_model = self.new_apps.get_model("PyADCSConnector", "DiscoveryHistory")
        certificate_model = self.new_apps.get_model("PyADCSConnector", "Certificate")
        cleanup_state_model = self.new_apps.get_model("PyADCSConnector", "CertificateCleanupState")

        history_model.objects.filter(id__in=[self.discovery_a_id, self.discovery_b_id]).delete()
        certificate_model.objects.all().delete()
        cleanup_state_model.objects.all().delete()

    def test_migration_0001_to_0002(self):
        certificate_model = self.new_apps.get_model("PyADCSConnector", "Certificate")
        discovery_certificate_model = self.new_apps.get_model("PyADCSConnector", "DiscoveryCertificate")

        with self.subTest("exact-match content collapses to a single certificate"):
            self.assertEqual(certificate_model.objects.filter(base64content=self.CERT_SHARED).count(), 1)
            self.assertEqual(certificate_model.objects.filter(base64content=self.CERT_DUP_ONE).count(), 1)

        with self.subTest("whitespace-varied content does NOT dedup"):
            self.assertEqual(certificate_model.objects.filter(base64content=self.CERT_WS_A).count(), 1)
            self.assertEqual(certificate_model.objects.filter(base64content=self.CERT_WS_B).count(), 1)
            cert_ws_a = certificate_model.objects.get(base64content=self.CERT_WS_A)
            cert_ws_b = certificate_model.objects.get(base64content=self.CERT_WS_B)
            self.assertNotEqual(cert_ws_a.id, cert_ws_b.id)
            self.assertNotEqual(cert_ws_a.fingerprint, cert_ws_b.fingerprint)
            self.assertEqual(cert_ws_a.fingerprint, certificate_fingerprint(self.CERT_WS_A))
            self.assertEqual(cert_ws_b.fingerprint, certificate_fingerprint(self.CERT_WS_B))

        with self.subTest("fingerprint matches the documented sha256(utf8) helper"):
            cert_shared = certificate_model.objects.get(base64content=self.CERT_SHARED)
            self.assertEqual(cert_shared.fingerprint, certificate_fingerprint(self.CERT_SHARED))

        with self.subTest("dangling discovery_id row removed entirely"):
            self.assertFalse(
                discovery_certificate_model.objects.filter(uuid=self.dangling_row_uuid).exists()
            )

        with self.subTest("dangling-only content is never inserted as an orphan certificate"):
            # The dangling row's content exists nowhere else, so the backfill (which
            # only sources rows whose discovery still exists) must not create a
            # certificate for it -- the upgrade leaves no immediately-orphaned rows.
            self.assertEqual(
                certificate_model.objects.filter(base64content=self.CERT_DANGLING).count(), 0
            )
            # Exactly the four distinct still-referenced contents survive as certificates.
            self.assertEqual(certificate_model.objects.count(), 4)

        with self.subTest("every surviving join row keeps its uuid/meta and gets a valid certificate"):
            surviving_rows = list(discovery_certificate_model.objects.all())
            surviving_uuids = {str(row.uuid) for row in surviving_rows}
            expected_surviving_uuids = set(self.seeded_rows) - {self.dangling_row_uuid}
            self.assertSetEqual(surviving_uuids, expected_surviving_uuids)

            valid_cert_ids = set(certificate_model.objects.values_list("id", flat=True))
            for row in surviving_rows:
                seeded = self.seeded_rows[str(row.uuid)]
                self.assertIn(row.certificate_id, valid_cert_ids)
                self.assertEqual(row.meta, seeded["meta"])
                self.assertEqual(row.discovery_id, seeded["discovery_id"])
                linked_cert = certificate_model.objects.get(id=row.certificate_id)
                self.assertEqual(linked_cert.base64content, seeded["base64content"])

        with self.subTest("join-row counts for valid discoveries are preserved"):
            self.assertEqual(
                discovery_certificate_model.objects.filter(discovery_id=self.discovery_a_id).count(), 4
            )
            self.assertEqual(
                discovery_certificate_model.objects.filter(discovery_id=self.discovery_b_id).count(), 2
            )
            self.assertEqual(discovery_certificate_model.objects.count(), 6)

        with self.subTest("shared certificate is referenced by both discoveries"):
            cert_shared = certificate_model.objects.get(base64content=self.CERT_SHARED)
            shared_links = discovery_certificate_model.objects.filter(certificate_id=cert_shared.id)
            self.assertEqual(shared_links.count(), 2)
            self.assertSetEqual(
                set(shared_links.values_list("discovery_id", flat=True)),
                {self.discovery_a_id, self.discovery_b_id},
            )

        with self.subTest("cert duplicated within one discovery collapses but both links survive"):
            cert_dup_one = certificate_model.objects.get(base64content=self.CERT_DUP_ONE)
            dup_links = discovery_certificate_model.objects.filter(certificate_id=cert_dup_one.id)
            self.assertEqual(dup_links.count(), 2)
            self.assertTrue(all(link.discovery_id == self.discovery_a_id for link in dup_links))

        with self.subTest("base64content column removed from discovery_certificate"):
            with connection.cursor() as cursor:
                columns = {
                    col.name
                    for col in connection.introspection.get_table_description(
                        cursor, "discovery_certificate"
                    )
                }
            self.assertNotIn("base64content", columns)

        with self.subTest("schema shape: unique fingerprint, FKs, index, bigint discovery_id"):
            with connection.cursor() as cursor:
                cert_constraints = connection.introspection.get_constraints(cursor, "certificate")
                self.assertTrue(
                    any(
                        c["unique"] and c["columns"] == ["fingerprint"]
                        for c in cert_constraints.values()
                    ),
                    f"expected a unique constraint on certificate.fingerprint, got: {cert_constraints}",
                )

                dc_constraints = connection.introspection.get_constraints(
                    cursor, "discovery_certificate"
                )

                fk_targets = {
                    (c["foreign_key"][0], tuple(c["columns"]))
                    for c in dc_constraints.values()
                    if c.get("foreign_key")
                }
                self.assertIn(("certificate", ("certificate_id",)), fk_targets)
                self.assertIn(("discovery_history", ("discovery_id",)), fk_targets)

                self.assertTrue(
                    any(
                        c["index"] and c["columns"] == ["certificate_id"]
                        for c in dc_constraints.values()
                    ),
                    f"expected an index on discovery_certificate.certificate_id, got: {dc_constraints}",
                )

                dc_columns = connection.introspection.get_table_description(
                    cursor, "discovery_certificate"
                )
                discovery_id_col = next(c for c in dc_columns if c.name == "discovery_id")
                # Postgres OID 20 == int8/bigint.
                self.assertEqual(discovery_id_col.type_code, 20)
