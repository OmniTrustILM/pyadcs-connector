from PyADCSConnector.models.authority_instance import AuthorityInstance
from PyADCSConnector.services.attributes import *
from PyADCSConnector.utils.ca_select_method import CaSelectMethod


def get_discovery_attributes_list(kind):
    attribute_list = []

    validate_discovery_kind(kind)

    attribute_list.append(get_discovery_info_attribute())
    attribute_list.append(get_authority_instances_attribute(kind))
    attribute_list.append(get_select_ca_method_attribute())
    attribute_list.append(get_ca_select_group_attribute())
    attribute_list.append(get_template_name_attribute())
    attribute_list.append(get_issued_after_attribute())

    return attribute_list


def validate_discovery_kind(kind):
    if kind != "PyADCS-WinRM":
        raise ValueError("Unrecognized discovery kind: %s" % kind)


########################################################################################################################
# Attributes definitions
########################################################################################################################


def get_discovery_info_attribute():
    properties = get_info_attribute_properties(
        DISCOVERY_INFO_ATTRIBUTE_LABEL,
        is_visible=True)
    markdown_string = """### Configuration of ADCS certificate discovery

Discovery by default runs on all authorities and templates.
It is looking for all certificates that have disposition >= 12 and <= 21.

If you want to limit the discovery to specific authorities or templates, then select the corresponding values."""
    content = [
        {"data": markdown_string},
    ]

    return build_attribute(DISCOVERY_INFO_ATTRIBUTE_NAME,
                           DISCOVERY_INFO_ATTRIBUTE_UUID,
                           "info",
                           "text",
                           DISCOVERY_INFO_ATTRIBUTE_DESCRIPTION,
                           properties,
                           content,
                           None,
                           None)


def get_authority_instances_attribute(kind):
    authority_instances = AuthorityInstance.objects.filter(kind=kind)
    properties = get_data_attribute_properties(
        DISCOVERY_AUTHORITY_INSTANCE_ATTRIBUTE_LABEL,
        is_required=True,
        is_read_only=False,
        is_visible=True,
        is_list=True,
        is_multi_select=False)
    content = [
        {"reference": instance.name,
         "data": {
             "uuid": instance.uuid,
             "name": instance.name
         }
         } for instance in authority_instances
    ]

    return build_attribute(DISCOVERY_AUTHORITY_INSTANCE_ATTRIBUTE_NAME,
                           DISCOVERY_AUTHORITY_INSTANCE_ATTRIBUTE_UUID,
                           "data",
                           "object",
                           DISCOVERY_AUTHORITY_INSTANCE_ATTRIBUTE_DESCRIPTION,
                           properties,
                           content,
                           None,
                           None)


def get_select_ca_method_attribute():
    properties = get_data_attribute_properties(
        DISCOVERY_SELECT_CA_METHOD_ATTRIBUTE_LABEL,
        is_required=True,
        is_read_only=False,
        is_visible=True,
        is_list=True,
        is_multi_select=False)
    content = [
        {"reference": method.description, "data": method.method} for method in CaSelectMethod
    ]

    return build_attribute(DISCOVERY_SELECT_CA_METHOD_ATTRIBUTE_NAME,
                           DISCOVERY_SELECT_CA_METHOD_ATTRIBUTE_UUID,
                           "data",
                           "string",
                           DISCOVERY_SELECT_CA_METHOD_ATTRIBUTE_DESCRIPTION,
                           properties,
                           content,
                           None,
                           None)


def get_ca_select_group_attribute():
    callback = {
        "callbackContext": "/v1/callbacks/discovery/caSelect/{ca_select_method}/{authority_instance_uuid}",
        "callbackMethod": "GET",
        "mappings": [
            {
                "from": "discovery_select_ca_method.data",
                "to": "ca_select_method",
                "targets": [
                    "pathVariable"
                ]
            },
            {
                "from": "discovery_authority_instance.data.uuid",
                "to": "authority_instance_uuid",
                "targets": [
                    "pathVariable"
                ]
            }
        ]
    }

    return build_attribute(DISCOVERY_CA_SELECT_GROUP_ATTRIBUTE_NAME,
                           DISCOVERY_CA_SELECT_GROUP_ATTRIBUTE_UUID,
                           "group",
                           None,
                           DISCOVERY_CA_SELECT_GROUP_ATTRIBUTE_DESCRIPTION,
                           None,
                           None,
                           callback,
                           None)


