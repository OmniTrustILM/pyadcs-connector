import base64
import json
import uuid
from datetime import timedelta
from unittest.mock import MagicMock, patch

import psycopg2
from django.conf import settings
from django.db import connection
from django.test import TransactionTestCase, override_settings
from django.utils import timezone

from PyADCSConnector.models.authority_instance import AuthorityInstance
from PyADCSConnector.models.certificate import Certificate
from PyADCSConnector.models.certificate_cleanup_state import CertificateCleanupState
from PyADCSConnector.models.discovery_certificate import DiscoveryCertificate
from PyADCSConnector.models.discovery_history import DiscoveryHistory
from PyADCSConnector.objects.discovery_history_request_dto import DiscoveryHistoryRequestDto
from PyADCSConnector.services import certificate_cleanup
from PyADCSConnector.services.attributes.discovery_attributes import (
    DISCOVERY_AUTHORITY_INSTANCE_ATTRIBUTE_NAME,
    DISCOVERY_CONFIGSTRING_ATTRIBUTE_NAME,
    DISCOVERY_SELECT_CA_METHOD_ATTRIBUTE_NAME,
)
from PyADCSConnector.services.certificate_cleanup import run_cleanup_once
from PyADCSConnector.services.discovery_history import (
    create_discovery_history,
    discover_certificates,
    get_discovery_history_data,
    run_discovery,
)
from PyADCSConnector.utils.certificate_fingerprint import certificate_fingerprint
from PyADCSConnector.utils.discovery_status import DiscoveryStatus
from PyADCSConnector.utils.dump_parser import DumpParser, ParseResult


def _competing_connection():
    """A second, independent connection to the same database the tests run against,
    used to hold or probe the advisory lock that discovery persistence uses.

    Built from Django's own connection parameters so the test database name, socket
    vs TCP host, and any OPTIONS are exactly what Django itself connects with; a
    connect timeout keeps a misconfigured environment from hanging the suite.
    """
    params = connection.get_connection_params()
    params.setdefault("connect_timeout", 10)
    return psycopg2.connect(**params)


