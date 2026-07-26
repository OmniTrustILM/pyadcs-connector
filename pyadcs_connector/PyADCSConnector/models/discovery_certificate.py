import uuid
import json

from django.conf import settings
from django.db import models


class DiscoveryCertificate(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    base64content = models.TextField()
    discovery_id = models.IntegerField()
    meta = models.JSONField(null=True, default=None)

    def __str__(self):
        return json.dumps(self.__dict__)

    class Meta:
        db_table = f'"{settings.DATABASE_SCHEMA}"."discovery_certificate"'