def get_discovery_ca_name_attribute(ca_names):
    properties = get_data_attribute_properties(
        DISCOVERY_CA_NAME_ATTRIBUTE_LABEL,
        is_required=False,
        is_read_only=False,
        is_visible=True,
        is_list=True,
        is_multi_select=True)
    content = ca_names

    return build_attribute(DISCOVERY_CA_NAME_ATTRIBUTE_NAME,
                           DISCOVERY_CA_NAME_ATTRIBUTE_UUID,
                           "data",
                           "object",
                           DISCOVERY_CA_NAME_ATTRIBUTE_DESCRIPTION,
                           properties,
                           content,
                           None,
                           None)


def get_template_name_attribute():
    properties = get_data_attribute_properties(
        DISCOVERY_TEMPLATE_NAME_ATTRIBUTE_LABEL,
        is_required=False,
        is_read_only=False,
        is_visible=True,
        is_list=True,
        is_multi_select=True)
    callback = {
        "callbackContext": "/v1/callbacks/discovery/listTemplate/{authority_instance_uuid}",
        "callbackMethod": "GET",
        "mappings": [
            {
                "from": "discovery_authority_instance.data.uuid",
                "to": "authority_instance_uuid",
                "targets": [
                    "pathVariable"
                ]
            }
        ]
    }

    return build_attribute(DISCOVERY_TEMPLATE_NAME_ATTRIBUTE_NAME,
                           DISCOVERY_TEMPLATE_NAME_ATTRIBUTE_UUID,
                           "data",
                           "object",
                           DISCOVERY_TEMPLATE_NAME_ATTRIBUTE_DESCRIPTION,
                           properties,
                           None,
                           callback,
                           None)


def get_issued_after_attribute():
    properties = get_data_attribute_properties(
        DISCOVERY_ISSUED_AFTER_ATTRIBUTE_LABEL,
        is_required=False,
        is_read_only=False,
        is_visible=True,
        is_list=False,
        is_multi_select=False)

    return build_attribute(DISCOVERY_ISSUED_AFTER_ATTRIBUTE_NAME,
                           DISCOVERY_ISSUED_AFTER_ATTRIBUTE_UUID,
                           "data",
                           "datetime",
                           DISCOVERY_ISSUED_AFTER_ATTRIBUTE_DESCRIPTION,
                           properties,
                           None,
                           None,
                           None)


def get_issued_days_before_attribute():
    properties = get_data_attribute_properties(
        DISCOVERY_ISSUED_DAYS_BEFORE_ATTRIBUTE_LABEL,
        is_required=True,
        is_read_only=False,
        is_visible=True,
        is_list=False,
        is_multi_select=False)
    content = [
        {"reference": "5", "data": "5"},
    ]

    return build_attribute(DISCOVERY_ISSUED_DAYS_BEFORE_ATTRIBUTE_NAME,
                           DISCOVERY_ISSUED_DAYS_BEFORE_ATTRIBUTE_UUID,
                           "data",
                           "integer",
                           DISCOVERY_ISSUED_DAYS_BEFORE_ATTRIBUTE_DESCRIPTION,
                           properties,
                           content,
                           None,
                           None)


def get_discovery_config_string_attribute():
    properties = get_data_attribute_properties(
        DISCOVERY_CONFIGSTRING_ATTRIBUTE_LABEL,
        is_required=False,
        is_read_only=False,
        is_visible=True,
        is_list=False,
        is_multi_select=False)

    return build_attribute(DISCOVERY_CONFIGSTRING_ATTRIBUTE_NAME,
                           DISCOVERY_CONFIGSTRING_ATTRIBUTE_UUID,
                           "data",
                           "string",
                           DISCOVERY_CONFIGSTRING_ATTRIBUTE_DESCRIPTION,
                           properties,
                           None,
                           None,
                           None)


########################################################################################################################
# Constants
########################################################################################################################

# Discovery Info Attribute
DISCOVERY_INFO_ATTRIBUTE_NAME = "discovery_info"
DISCOVERY_INFO_ATTRIBUTE_UUID = "6daef143-0c76-46db-a162-bc38cf70951f"
DISCOVERY_INFO_ATTRIBUTE_LABEL = "Discovery Information"
DISCOVERY_INFO_ATTRIBUTE_DESCRIPTION = "How to use Discovery Attributes"

