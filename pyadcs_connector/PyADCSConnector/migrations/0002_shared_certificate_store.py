from django.conf import settings
from django.db import migrations, models

# Schema prefix used for all tables (see settings.DATABASE_SCHEMA).
S = settings.DATABASE_SCHEMA

# Fingerprint expression: exact-string SHA-256 of the stored base64content, matching
# PyADCSConnector.utils.certificate_fingerprint.certificate_fingerprint() byte-for-byte.
FP = "encode(sha256(convert_to(base64content,'UTF8')),'hex')"
FP_DC = FP.replace("base64content", "dc.base64content")


def seed_certificate_cleanup_state(apps, schema_editor):
    cleanup_state_model = apps.get_model("PyADCSConnector", "CertificateCleanupState")
    cleanup_state_model.objects.using(schema_editor.connection.alias).create(last_run_at=None)


class Migration(migrations.Migration):

    atomic = True

    dependencies = [
        ("PyADCSConnector", "0001_initial"),
    ]

    operations = [
        # 1. New shared tables.
        migrations.CreateModel(
            name="Certificate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fingerprint", models.CharField(max_length=64, unique=True)),
                ("base64content", models.TextField()),
            ],
            options={
                "db_table": f'"{S}"."certificate"',
            },
        ),
        migrations.CreateModel(
            name="CertificateCleanupState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("last_run_at", models.DateTimeField(default=None, null=True)),
            ],
            options={
                "db_table": f'"{S}"."certificate_cleanup_state"',
            },
        ),
        # 2. Seed the singleton cleanup-state row.
        # No reverse_code: this migration is forward-upgrade-only (see the RunSQL backfill
        # below), so reversing it must fail loudly rather than silently leaving a
        # half-undone, inconsistent schema.
        migrations.RunPython(seed_certificate_cleanup_state),
        # 3. Add the certificate FK, nullable for now so it can be backfilled.
        migrations.AddField(
            model_name="discoverycertificate",
            name="certificate",
            field=models.ForeignKey(
                null=True,
                on_delete=models.PROTECT,
                to="PyADCSConnector.certificate",
                db_column="certificate_id",
                related_name="discovery_links",
            ),
        ),
        # 4. Backfill: dedupe base64content into certificate (only from rows whose
        #    discovery still exists, so the upgrade never creates immediately-orphaned
        #    certificate rows), point every discovery_certificate row at its
        #    certificate, then drop rows with a dangling discovery_id (no matching
        #    discovery_history).
        # No reverse_sql: the dedup (dropped duplicate rows) and the dangling-row delete
        # are lossy and cannot be undone, so this step -- and therefore the whole
        # migration -- is unambiguously irreversible (forward-upgrade only). Django
        # raises IrreversibleError rather than silently no-op'ing a partial rollback.
        migrations.RunSQL(
            sql=f"""
            INSERT INTO "{S}"."certificate" (fingerprint, base64content)
            SELECT fp, base64content FROM (
              SELECT base64content, {FP} AS fp,
                     row_number() OVER (PARTITION BY {FP} ORDER BY id) rn
              FROM "{S}"."discovery_certificate" dc
              WHERE EXISTS (SELECT 1 FROM "{S}"."discovery_history" dh WHERE dh.id = dc.discovery_id)) s WHERE rn = 1;

            UPDATE "{S}"."discovery_certificate" dc
              SET certificate_id = c.id FROM "{S}"."certificate" c
              WHERE c.fingerprint = {FP_DC};

            DELETE FROM "{S}"."discovery_certificate" dc
              WHERE NOT EXISTS (SELECT 1 FROM "{S}"."discovery_history" dh WHERE dh.id = dc.discovery_id);
            """,
        ),
        # 5. Now that every row has a certificate, enforce NOT NULL.
        migrations.AlterField(
            model_name="discoverycertificate",
            name="certificate",
            field=models.ForeignKey(
                on_delete=models.PROTECT,
                to="PyADCSConnector.certificate",
                db_column="certificate_id",
                related_name="discovery_links",
            ),
        ),
        # 6. base64content now lives solely on certificate.
        migrations.RemoveField(
            model_name="discoverycertificate",
            name="base64content",
        ),
        # 7. Turn the legacy discovery_id int column into a real FK to discovery_history,
        #    preserving the data (no drop + re-add).
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name="discoverycertificate",
                    name="discovery_id",
                ),
                migrations.AddField(
                    model_name="discoverycertificate",
                    name="discovery",
                    field=models.ForeignKey(
                        on_delete=models.CASCADE,
                        to="PyADCSConnector.discoveryhistory",
                        db_column="discovery_id",
                        related_name="certificate_links",
                    ),
                ),
            ],
            database_operations=[
                # No reverse_sql here either: dropping the constraint/index alone would
                # NOT restore the widened column back to integer, so a "reverse" would
                # leave discovery_id as bigint while the migration state claims integer
                # -- exactly the silently-inconsistent partial rollback this migration
                # must not allow.
                migrations.RunSQL(
                    sql=f"""
                    ALTER TABLE "{S}"."discovery_certificate" ALTER COLUMN discovery_id TYPE bigint;
                    CREATE INDEX IF NOT EXISTS discovery_certificate_discovery_id_idx ON "{S}"."discovery_certificate" (discovery_id);
                    ALTER TABLE "{S}"."discovery_certificate"
                      ADD CONSTRAINT dc_discovery_fk FOREIGN KEY (discovery_id)
                      REFERENCES "{S}"."discovery_history"(id) DEFERRABLE INITIALLY DEFERRED;
                    """,
                ),
            ],
        ),
        # 8. Explicit model index on uuid (certificate_id already gets an automatic FK
        #    index, so no separate AddIndex for it -- see DiscoveryCertificate.Meta).
        #    Name computed by Index.set_name_with_model() for this table/field pair; must
        #    match PyADCSConnector.models.discovery_certificate.DiscoveryCertificate.Meta.indexes
        #    exactly for `makemigrations --check` to report no drift.
        migrations.AddIndex(
            model_name="discoverycertificate",
            index=models.Index(fields=["uuid"], name="discovery_c_uuid_2cc0e3_idx"),
        ),
    ]