class DiscoveryDeduplicationTests(TransactionTestCase):
    """
    Exercises discover_certificates persistence (shared Certificate store +
    DiscoveryCertificate join) and the read/delete paths that were restructured
    to match, WITHOUT touching real WinRM: the
    authority session and DumpParser.parse_certificates are mocked so
    discover_certificates runs its real dedup/persistence logic against
    caller-supplied fake certificate content.

    Note on isolation: as documented in tests_migration.py, this app's models
    declare schema-qualified db_table values (e.g. '"pyadcs"."certificate"'),
    which defeats TransactionTestCase's introspection-based flush between test
    methods AND between test classes in the same run -- rows are committed for
    real and are NOT wiped automatically. Every test method below therefore
    (a) uses its own uuid-suffixed discovery names / certificate content (see
    self.run_id) and scopes assertions to the objects it itself created, and
    (b) explicitly tears down everything it inserted in tearDown(), so a
    later test module (e.g. tests_migration.py, which migrates this same
    schema backward and forward) starts from a clean slate rather than
    tripping over leftover discovery_certificate/certificate rows.
    """

    def setUp(self):
        self.run_id = uuid.uuid4().hex[:12]
        self._discovery_ids = []
        self.authority = AuthorityInstance.objects.create(
            name=f"authority-{self.run_id}",
            address="ca.example.local",
            https=False,
            port=5985,
            attributes={},
            credential={},
            kind="PyADCS-WinRM",
        )

    def tearDown(self):
        # Cascades DiscoveryCertificate join rows via the FK; any Certificate
        # left with no remaining discovery_links is this test's own orphan
        # and is safe to remove too, keeping the shared schema clean for
        # whichever test module runs next.
        DiscoveryHistory.objects.filter(id__in=self._discovery_ids).delete()
        Certificate.objects.filter(discovery_links__isnull=True).delete()
        self.authority.delete()

    # -- helpers ----------------------------------------------------------

    def _b64(self, label):
        """A distinct, deterministic fake base64 certificate payload."""
        return base64.b64encode(f"cert-content-{label}-{self.run_id}".encode()).decode()

    def _request_dto(self, name):
        return {
            "name": f"{name}-{self.run_id}",
            "kind": "PyADCS-WinRM",
            "attributes": [
                {"name": DISCOVERY_SELECT_CA_METHOD_ATTRIBUTE_NAME, "content": [{"data": "configstring"}]},
                {
                    "name": DISCOVERY_AUTHORITY_INSTANCE_ATTRIBUTE_NAME,
                    "content": [{"data": {"uuid": str(self.authority.uuid), "name": self.authority.name}}],
                },
                {
                    "name": DISCOVERY_CONFIGSTRING_ATTRIBUTE_NAME,
                    "content": [{"data": "ca.example.local\\Test CA"}],
                },
            ],
        }

    def _run_discovery(self, name, certs):
        """
        Creates a DiscoveryHistory and runs discover_certificates against it,
        faking the WinRM collection to return `certs` -- a list of
        (base64content, template_name) tuples -- as if they were parsed from
        the ADCS dump. Returns the refreshed DiscoveryHistory.
        """
        request_dto = self._request_dto(name)
        discovery_history = create_discovery_history(request_dto)
        fake_results = [ParseResult(template, content) for content, template in certs]

        with patch(
            "PyADCSConnector.services.discovery_history.create_session_from_authority_instance",
            return_value=MagicMock(),
        ), patch.object(DumpParser, "parse_certificates", return_value=fake_results):
            discover_certificates(request_dto, discovery_history)

        discovery_history.refresh_from_db()
        self._discovery_ids.append(discovery_history.id)
        return discovery_history

    @staticmethod
    def _paging_request(page_number, items_per_page):
        return DiscoveryHistoryRequestDto(None, None, page_number, items_per_page)

    # -- tests --------------------------------------------------------------

    def test_dedup_across_two_discoveries(self):
        """Same certificate content discovered by two separate discoveries
        collapses to a single Certificate row, with one join row per
        discovery, each carrying its own uuid/meta."""
        shared_cert = self._b64("shared")

        d1 = self._run_discovery("disco-shared-1", [(shared_cert, "WebServer")])
        d2 = self._run_discovery("disco-shared-2", [(shared_cert, "User")])

        fingerprint = certificate_fingerprint(shared_cert)
        self.assertEqual(Certificate.objects.filter(fingerprint=fingerprint).count(), 1)
        shared_certificate = Certificate.objects.get(fingerprint=fingerprint)
        self.assertEqual(shared_certificate.base64content, shared_cert)

        link1 = DiscoveryCertificate.objects.get(discovery_id=d1.id)
        link2 = DiscoveryCertificate.objects.get(discovery_id=d2.id)
        self.assertEqual(link1.certificate_id, shared_certificate.id)
        self.assertEqual(link2.certificate_id, shared_certificate.id)
        self.assertNotEqual(link1.uuid, link2.uuid)
        self.assertNotEqual(link1.meta, link2.meta)

        resp1 = get_discovery_history_data(self._paging_request(1, 10), d1)
        self.assertEqual(resp1.total_certificates_discovered, 1)
        self.assertEqual(len(resp1.certificate_data), 1)
        self.assertEqual(resp1.certificate_data[0]["uuid"], link1.uuid)
        self.assertEqual(resp1.certificate_data[0]["base64Content"], shared_cert)
        self.assertEqual(resp1.certificate_data[0]["meta"], link1.meta)

        resp2 = get_discovery_history_data(self._paging_request(1, 10), d2)
        self.assertEqual(resp2.total_certificates_discovered, 1)
        self.assertEqual(len(resp2.certificate_data), 1)
        self.assertEqual(resp2.certificate_data[0]["uuid"], link2.uuid)
        self.assertEqual(resp2.certificate_data[0]["base64Content"], shared_cert)
        self.assertEqual(resp2.certificate_data[0]["meta"], link2.meta)

    def test_duplicate_within_one_discovery_preserves_both_rows(self):
        """The same certificate discovered twice within a single discovery
        still yields two join rows (duplicate count preserved), backed by a
        single Certificate row."""
        dup_cert = self._b64("dup-in-one")

        d = self._run_discovery("disco-dup-one", [(dup_cert, "WebServer"), (dup_cert, "WebServer")])

        fingerprint = certificate_fingerprint(dup_cert)
        self.assertEqual(Certificate.objects.filter(fingerprint=fingerprint).count(), 1)

        links = list(DiscoveryCertificate.objects.filter(discovery_id=d.id))
        self.assertEqual(len(links), 2)
        self.assertNotEqual(links[0].uuid, links[1].uuid)
        for link in links:
            self.assertEqual(link.certificate.fingerprint, fingerprint)

        resp = get_discovery_history_data(self._paging_request(1, 100), d)
        self.assertEqual(resp.total_certificates_discovered, 2)
        self.assertEqual(len(resp.certificate_data), 2)

    def test_response_shape_order_and_pagination_parity(self):
        """DTO shape, order_by('uuid'), pagination math, and the reported
        total match the pre-dedup semantics -- just sourced via the join."""
        certs = [(self._b64(f"resp-{i}"), "WebServer") for i in range(3)]

        d = self._run_discovery("disco-resp-parity", certs)

        all_links = list(DiscoveryCertificate.objects.filter(discovery_id=d.id).order_by("uuid"))
        self.assertEqual(len(all_links), 3)

        # itemsPerPage=2 forces a second page; pageNumber is 1-indexed at the
        # DTO boundary (get_discovery_history_data converts to 0-indexed).
        resp_page1 = get_discovery_history_data(self._paging_request(1, 2), d)
        resp_page2 = get_discovery_history_data(self._paging_request(2, 2), d)

        self.assertEqual(resp_page1.total_certificates_discovered, 3)
        self.assertEqual(resp_page2.total_certificates_discovered, 3)
        self.assertEqual(len(resp_page1.certificate_data), 2)
        self.assertEqual(len(resp_page2.certificate_data), 1)

        combined = resp_page1.certificate_data + resp_page2.certificate_data
        self.assertEqual(len(combined), len(all_links))
        for entry, link in zip(combined, all_links):
            self.assertEqual(set(entry.keys()), {"uuid", "base64Content", "meta"})
            self.assertEqual(entry["uuid"], link.uuid)
            self.assertEqual(entry["base64Content"], link.certificate.base64content)
            self.assertEqual(entry["meta"], link.meta)

    def test_delete_discovery_cascades_join_rows_and_preserves_shared_certificate(self):
        """Deleting a DiscoveryHistory cascades its DiscoveryCertificate join
        rows via the ORM FK, but leaves a Certificate still referenced by
        another discovery untouched (removing newly-orphaned certificates is
        the scheduled sweep's job, not the delete path's)."""
        shared_cert = self._b64("delete-shared")

        d1 = self._run_discovery("disco-del-1", [(shared_cert, "WebServer")])
        d2 = self._run_discovery("disco-del-2", [(shared_cert, "WebServer")])

        fingerprint = certificate_fingerprint(shared_cert)
        certificate_id = Certificate.objects.get(fingerprint=fingerprint).id
        self.assertTrue(DiscoveryCertificate.objects.filter(discovery_id=d1.id).exists())

        d1.delete()

        self.assertFalse(DiscoveryCertificate.objects.filter(discovery_id=d1.id).exists())
        self.assertTrue(DiscoveryCertificate.objects.filter(discovery_id=d2.id).exists())
        self.assertTrue(Certificate.objects.filter(id=certificate_id).exists())

    def test_fingerprint_python_sql_parity(self):
        """certificate_fingerprint(x) must match Postgres'
        encode(sha256(convert_to(x,'UTF8')),'hex') exactly, including for
        content with embedded newlines/tabs, since migration 0002 used this SQL
        expression to compute the same fingerprints the discovery path computes
        in Python."""
        samples = [
            "cGxhaW4tYmFzZTY0LWNvbnRlbnQ=" + self.run_id,  # plain
            "d3JhcHBlZC1iYXNlNjQtY29udGVudA==\nTU9SRV9MSU5FX1RXTw==\nQU5EX0xJTkVfVEhSRUU=",  # newline-wrapped
            "dGFiLXNlcGFyYXRlZC1jb250ZW50\t\tsuffix\tvalue",  # tab-containing
        ]
        with connection.cursor() as cursor:
            for sample in samples:
                with self.subTest(sample=sample):
                    python_fingerprint = certificate_fingerprint(sample)
                    cursor.execute("SELECT encode(sha256(convert_to(%s, 'UTF8')), 'hex')", [sample])
                    sql_fingerprint = cursor.fetchone()[0]
                    self.assertEqual(python_fingerprint, sql_fingerprint)

    def test_new_certificates_inserted_in_ascending_fingerprint_order(self):
        """Two concurrent discoveries inserting overlapping NEW fingerprints
        in different orders can deadlock in Postgres; discover_certificates
        must always hand bulk_create a deterministic (ascending-fingerprint)
        list regardless of the order certificates were collected in. This is
        a deterministic, single-threaded assertion on the argument order --
        not a flaky real-thread race."""
        candidates = [self._b64(f"order-{i}") for i in range(5)]
        # Feed discover_certificates the certs in descending-fingerprint
        # order: an implementation that didn't sort would then hand
        # bulk_create that same (wrong) descending order.
        candidates.sort(key=certificate_fingerprint, reverse=True)
        certs = [(content, "WebServer") for content in candidates]

        original_bulk_create = Certificate.objects.bulk_create
        captured = {}

        def _capturing_bulk_create(objs, **kwargs):
            objs = list(objs)
            captured["fingerprints"] = [o.fingerprint for o in objs]
            return original_bulk_create(objs, **kwargs)

        request_dto = self._request_dto("disco-order")
        discovery_history = create_discovery_history(request_dto)
        fake_results = [ParseResult(template, content) for content, template in certs]

        with patch(
            "PyADCSConnector.services.discovery_history.create_session_from_authority_instance",
            return_value=MagicMock(),
        ), patch.object(DumpParser, "parse_certificates", return_value=fake_results), patch.object(
            Certificate.objects, "bulk_create", side_effect=_capturing_bulk_create,
        ):
            discover_certificates(request_dto, discovery_history)
        self._discovery_ids.append(discovery_history.id)

        self.assertIn("fingerprints", captured)
        self.assertEqual(captured["fingerprints"], sorted(captured["fingerprints"]))
        # Sanity check the test actually set up a non-trivial (not already
        # ascending) input order, so the assertion above is meaningful.
        self.assertNotEqual([certificate_fingerprint(c) for c in candidates], captured["fingerprints"])

    def test_discover_certificates_returns_early_if_discovery_deleted_before_persistence(self):
        """If the DiscoveryHistory row is gone by the time the (post-WinRM)
        persistence transaction runs -- e.g. deleted by a concurrent DELETE
        while collection was still in progress -- discover_certificates must
        return quietly rather than resurrect the discovery, raise, or
        persist anything."""
        cert = self._b64("deleted-during-collection")
        request_dto = self._request_dto("disco-deleted-mid-flight")
        discovery_history = create_discovery_history(request_dto)
        discovery_id = discovery_history.id

        # Simulate a concurrent DELETE landing after WinRM collection
        # finished (mocked below) but before the persistence transaction runs.
        DiscoveryHistory.objects.filter(id=discovery_id).delete()

        fake_results = [ParseResult("WebServer", cert)]
        with patch(
            "PyADCSConnector.services.discovery_history.create_session_from_authority_instance",
            return_value=MagicMock(),
        ), patch.object(DumpParser, "parse_certificates", return_value=fake_results):
            discover_certificates(request_dto, discovery_history)  # must not raise

        fingerprint = certificate_fingerprint(cert)
        self.assertFalse(DiscoveryCertificate.objects.filter(discovery_id=discovery_id).exists())
        self.assertFalse(Certificate.objects.filter(fingerprint=fingerprint).exists())

    def test_run_discovery_marks_failed_status_on_exception(self):
        """run_discovery's except-branch uses a filtered .update() (not
        discovery_history.save()) precisely so a concurrently-deleted
        discovery isn't resurrected; this test exercises the normal
        (still-existing) case: status flips to FAILED with a failure-reason
        meta entry, and the original exception still propagates to the
        caller/thread."""
        request_dto = self._request_dto("disco-run-fails")
        discovery_history = create_discovery_history(request_dto)
        self._discovery_ids.append(discovery_history.id)

        boom = RuntimeError("simulated WinRM failure")
        with patch(
            "PyADCSConnector.services.discovery_history.create_session_from_authority_instance",
            side_effect=boom,
        ):
            with self.assertRaises(RuntimeError):
                run_discovery(request_dto, discovery_history.uuid)

        discovery_history.refresh_from_db()
        self.assertEqual(discovery_history.status, DiscoveryStatus.FAILED.value)
        self.assertEqual(len(discovery_history.meta), 1)
        self.assertEqual(discovery_history.meta[0]["content"][0]["data"], str(boom))


