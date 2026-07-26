import uuid
import json

from django.conf import settings
from django.db import models


class AuthorityInstance(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    https = models.BooleanField(default=False)
    port = models.IntegerField()
    attributes = models.JSONField()
    credential = models.JSONField()
    kind = models.CharField(max_length=100)
    transport = models.CharField(max_length=100, default="credssp")

    def __str__(self):
        return json.dumps(self.__dict__)

    class Meta:
        db_table = f'"{settings.DATABASE_SCHEMA}"."authority_instance"'
