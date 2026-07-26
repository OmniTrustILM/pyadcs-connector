from rest_framework import serializers
from PyADCSConnector.models.discovery_certificate import DiscoveryCertificate


class DiscoveryCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscoveryCertificate
        fields = ["uuid"]