class CertificateCleanupTests(TransactionTestCase):
    """
    Exercises the scheduled orphan sweep (run_cleanup_once): the
    advisory-lock-gated, DB-clock-leased, batched DELETE that removes
    Certificate rows with no remaining discovery_certificate join rows.

    Same schema-qualified-table caveat as DiscoveryDeduplicationTests above:
    rows (including the singleton-ish CertificateCleanupState row) are NOT
    wiped automatically between tests, so setUp/tearDown here explicitly
    reset both the cleanup-state table and any stray orphan Certificate rows
    to keep this class self-contained and safe to run repeatedly.
    """

    def setUp(self):
        self.run_id = uuid.uuid4().hex[:12]
        self._discovery_ids = []
        # Clean slate: no lease state, no pre-existing orphans from another
        # test module/run, so deleted-count assertions below are exact.
        CertificateCleanupState.objects.all().delete()
        Certificate.objects.filter(discovery_links__isnull=True).delete()

    def tearDown(self):
        DiscoveryHistory.objects.filter(id__in=self._discovery_ids).delete()
        Certificate.objects.filter(discovery_links__isnull=True).delete()
        CertificateCleanupState.objects.all().delete()

    # -- helpers ----------------------------------------------------------

    def _b64(self, label):
        return base64.b64encode(f"cleanup-cert-{label}-{self.run_id}".encode()).decode()

    def _make_certificate(self, label):
        content = self._b64(label)
        return Certificate.objects.create(
            fingerprint=certificate_fingerprint(content), base64content=content)

    def _make_discovery(self, name):
        discovery = DiscoveryHistory.objects.create(
            name=f"{name}-{self.run_id}", status=DiscoveryStatus.COMPLETED.value)
        self._discovery_ids.append(discovery.id)
        return discovery

    def _link(self, discovery, certificate):
        return DiscoveryCertificate.objects.create(
            discovery_id=discovery.id, certificate_id=certificate.id, meta=None)

    # -- tests --------------------------------------------------------------

    def test_orphan_deleted_linked_certificate_kept(self):
        """A Certificate with no discovery_certificate join row is swept;
        one still referenced by a discovery survives."""
        discovery = self._make_discovery("cleanup-linked")
        linked_certificate = self._make_certificate("linked")
        self._link(discovery, linked_certificate)
        orphan_certificate = self._make_certificate("orphan")

        deleted = run_cleanup_once()

        self.assertEqual(deleted, 1)
        self.assertFalse(Certificate.objects.filter(id=orphan_certificate.id).exists())
        self.assertTrue(Certificate.objects.filter(id=linked_certificate.id).exists())

    def test_lease_blocks_immediate_rerun_then_allows_once_due(self):
        """An immediate second call is a no-op (lease not due yet); once the
        lease is (simulated to be) due again, the sweep runs anew."""
        with override_settings(CERTIFICATE_CLEANUP_INTERVAL_SECONDS=3600):
            first_orphan = self._make_certificate("lease-first")

            first_run = run_cleanup_once()
            self.assertEqual(first_run, 1)
            self.assertFalse(Certificate.objects.filter(id=first_orphan.id).exists())

            second_orphan = self._make_certificate("lease-second")

            second_run = run_cleanup_once()
            self.assertIsNone(second_run)
            self.assertTrue(Certificate.objects.filter(id=second_orphan.id).exists())

            # Simulate the interval having elapsed since the last run.
            CertificateCleanupState.objects.update(
                last_run_at=timezone.now() - timedelta(hours=2))

            third_run = run_cleanup_once()
            self.assertEqual(third_run, 1)
            self.assertFalse(Certificate.objects.filter(id=second_orphan.id).exists())

    def test_sweep_skips_while_a_discovery_holds_the_shared_lock(self):
        """The core safety property: while another connection holds the shared
        advisory lock (as discovery persistence does), the sweep must not delete
        anything -- it cannot take the exclusive lock, so it returns None and
        leaves the lease untouched. Once that lock is released it sweeps."""
        orphan = self._make_certificate("lock-held")

        blocker = _competing_connection()
        try:
            # Transaction-scoped shared lock, held open by not committing.
            with blocker.cursor() as blocking_cursor:
                blocking_cursor.execute(
                    "SELECT pg_advisory_xact_lock_shared(%s)",
                    [settings.CERTIFICATE_CLEANUP_LOCK_KEY])

                self.assertIsNone(run_cleanup_once())
                self.assertTrue(Certificate.objects.filter(id=orphan.id).exists())
                # Lease untouched, so the sweep is still due once the lock frees.
                self.assertFalse(
                    CertificateCleanupState.objects.filter(last_run_at__isnull=False).exists())
        finally:
            blocker.rollback()  # releases the transaction-scoped lock
            blocker.close()

        self.assertEqual(run_cleanup_once(), 1)
        self.assertFalse(Certificate.objects.filter(id=orphan.id).exists())

    def test_sweep_deletes_across_multiple_batches(self):
        """With a batch size smaller than the backlog, the sweep loops until
        drained and reports the full count."""
        orphans = [self._make_certificate(f"batch-{index}") for index in range(5)]

        with override_settings(CERTIFICATE_CLEANUP_BATCH_SIZE=2):
            deleted = run_cleanup_once()

        self.assertEqual(deleted, 5)
        self.assertFalse(
            Certificate.objects.filter(id__in=[orphan.id for orphan in orphans]).exists())

    def test_exclusive_lock_is_released_between_batches(self):
        """The point of batching: the sweep must not hold its exclusive lock for
        the whole run. Probed from a second connection at every batch boundary --
        a competing shared lock (what discovery persistence takes) has to be
        grantable there, which it would not be if one lock spanned the sweep."""
        for index in range(4):
            self._make_certificate(f"release-{index}")

        real_delete_batch = certificate_cleanup._delete_orphan_batch
        shared_lock_grantable = []

        def delete_then_probe(batch_size, max_certificate_id):
            deleted = real_delete_batch(batch_size, max_certificate_id)
            probe = _competing_connection()
            try:
                with probe.cursor() as probe_cursor:
                    probe_cursor.execute(
                        "SELECT pg_try_advisory_xact_lock_shared(%s)",
                        [settings.CERTIFICATE_CLEANUP_LOCK_KEY])
                    shared_lock_grantable.append(probe_cursor.fetchone()[0])
            finally:
                probe.rollback()
                probe.close()
            return deleted

        with override_settings(CERTIFICATE_CLEANUP_BATCH_SIZE=2), patch.object(
                certificate_cleanup, "_delete_orphan_batch", delete_then_probe):
            run_cleanup_once()

        # More than one boundary observed, and the lock was free at each of them.
        self.assertGreater(len(shared_lock_grantable), 1)
        self.assertTrue(all(shared_lock_grantable))

    def test_sweep_is_bounded_to_certificates_present_at_start(self):
        """Certificates orphaned after the sweep claimed its lease are left for
        the next run, so continuous churn cannot keep a sweep -- and its lock
        contention -- going indefinitely."""
        existing = [self._make_certificate(f"churn-{index}") for index in range(3)]
        late_orphans = []
        real_delete_batch = certificate_cleanup._delete_orphan_batch

        def delete_then_churn(batch_size, max_certificate_id):
            deleted = real_delete_batch(batch_size, max_certificate_id)
            if not late_orphans:  # create a fresh orphan mid-sweep, once
                late_orphans.append(self._make_certificate("churn-late"))
            return deleted

        with override_settings(CERTIFICATE_CLEANUP_BATCH_SIZE=2), patch.object(
                certificate_cleanup, "_delete_orphan_batch", delete_then_churn):
            deleted = run_cleanup_once()

        # Only the three pre-existing orphans; the one created mid-sweep survives.
        self.assertEqual(deleted, 3)
        self.assertFalse(
            Certificate.objects.filter(id__in=[cert.id for cert in existing]).exists())
        self.assertTrue(Certificate.objects.filter(id=late_orphans[0].id).exists())


