import uuid
import json

from django.conf import settings
from django.db import models


class DiscoveryHistory(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    status = models.CharField()
    meta = models.JSONField(null=True, default=None)

    def __str__(self):
        return json.dumps(self.__dict__)

    class Meta:
        db_table = f'"{settings.DATABASE_SCHEMA}"."discovery_history"'
