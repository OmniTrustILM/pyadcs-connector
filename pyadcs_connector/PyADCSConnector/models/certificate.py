from django.conf import settings
from django.db import models


class Certificate(models.Model):
    fingerprint = models.CharField(max_length=64, unique=True)
    base64content = models.TextField()

    class Meta:
        db_table = f'"{settings.DATABASE_SCHEMA}"."certificate"'
