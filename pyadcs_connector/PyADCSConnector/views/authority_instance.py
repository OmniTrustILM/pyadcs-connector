import json

from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods

from PyADCSConnector.models.authority_instance import AuthorityInstance
from PyADCSConnector.serializers.authority_instance_serializer import AuthorityInstanceSerializer
from PyADCSConnector.services.authority_instance import create_authority_instance, update_authority_instance


@require_http_methods(["GET", "POST"])
@transaction.atomic
def authority_operations(request, *args, **kwargs):
    if request.method == "GET":
        authorities = AuthorityInstance.objects
        serializer = AuthorityInstanceSerializer(authorities, many=True)
        return JsonResponse(serializer.data, safe=False)
    else:
        request_dto = json.loads(request.body)
        authority = create_authority_instance(request_dto)
        serializer = AuthorityInstanceSerializer(authority)
        return JsonResponse(serializer.data, safe=False)


@require_http_methods(["GET", "POST", "DELETE"])
@transaction.atomic
def authority_instance_operations(request, uuid, *args, **kwargs):
    if request.method == "GET":
        try:
            authority = AuthorityInstance.objects.get(uuid=uuid)
            serializer = AuthorityInstanceSerializer(authority)
            return JsonResponse(serializer.data, safe=False)
        except AuthorityInstance.DoesNotExist:
            return JsonResponse({"message": "Requested Authority with UUID %s not found" % uuid}, status=404)
    elif request.method == "DELETE":
        try:
            AuthorityInstance.objects.get(uuid=uuid).delete()
            return HttpResponse(status=204)
        except AuthorityInstance.DoesNotExist:
            return JsonResponse({"message": "Requested Authority with UUID %s not found" % uuid}, status=404)
    elif request.method == "POST":
        try:
            request_dto = json.loads(request.body)
            authority = AuthorityInstance.objects.get(uuid=uuid)
            authority = update_authority_instance(request_dto, authority)
            serializer = AuthorityInstanceSerializer(authority)
            return JsonResponse(serializer.data, safe=False)
        except AuthorityInstance.DoesNotExist:
            return JsonResponse({"message": "Requested Authority with UUID %s not found" % uuid}, status=404)
    else:
        raise ValueError("Update authority is not supported")
