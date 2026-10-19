from typing import Any

from django.apps import AppConfig
from django.conf import settings
from django.db import connection
from django.db.models.signals import pre_migrate
from django.dispatch import receiver
from psycopg2 import sql

import logging

logger = logging.getLogger(__name__)


@receiver(pre_migrate)
def create_schema(sender: AppConfig, **kwargs: Any) -> None:
    schema = settings.DATABASE_SCHEMA
    with connection.cursor() as cursor:
        # CREATE SCHEMA IF NOT EXISTS checks the CREATE privilege on the database
        # before it looks at the schema, so a role that merely owns a pre-provisioned
        # schema would be refused.
        cursor.execute("SELECT 1 FROM pg_namespace WHERE nspname = %s", [schema])
        if cursor.fetchone():
            return
        logger.info("Creating schema %s", schema)
        cursor.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema)))
