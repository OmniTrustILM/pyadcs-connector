from PyADCSConnector.models.authority_instance import AuthorityInstance
from PyADCSConnector.remoting.winrm.scripts import get_templates_script
from PyADCSConnector.remoting.winrm_remoting import create_session_from_authority_instance
from PyADCSConnector.services.attributes import *
from PyADCSConnector.utils.ca_select_method import CaSelectMethod
from PyADCSConnector.utils.dump_parser import DumpParser, TemplateData


def get_raprofile_attributes_list(uuid):
    authority_instance = AuthorityInstance.objects.get(uuid=uuid)

    session = create_session_from_authority_instance(authority_instance)
    session.connect()
    templates = session.run_ps(get_templates_script())
    session.disconnect()

    templates = DumpParser.parse_template_data(templates)

    attribute_list = [get_select_ca_method_attribute(),
                      get_authority_uuid_attribute(uuid),
                      get_ca_select_group_attribute(),
                      get_template_name_attribute(templates)]

    return attribute_list


########################################################################################################################
# Attributes definitions
########################################################################################################################

def get_select_ca_method_attribute():
    properties = get_data_attribute_properties(
        RAPROFILE_SELECT_CA_METHOD_ATTRIBUTE_LABEL,
        is_required=True,
        is_read_only=False,
        is_visible=True,
        is_list=True,
        is_multi_select=False)
    content = [
        {"reference": method.description, "data": method.method} for method in CaSelectMethod
    ]

    return build_attribute(RAPROFILE_SELECT_CA_METHOD_ATTRIBUTE_NAME,
                           RAPROFILE_SELECT_CA_METHOD_ATTRIBUTE_UUID,
                           "data",
                           "string",
                           RAPROFILE_SELECT_CA_METHOD_ATTRIBUTE_DESCRIPTION,
                           properties,
                           content,
                           None,
                           None)


def get_authority_uuid_attribute(authority_uuid):
    properties = get_data_attribute_properties(
        RAPROFILE_AUTHORITY_UUID_ATTRIBUTE_LABEL,
        is_required=True,
        is_read_only=False,
        is_visible=False,
        is_list=False,
        is_multi_select=False)
    content = [
        {"reference": authority_uuid, "data": authority_uuid}
    ]

    return build_attribute(RAPROFILE_AUTHORITY_UUID_ATTRIBUTE_NAME,
                           RAPROFILE_AUTHORITY_UUID_ATTRIBUTE_UUID,
                           "data",
                           "string",
                           RAPROFILE_AUTHORITY_UUID_ATTRIBUTE_DESCRIPTION,
                           properties,
                           content,
                           None,
                           None)


def get_ca_select_group_attribute():
    callback = {
        "callbackContext": "/v1/callbacks/raProfile/caSelect/{ca_select_method}/{authority_instance_uuid}",
        "callbackMethod": "GET",
        "mappings": [
            {
                "from": "raprofile_select_ca_method.data",
                "to": "ca_select_method",
                "targets": [
                    "pathVariable"
                ]
            },
            {
                "from": "raprofile_authority_uuid.data",
                "to": "authority_instance_uuid",
                "targets": [
                    "pathVariable"
                ]
            }
        ]
    }

    return build_attribute(RAPROFILE_CA_SELECT_GROUP_ATTRIBUTE_NAME,
                           RAPROFILE_CA_SELECT_GROUP_ATTRIBUTE_UUID,
                           "group",
                           None,
                           RAPROFILE_CA_SELECT_GROUP_ATTRIBUTE_DESCRIPTION,
                           None,
                           None,
                           callback,
                           None)


def get_template_name_attribute(templates: list[TemplateData]):
    properties = get_data_attribute_properties(
        RAPROFILE_TEMPLATE_NAME_ATTRIBUTE_LABEL,
        is_required=True,
        is_read_only=False,
        is_visible=True,
        is_list=True,
        is_multi_select=False)
    content = [
        {"reference": template.display_name,
         "data": template.__dict__
         } for template in templates
    ]

    return build_attribute(RAPROFILE_TEMPLATE_NAME_ATTRIBUTE_NAME,
                           RAPROFILE_TEMPLATE_NAME_ATTRIBUTE_UUID,
                           "data",
                           "object",
                           RAPROFILE_TEMPLATE_NAME_ATTRIBUTE_DESCRIPTION,
                           properties,
                           content,
                           None,
                           None)