# Authority Instance Attribute
DISCOVERY_AUTHORITY_INSTANCE_ATTRIBUTE_NAME = "discovery_authority_instance"
DISCOVERY_AUTHORITY_INSTANCE_ATTRIBUTE_UUID = "b0026fc5-cbee-447b-9e6c-1b1a20f183e4"
DISCOVERY_AUTHORITY_INSTANCE_ATTRIBUTE_LABEL = "Authority Instance"
DISCOVERY_AUTHORITY_INSTANCE_ATTRIBUTE_DESCRIPTION = "Choose the authority instance to use"

# CA Name Attribute
DISCOVERY_CA_NAME_ATTRIBUTE_NAME = "discovery_ca_name"
DISCOVERY_CA_NAME_ATTRIBUTE_UUID = "c725fa53-a3f2-4d24-909d-c40a52a93c01"
DISCOVERY_CA_NAME_ATTRIBUTE_LABEL = "CA Name"
DISCOVERY_CA_NAME_ATTRIBUTE_DESCRIPTION = "Identification of the certification authority"

# Issued After Attribute
DISCOVERY_ISSUED_AFTER_ATTRIBUTE_NAME = "discovery_issued_after"
DISCOVERY_ISSUED_AFTER_ATTRIBUTE_UUID = "f1b49091-de61-4806-95de-02ed94f8f954"
DISCOVERY_ISSUED_AFTER_ATTRIBUTE_LABEL = "Issued After"
DISCOVERY_ISSUED_AFTER_ATTRIBUTE_DESCRIPTION = "Select certificates issued after this date (notBefore)"

# Issued Days Before Attribute
DISCOVERY_ISSUED_DAYS_BEFORE_ATTRIBUTE_NAME = "discovery_issued_days_before"
DISCOVERY_ISSUED_DAYS_BEFORE_ATTRIBUTE_UUID = "bccd95b2-c580-4311-baff-7099aeb57b48"
DISCOVERY_ISSUED_DAYS_BEFORE_ATTRIBUTE_LABEL = "Number of days before discovery"
DISCOVERY_ISSUED_DAYS_BEFORE_ATTRIBUTE_DESCRIPTION = (
    "Maximum number of days before the certificate was issued, from running "
    "the discovery")

# Select CA Method Attribute
DISCOVERY_SELECT_CA_METHOD_ATTRIBUTE_NAME = "discovery_select_ca_method"
DISCOVERY_SELECT_CA_METHOD_ATTRIBUTE_UUID = "ad5e1ca6-a018-43b3-8d36-17a1deb61cb8"
DISCOVERY_SELECT_CA_METHOD_ATTRIBUTE_LABEL = "Select CA Method"
DISCOVERY_SELECT_CA_METHOD_ATTRIBUTE_DESCRIPTION = "Select how the CA will be chosen, either by ComputerName or search"

# CA Select Group Attribute
DISCOVERY_CA_SELECT_GROUP_ATTRIBUTE_NAME = "discovery_ca_select_group"
DISCOVERY_CA_SELECT_GROUP_ATTRIBUTE_UUID = "b5cd936c-5375-48d9-bd34-4e859195f1af"
DISCOVERY_CA_SELECT_GROUP_ATTRIBUTE_LABEL = "CA Select Group Attribute"
DISCOVERY_CA_SELECT_GROUP_ATTRIBUTE_DESCRIPTION = "For identification of select CA method"

# Template Name Attribute
DISCOVERY_TEMPLATE_NAME_ATTRIBUTE_NAME = "discovery_template_name"
DISCOVERY_TEMPLATE_NAME_ATTRIBUTE_UUID = "53286673-be2a-453f-9998-cab67dbb4620"
DISCOVERY_TEMPLATE_NAME_ATTRIBUTE_LABEL = "Certificate Template Name"
DISCOVERY_TEMPLATE_NAME_ATTRIBUTE_DESCRIPTION = "Select certificate templates to use"

# ConfigString Attribute
DISCOVERY_CONFIGSTRING_ATTRIBUTE_NAME = "discovery_config_string"
DISCOVERY_CONFIGSTRING_ATTRIBUTE_UUID = "ab4f8573-bf55-4863-b2ce-44597b111cf9"
DISCOVERY_CONFIGSTRING_ATTRIBUTE_LABEL = "CA ConfigString"
DISCOVERY_CONFIGSTRING_ATTRIBUTE_DESCRIPTION = "ConfigString of the CA"
