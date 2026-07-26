from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

import logging

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def get_endpoints(request, *args, **kwargs):
    logger.debug("Getting all available endpoints")

    endpoint_response = dict()
    endpoint_response["functionGroupCode"] = "authorityProvider"
    endpoint_response["kinds"] = ["PyADCS-WinRM"]
    endpoint_response["endPoints"] = [
        {
            "name": "removeAuthorityInstance",
            "context": "/v1/authorityProvider/authorities/{uuid}",
            "method": "DELETE",
            "required": False
        },
        {
            "name": "validateIssueCertificateAttributes",
            "context": "/v2/authorityProvider/authorities/{uuid}/certificates/issue/attributes/validate",
            "method": "POST",
            "required": False
        },
        {
            "name": "validateRevokeCertificateAttributes",
            "context": "/v2/authorityProvider/authorities/{uuid}/certificates/revoke/attributes/validate",
            "method": "POST",
            "required": False
        },
        {
            "name": "validateRAProfileAttributes",
            "context": "/v1/authorityProvider/authorities/{uuid}/raProfile/attributes/validate",
            "method": "POST",
            "required": False
        },
        {
            "name": "revokeCertificate",
            "context": "/v2/authorityProvider/authorities/{uuid}/certificates/revoke",
            "method": "POST",
            "required": False
        },
        {
            "name": "validateAttributes",
            "context": "/v1/authorityProvider/{kind}/attributes/validate",
            "method": "POST",
            "required": False
        },
        {
            "name": "listRevokeCertificateAttributes",
            "context": "/v2/authorityProvider/authorities/{uuid}/certificates/revoke/attributes",
            "method": "GET",
            "required": False
        },
        {
            "name": "checkHealth",
            "context": "/v1/health",
            "method": "GET",
            "required": False
        },
        {
            "name": "listAttributeDefinitions",
            "context": "/v1/authorityProvider/{kind}/attributes",
            "method": "GET",
            "required": False
        },
        {
            "name": "updateAuthorityInstance",
            "context": "/v1/authorityProvider/authorities/{uuid}",
            "method": "POST",
            "required": False
        },
        {
            "name": "getConnection",
            "context": "/v1/authorityProvider/authorities/{uuid}/connect",
            "method": "GET",
            "required": False
        },
        {
            "name": "renewCertificate",
            "context": "/v2/authorityProvider/authorities/{uuid}/certificates/renew",
            "method": "POST",
            "required": False
        },
        {
            "name": "listRAProfileAttributes",
            "context": "/v1/authorityProvider/authorities/{uuid}/raProfile/attributes",
            "method": "GET",
            "required": False
        },
        {
            "name": "getAuthorityInstance",
            "context": "/v1/authorityProvider/authorities/{uuid}",
            "method": "GET",
            "required": False
        },
        {
            "name": "listAuthorityInstances",
            "context": "/v1/authorityProvider/authorities",
            "method": "GET",
            "required": False
        },
        {
            "name": "issueCertificate",
            "context": "/v2/authorityProvider/authorities/{uuid}/certificates/issue",
            "method": "POST",
            "required": False
        },
        {
            "name": "listSupportedFunctions",
            "context": "/v1",
            "method": "GET",
            "required": False
        },
        {
            "name": "listIssueCertificateAttributes",
            "context": "/v2/authorityProvider/authorities/{uuid}/certificates/issue/attributes",
            "method": "GET",
            "required": False
        },
        {
            "name": "createAuthorityInstance",
            "context": "/v1/authorityProvider/authorities",
            "method": "POST",
            "required": False
        }
    ]

    discovery_endpoint_response = dict()
    discovery_endpoint_response["functionGroupCode"] = "discoveryProvider"
    discovery_endpoint_response["kinds"] = ["PyADCS-WinRM"]
    discovery_endpoint_response["endPoints"] = [
        {
            "name": "listAttributeDefinitions",
            "context": "/v1/discoveryProvider/{kind}/attributes",
            "method": "GET",
            "required": False
        },
        {
            "name": "validateAttributes",
            "context": "/v1/discoveryProvider/{kind}/attributes/validate",
            "method": "POST",
            "required": False
        },
        {
            "name": "getDiscovery",
            "context": "/v1/discoveryProvider/discover/{uuid}",
            "method": "GET",
            "required": False
        },
        {
            "name": "discoverCertificate",
            "context": "/v1/discoveryProvider/discover",
            "method": "POST",
            "required": False
        },
        {
            "name": "deleteDiscovery",
            "context": "/v1/discoveryProvider/discover/{uuid}",
            "method": "DELETE",
            "required": False
        }
    ]

    function_groups = [endpoint_response, discovery_endpoint_response]

    return JsonResponse(function_groups, safe=False)
