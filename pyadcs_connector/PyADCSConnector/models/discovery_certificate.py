import uuid
import json

from django.conf import settings
from django.db import models

from PyADCSConnector.models.certificate import Certificate
from PyADCSConnector.models.discovery_history import DiscoveryHistory


class DiscoveryCertificate(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    meta = models.JSONField(null=True, default=None)
    discovery = models.ForeignKey(DiscoveryHistory, on_delete=models.CASCADE,
                                   db_column="discovery_id", related_name="certificate_links")
    certificate = models.ForeignKey(Certificate, on_delete=models.PROTECT,
                                     db_column="certificate_id", related_name="discovery_links")

    def __str__(self):
        return json.dumps(self.__dict__)

    class Meta:
        db_table = f'"{settings.DATABASE_SCHEMA}"."discovery_certificate"'
        # No explicit index on "certificate": the FK already auto-creates one on certificate_id.
        indexes = [models.Index(fields=["uuid"])]