def get_raprofile_config_string_attribute():
    properties = get_data_attribute_properties(
        RAPROFILE_CONFIGSTRING_ATTRIBUTE_LABEL,
        is_required=False,
        is_read_only=False,
        is_visible=True,
        is_list=False,
        is_multi_select=False)

    return build_attribute(RAPROFILE_CONFIGSTRING_ATTRIBUTE_NAME,
                           RAPROFILE_CONFIGSTRING_ATTRIBUTE_UUID,
                           "data",
                           "string",
                           RAPROFILE_CONFIGSTRING_ATTRIBUTE_DESCRIPTION,
                           properties,
                           None,
                           None,
                           None)


def get_raprofile_ca_name_attribute(ca_names):
    properties = get_data_attribute_properties(
        RAPROFILE_CA_NAME_ATTRIBUTE_LABEL,
        is_required=False,
        is_read_only=False,
        is_visible=True,
        is_list=True,
        is_multi_select=False)
    content = ca_names

    return build_attribute(RAPROFILE_CA_NAME_ATTRIBUTE_NAME,
                           RAPROFILE_CA_NAME_ATTRIBUTE_UUID,
                           "data",
                           "object",
                           RAPROFILE_CA_NAME_ATTRIBUTE_DESCRIPTION,
                           properties,
                           content,
                           None,
                           None)


########################################################################################################################
# Constants
########################################################################################################################

# Select CA Method Attribute
RAPROFILE_SELECT_CA_METHOD_ATTRIBUTE_NAME = "raprofile_select_ca_method"
RAPROFILE_SELECT_CA_METHOD_ATTRIBUTE_UUID = "9b5b38a2-9bcc-4178-8d02-7817cc3f3ada"
RAPROFILE_SELECT_CA_METHOD_ATTRIBUTE_LABEL = "Select CA Method"
RAPROFILE_SELECT_CA_METHOD_ATTRIBUTE_DESCRIPTION = "Select how the CA will be chosen, either by ComputerName or search"

# CA Select Group Attribute
RAPROFILE_CA_SELECT_GROUP_ATTRIBUTE_NAME = "raprofile_ca_select_group"
RAPROFILE_CA_SELECT_GROUP_ATTRIBUTE_UUID = "0f26f6a0-94ca-420b-bbd8-4324218d7692"
RAPROFILE_CA_SELECT_GROUP_ATTRIBUTE_LABEL = "CA Select Group Attribute"
RAPROFILE_CA_SELECT_GROUP_ATTRIBUTE_DESCRIPTION = "For identification of select CA method"

# Template Name Attribute
RAPROFILE_TEMPLATE_NAME_ATTRIBUTE_NAME = "raprofile_template_name"
RAPROFILE_TEMPLATE_NAME_ATTRIBUTE_UUID = "da285a61-822a-4508-a565-ce366de66980"
RAPROFILE_TEMPLATE_NAME_ATTRIBUTE_LABEL = "Certificate Template Name"
RAPROFILE_TEMPLATE_NAME_ATTRIBUTE_DESCRIPTION = "Select certificate templates to use"

# Authority UUID Attribute
RAPROFILE_AUTHORITY_UUID_ATTRIBUTE_NAME = "raprofile_authority_uuid"
RAPROFILE_AUTHORITY_UUID_ATTRIBUTE_UUID = "8c4c213a-9bd4-4d49-9812-a539a2deac16"
RAPROFILE_AUTHORITY_UUID_ATTRIBUTE_LABEL = "Authority UUID"
RAPROFILE_AUTHORITY_UUID_ATTRIBUTE_DESCRIPTION = "UUID of selected authority"

# ConfigString Attribute
RAPROFILE_CONFIGSTRING_ATTRIBUTE_NAME = "raprofile_config_string"
RAPROFILE_CONFIGSTRING_ATTRIBUTE_UUID = "2cc47472-f01c-40fd-8291-a2937dacec53"
RAPROFILE_CONFIGSTRING_ATTRIBUTE_LABEL = "CA ConfigString"
RAPROFILE_CONFIGSTRING_ATTRIBUTE_DESCRIPTION = "ConfigString of the CA"

# CA Name Attribute
RAPROFILE_CA_NAME_ATTRIBUTE_NAME = "raprofile_ca_name"
RAPROFILE_CA_NAME_ATTRIBUTE_UUID = "86a3fcb9-d74e-4b2c-b78d-3f71b1181472"
RAPROFILE_CA_NAME_ATTRIBUTE_LABEL = "CA Name"
RAPROFILE_CA_NAME_ATTRIBUTE_DESCRIPTION = "Identification of the certification authority"