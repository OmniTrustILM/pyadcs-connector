from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def get_health(request, *args, **kwargs):
    return JsonResponse({"status": "ok", "description": "string"})
