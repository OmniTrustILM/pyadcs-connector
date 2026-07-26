from django.conf import settings
from django.db.backends.signals import connection_created
from django.dispatch import receiver


@receiver(connection_created)
def set_search_path(sender, connection, **kwargs):
    """Set PostgreSQL search_path when a new DB connection is created."""
    with connection.cursor() as cursor:
        cursor.execute(f"SET search_path TO {settings.DATABASE_SCHEMA};")
