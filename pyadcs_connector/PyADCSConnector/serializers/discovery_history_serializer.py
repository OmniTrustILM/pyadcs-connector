from rest_framework import serializers
from PyADCSConnector.models.discovery_history import DiscoveryHistory


class DiscoveryHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscoveryHistory
        fields = ["uuid"]
