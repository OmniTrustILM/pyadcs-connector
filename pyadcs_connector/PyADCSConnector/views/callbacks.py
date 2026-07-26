from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from PyADCSConnector.services.attributes.authority_attributes import get_winrm_transport_configuration_attributes_list
from PyADCSConnector.services.attributes.discovery_attributes import get_discovery_config_string_attribute, \
    get_discovery_ca_name_attribute
from PyADCSConnector.services.attributes.raprofile_attributes import get_raprofile_config_string_attribute, \
    get_raprofile_ca_name_attribute
from PyADCSConnector.services.authority_instance import get_cas, get_templates
from PyADCSConnector.utils.ca_select_method import CaSelectMethod


@require_http_methods(["GET"])
def get_winrm_transport_configuration(request, kind, wirm_transport, *args, **kwargs):
    attributes = get_winrm_transport_configuration_attributes_list(kind, wirm_transport)
    return JsonResponse(attributes, safe=False,
                        content_type="application/json")


@require_http_methods(["GET"])
def get_discovery_ca_select_configuration(request, ca_select_method: str, authority_instance_uuid: str, *args, **kwargs):
    attributes = []
    if ca_select_method == CaSelectMethod.CONFIGSTRING.method:
        attributes.append(get_discovery_config_string_attribute())
    elif ca_select_method == CaSelectMethod.SEARCH.method:
        attributes.append(get_discovery_ca_name_attribute(get_cas(authority_instance_uuid)))
    else:
        raise Exception("Unknown CA Select Method: " + ca_select_method)

    return JsonResponse(attributes, safe=False,content_type="application/json")


@require_http_methods(["GET"])
def get_raprofile_ca_select_configuration(request, ca_select_method: str, authority_instance_uuid: str, *args, **kwargs):
    attributes = []
    if ca_select_method == CaSelectMethod.CONFIGSTRING.method:
        attributes.append(get_raprofile_config_string_attribute())
    elif ca_select_method == CaSelectMethod.SEARCH.method:
        attributes.append(get_raprofile_ca_name_attribute(get_cas(authority_instance_uuid)))
    else:
        raise Exception("Unknown CA Select Method: " + ca_select_method)

    return JsonResponse(attributes, safe=False,content_type="application/json")


@require_http_methods(["GET"])
def get_ca_names(request, authority_instance_uuid, *args, **kwargs):
    cas = get_cas(authority_instance_uuid)
    return JsonResponse(cas, safe=False, content_type="application/json")


@require_http_methods(["GET"])
def get_template_names(request, authority_instance_uuid, *args, **kwargs):
    templates = get_templates(authority_instance_uuid)
    return JsonResponse(templates, safe=False, content_type="application/json")