class CertificateCleanupSchedulerTests(TransactionTestCase):
    """
    Exercises start_cleanup_scheduler()'s guards -- disabled, non-positive
    interval, and the started-once/idempotent-second-call behavior -- with
    threading.Thread patched out so no real background thread or sleep loop
    ever runs.
    """

    def setUp(self):
        certificate_cleanup._started = False

    def tearDown(self):
        certificate_cleanup._started = False

    def test_disabled_starts_no_thread(self):
        with override_settings(CERTIFICATE_CLEANUP_ENABLED=False), patch(
            "PyADCSConnector.services.certificate_cleanup.threading.Thread"
        ) as thread_cls:
            certificate_cleanup.start_cleanup_scheduler()

        thread_cls.assert_not_called()
        self.assertFalse(certificate_cleanup._started)

    def test_non_positive_interval_warns_and_starts_no_thread(self):
        with override_settings(
            CERTIFICATE_CLEANUP_ENABLED=True, CERTIFICATE_CLEANUP_INTERVAL_SECONDS=0
        ), patch("PyADCSConnector.services.certificate_cleanup.threading.Thread") as thread_cls, \
                self.assertLogs("PyADCSConnector.services.certificate_cleanup", level="WARNING") as logs:
            certificate_cleanup.start_cleanup_scheduler()

        thread_cls.assert_not_called()
        self.assertFalse(certificate_cleanup._started)
        self.assertTrue(any("must be positive" in message for message in logs.output))

    def test_enabled_starts_thread_once_second_call_is_noop(self):
        with override_settings(
            CERTIFICATE_CLEANUP_ENABLED=True, CERTIFICATE_CLEANUP_INTERVAL_SECONDS=60
        ), patch("PyADCSConnector.services.certificate_cleanup.threading.Thread") as thread_cls:
            certificate_cleanup.start_cleanup_scheduler()
            certificate_cleanup.start_cleanup_scheduler()

        thread_cls.assert_called_once()
        thread_cls.return_value.start.assert_called_once()
        self.assertTrue(certificate_cleanup._started)


