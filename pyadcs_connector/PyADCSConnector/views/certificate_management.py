import json
import logging

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from PyADCSConnector.services.certificate_management import issue, renew, revoke, identify

logger = logging.getLogger(__name__)


@require_http_methods(["POST"])
def issue_certificate(request, uuid, *args, **kwargs):
    request_dto = json.loads(request.body)
    certificate_dto = issue(request_dto, uuid)
    return JsonResponse(certificate_dto.to_json(), safe=False, content_type="application/json")


@require_http_methods(["POST"])
def renew_certificate(request, uuid, *args, **kwargs):
    request_dto = json.loads(request.body)
    certificate_dto = renew(request_dto, uuid)
    return JsonResponse(certificate_dto.to_json(), safe=False, content_type="application/json")


@require_http_methods(["POST"])
def revoke_certificate(request, uuid, *args, **kwargs):
    request_dto = json.loads(request.body)
    revoke(request_dto, uuid)
    return JsonResponse({}, safe=False, content_type="application/json")


@require_http_methods(["POST"])
def identify_certificate(request, uuid, *args, **kwargs):
    request_dto = json.loads(request.body)
    response = identify(request_dto, uuid)
    return JsonResponse(response, safe=False, content_type="application/json")
