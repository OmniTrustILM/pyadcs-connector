import json
import logging
from threading import Thread

from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from PyADCSConnector.models.discovery_history import DiscoveryHistory
from PyADCSConnector.objects.discovery_history_request_dto import DiscoveryHistoryRequestDto
from PyADCSConnector.services.discovery_history import create_discovery_history, get_discovery_history_data, \
    run_discovery

logger = logging.getLogger(__name__)


@require_http_methods(["POST"])
def start_discovery(request, *args, **kwargs):
    request_dto = json.loads(request.body)

    discovery_history = create_discovery_history(request_dto)

    # create a new thread and run discovery
    # Discovery runs asynchronously in a background thread.
    Thread(target=run_discovery, args=(request_dto, discovery_history.uuid), daemon=True).start()

    discovery_history_request = DiscoveryHistoryRequestDto()
    discovery_history_request.name = request_dto["name"]
    discovery_history_request.pageNumber = 0
    discovery_history_request.itemsPerPage = 10

    discovery_history_response = get_discovery_history_data(discovery_history_request, discovery_history)

    return JsonResponse(discovery_history_response.to_json(), safe=False, content_type="application/json")


@require_http_methods(["POST", "DELETE"])
@transaction.atomic
def discovery_operations(request, uuid, *args, **kwargs):
    if request.method == "DELETE":
        try:
            # select_for_update locks the row so a concurrent discovery
            # persistence (which reads the same row under FOR UPDATE before
            # adding join rows) cannot slip in a new DiscoveryCertificate
            # after we've collected this discovery's rows for cascade delete.
            discovery_history = DiscoveryHistory.objects.select_for_update().get(uuid=uuid)
            # ORM cascade (DiscoveryCertificate.discovery FK, on_delete=CASCADE)
            # clears join rows; shared Certificate rows are left for the cleanup sweep.
            discovery_history.delete()
            # return 204 no content
            return JsonResponse({}, status=204)
        except DiscoveryHistory.DoesNotExist:
            return JsonResponse({"message": "Requested Discovery History with UUID %s not found" % uuid}, status=404)
    else:
        try:
            discovery_history = DiscoveryHistory.objects.get(uuid=uuid)
            request_dto = json.loads(request.body)
            discovery_history_request = DiscoveryHistoryRequestDto.from_json(request_dto)
            discovery_history_data_response = get_discovery_history_data(discovery_history_request, discovery_history)
            return JsonResponse(discovery_history_data_response.to_json(), safe=False, content_type="application/json")
        except DiscoveryHistory.DoesNotExist:
            return JsonResponse({"message": "Requested Discovery History with UUID %s not found" % uuid}, status=404)