class DiscoveryViewsTests(TransactionTestCase):
    """
    Exercises the HTTP views in views/discovery_history.py end-to-end via
    Django's test Client: start_discovery's background Thread is patched out
    (asserting only that a DiscoveryHistory row is created, no real WinRM/
    thread runs), and discovery_operations POST (data retrieval)/DELETE are
    exercised against a discovery seeded the same way as
    DiscoveryDeduplicationTests._run_discovery above.

    Same schema-qualified-table caveat as the other classes in this module:
    tearDown explicitly cleans up everything this class creates.
    """

    def setUp(self):
        self.run_id = uuid.uuid4().hex[:12]
        self._discovery_ids = []
        self.authority = AuthorityInstance.objects.create(
            name=f"authority-views-{self.run_id}",
            address="ca.example.local",
            https=False,
            port=5985,
            attributes={},
            credential={},
            kind="PyADCS-WinRM",
        )

    def tearDown(self):
        DiscoveryHistory.objects.filter(id__in=self._discovery_ids).delete()
        Certificate.objects.filter(discovery_links__isnull=True).delete()
        self.authority.delete()

    # -- helpers ----------------------------------------------------------

    def _b64(self, label):
        return base64.b64encode(f"views-cert-{label}-{self.run_id}".encode()).decode()

    def _request_dto(self, name):
        return {
            "name": f"{name}-{self.run_id}",
            "kind": "PyADCS-WinRM",
            "attributes": [
                {"name": DISCOVERY_SELECT_CA_METHOD_ATTRIBUTE_NAME, "content": [{"data": "configstring"}]},
                {
                    "name": DISCOVERY_AUTHORITY_INSTANCE_ATTRIBUTE_NAME,
                    "content": [{"data": {"uuid": str(self.authority.uuid), "name": self.authority.name}}],
                },
                {
                    "name": DISCOVERY_CONFIGSTRING_ATTRIBUTE_NAME,
                    "content": [{"data": "ca.example.local\\Test CA"}],
                },
            ],
        }

    def _seed_discovery(self, name, certs):
        """Builds a real DiscoveryHistory + DiscoveryCertificate/Certificate
        rows by calling discover_certificates directly with WinRM mocked
        out -- same approach as DiscoveryDeduplicationTests._run_discovery."""
        request_dto = self._request_dto(name)
        discovery_history = create_discovery_history(request_dto)
        fake_results = [ParseResult(template, content) for content, template in certs]

        with patch(
            "PyADCSConnector.services.discovery_history.create_session_from_authority_instance",
            return_value=MagicMock(),
        ), patch.object(DumpParser, "parse_certificates", return_value=fake_results):
            discover_certificates(request_dto, discovery_history)

        discovery_history.refresh_from_db()
        self._discovery_ids.append(discovery_history.id)
        return discovery_history

    # -- tests --------------------------------------------------------------

    def test_start_discovery_creates_discovery_and_returns_200(self):
        body = {"name": f"view-start-{self.run_id}", "kind": "PyADCS-WinRM", "attributes": []}

        with patch("PyADCSConnector.views.discovery_history.Thread") as thread_cls:
            response = self.client.post(
                "/v1/discoveryProvider/discover", data=json.dumps(body), content_type="application/json")

        self.assertEqual(response.status_code, 200)
        thread_cls.assert_called_once()
        thread_cls.return_value.start.assert_called_once()

        created = DiscoveryHistory.objects.get(name=body["name"])
        self._discovery_ids.append(created.id)

        payload = response.json()
        self.assertEqual(payload["name"], body["name"])
        self.assertEqual(payload["uuid"], str(created.uuid))
        self.assertEqual(payload["status"], DiscoveryStatus.IN_PROGRESS.value)
        self.assertEqual(payload["certificateData"], [])
        self.assertEqual(payload["totalCertificatesDiscovered"], 0)

    def test_discovery_operations_post_existing_returns_data(self):
        cert = self._b64("post-existing")
        discovery = self._seed_discovery("view-post-existing", [(cert, "WebServer")])

        body = {"name": discovery.name, "kind": "PyADCS-WinRM", "pageNumber": 1, "itemsPerPage": 10}
        response = self.client.post(
            f"/v1/discoveryProvider/discover/{discovery.uuid}",
            data=json.dumps(body), content_type="application/json")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["uuid"], str(discovery.uuid))
        self.assertEqual(payload["name"], discovery.name)
        self.assertEqual(payload["totalCertificatesDiscovered"], 1)
        self.assertEqual(len(payload["certificateData"]), 1)
        self.assertEqual(set(payload["certificateData"][0].keys()), {"uuid", "base64Content", "meta"})

    def test_discovery_operations_post_missing_returns_404(self):
        missing_uuid = uuid.uuid4()
        body = {"name": "whatever", "kind": "PyADCS-WinRM", "pageNumber": 1, "itemsPerPage": 10}

        response = self.client.post(
            f"/v1/discoveryProvider/discover/{missing_uuid}",
            data=json.dumps(body), content_type="application/json")

        self.assertEqual(response.status_code, 404)
        self.assertIn(str(missing_uuid), response.json()["message"])

    def test_discovery_operations_delete_existing_returns_204_and_cascades(self):
        shared_cert = self._b64("delete-view-shared")
        d1 = self._seed_discovery("view-del-1", [(shared_cert, "WebServer")])
        d2 = self._seed_discovery("view-del-2", [(shared_cert, "WebServer")])
        certificate_id = Certificate.objects.get(fingerprint=certificate_fingerprint(shared_cert)).id

        response = self.client.delete(f"/v1/discoveryProvider/discover/{d1.uuid}")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(DiscoveryHistory.objects.filter(id=d1.id).exists())
        self.assertFalse(DiscoveryCertificate.objects.filter(discovery_id=d1.id).exists())
        self.assertTrue(DiscoveryHistory.objects.filter(id=d2.id).exists())
        self.assertTrue(Certificate.objects.filter(id=certificate_id).exists())

    def test_discovery_operations_delete_missing_returns_404(self):
        missing_uuid = uuid.uuid4()

        response = self.client.delete(f"/v1/discoveryProvider/discover/{missing_uuid}")

        self.assertEqual(response.status_code, 404)
        self.assertIn(str(missing_uuid), response.json()["message"])
