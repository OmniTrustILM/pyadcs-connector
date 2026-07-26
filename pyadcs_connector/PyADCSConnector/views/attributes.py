"""
Script to perform attribute related operations like getting attributes,
validate attributes
"""

from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods

from PyADCSConnector.services.attributes.authority_attributes import get_authority_attributes_list
from PyADCSConnector.services.attributes.discovery_attributes import get_discovery_attributes_list
from PyADCSConnector.services.attributes.raprofile_attributes import get_raprofile_attributes_list


@require_http_methods(["GET"])
def get_authority_attributes(request, kind, *args, **kwargs):
    try:
        return JsonResponse(get_authority_attributes_list(kind), safe=False, content_type="application/json")
    except ValueError as e:
        return JsonResponse({"message": str(e)}, status=400)


@require_http_methods(["GET"])
def get_discovery_attributes(request, kind, *args, **kwargs):
    try:
        return JsonResponse(get_discovery_attributes_list(kind), safe=False, content_type="application/json")
    except ValueError as e:
        return JsonResponse({"message": str(e)}, status=400)


@require_http_methods(["GET"])
def get_raprofile_attributes(request, uuid, *args, **kwargs):
    try:
        return JsonResponse(get_raprofile_attributes_list(uuid), safe=False, content_type="application/json")
    except ValueError as e:
        return JsonResponse({"message": str(e)}, status=400)


@require_http_methods(["GET"])
def get_issue_attributes(request, uuid, *args, **kwargs):
    try:
        attribute_list = []
        return JsonResponse(attribute_list, safe=False, content_type="application/json")
    except ValueError as e:
        return JsonResponse({"message": str(e)}, status=400)


@require_http_methods(["GET"])
def get_revoke_attributes(request, uuid, *args, **kwargs):
    try:
        attribute_list = []
        return JsonResponse(attribute_list, safe=False, content_type="application/json")
    except ValueError as e:
        return JsonResponse({"message": str(e)}, status=400)


@require_http_methods(["POST"])
def validate_authority_attributes(request, kind, *args, **kwargs):
    # Attribute values are accepted as provided; no additional validation is applied here.
    return HttpResponse(content_type="application/json", status=200)


@require_http_methods(["POST"])
def validate_discovery_attributes(request, kind, *args, **kwargs):
    # Attribute values are accepted as provided; no additional validation is applied here.
    return HttpResponse(content_type="application/json", status=200)


@require_http_methods(["POST"])
def validate_raprofile_attributes(request, uuid, *args, **kwargs):
    # Attribute values are accepted as provided; no additional validation is applied here.
    return HttpResponse(content_type="application/json", status=200)


@require_http_methods(["POST"])
def validate_issue_attributes(request, uuid, *args, **kwargs):
    # Attribute values are accepted as provided; no additional validation is applied here.
    return HttpResponse(content_type="application/json", status=200)


@require_http_methods(["POST"])
def validate_revoke_attributes(request, uuid, *args, **kwargs):
    # Attribute values are accepted as provided; no additional validation is applied here.
    return HttpResponse(content_type="application/json", status=200)
