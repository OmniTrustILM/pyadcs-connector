import logging
import os

import django
from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.db import connection, transaction
from django.db.migrations.recorder import MigrationRecorder
from psycopg2 import sql

logger = logging.getLogger(__name__)

APP_LABEL = "PyADCSConnector"
TABLE = "django_migrations"


def adopt_stray_records(cursor, schema):
    """Move this app's records out of a django_migrations table that an earlier
    start left in another schema, so an existing install is not migrated twice.

    Only installs whose tables already live in the schema qualify; an empty
    schema is a fresh install regardless of what other schemas hold.
    """
    cursor.execute("SELECT to_regclass(%s) IS NOT NULL", [f'"{schema}"."{TABLE}"'])
    if cursor.fetchone()[0]:
        return
    own_tables = [model._meta.db_table for model in apps.get_app_config(APP_LABEL).get_models()]
    cursor.execute("SELECT bool_or(to_regclass(t) IS NOT NULL) FROM unnest(%s::text[]) AS t", [own_tables])
    if not cursor.fetchone()[0]:
        return
    # A django_migrations next to this app's tables belongs to another instance of
    # this connector using that schema; only tables elsewhere are strays.
    own_names = [table.rsplit(".", 1)[-1].strip('"') for table in own_tables]
    cursor.execute(
        "SELECT n.nspname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE c.relname = %s AND c.relkind = 'r' AND n.nspname <> %s "
        "AND has_table_privilege(c.oid, 'SELECT') "
        "AND NOT EXISTS (SELECT 1 FROM pg_class o WHERE o.relnamespace = n.oid AND o.relname = ANY(%s))",
        [TABLE, schema, own_names],
    )
    strays = [row[0] for row in cursor.fetchall()]
    if not strays:
        return

    # Django creates the table with its own DDL; the search_path puts it in the schema.
    MigrationRecorder(connection).ensure_schema()
    records = {}
    for stray in strays:
        stray_table = sql.SQL("{}.{}").format(sql.Identifier(stray), sql.Identifier(TABLE))
        cursor.execute(
            sql.SQL("DELETE FROM {} WHERE app = %s RETURNING name, applied").format(stray_table),
            [APP_LABEL],
        )
        rows = cursor.fetchall()
        records.update(dict(rows))
        logger.warning('Moved %d migration records from %s.%s to "%s".%s', len(rows), stray, TABLE, schema, TABLE)
    cursor.executemany(
        sql.SQL("INSERT INTO {}.{} (app, name, applied) VALUES (%s, %s, %s)").format(
            sql.Identifier(schema), sql.Identifier(TABLE)),
        [(APP_LABEL, name, applied) for name, applied in records.items()],
    )


if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pyadcs_connector.settings')
    django.setup()
    schema = settings.DATABASE_SCHEMA
    # One transaction keeps the whole run on a single pooled server connection, so
    # the transaction-local search_path reaches every statement -- including the
    # unqualified django_migrations table that Django creates and reads itself.
    # Every migration therefore runs inside this transaction: a migration must stay
    # atomic and cannot use CONCURRENTLY operations.
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('search_path', %s, true)", [f'"{schema}"'])
            adopt_stray_records(cursor, schema)
        call_command("migrate", APP_LABEL)
