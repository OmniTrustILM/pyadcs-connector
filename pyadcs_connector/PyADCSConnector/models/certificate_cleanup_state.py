from django.conf import settings
from django.db import models


class CertificateCleanupState(models.Model):
    last_run_at = models.DateTimeField(null=True, default=None)

    class Meta:
        db_table = f'"{settings.DATABASE_SCHEMA}"."certificate_cleanup_state"'
