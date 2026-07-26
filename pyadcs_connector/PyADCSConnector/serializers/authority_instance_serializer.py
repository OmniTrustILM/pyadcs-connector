from rest_framework import serializers
from PyADCSConnector.models.authority_instance import AuthorityInstance


class AuthorityInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthorityInstance
        fields = ["uuid", "name", "attributes"]
