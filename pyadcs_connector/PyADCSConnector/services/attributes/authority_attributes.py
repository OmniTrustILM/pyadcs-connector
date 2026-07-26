from PyADCSConnector.services.attributes import *


def get_authority_attributes_list(kind):
    attribute_list = []

    validate_authority_kind(kind)

    attribute_list.append(get_adcs_info_attribute())
    attribute_list.append(get_credential_type_attribute())
    attribute_list.append(get_credential_attribute())
    attribute_list.append(get_server_attribute())
    attribute_list.append(get_use_https_attribute())
    attribute_list.append(get_winrm_port_attribute())
    attribute_list.append(get_winrm_transport_attribute())

    return attribute_list


def validate_authority_kind(kind):
    if kind != "PyADCS-WinRM":
        raise ValueError("Unrecognized authority kind: %s" % kind)


def get_all_authority_attributes_list(kind, winrm_transport):
    validate_authority_kind(kind)

    if winrm_transport != "credssp":
        raise ValueError("Unrecognized protocol: %s" % winrm_transport)

    attribute_list = [get_adcs_info_attribute(), get_credential_type_attribute(), get_credential_attribute(),
                      get_server_attribute(), get_use_https_attribute(), get_winrm_port_attribute(),
                      get_winrm_transport_attribute(), get_winrm_transport_config_attribute(kind)]
    return attribute_list

########################################################################################################################
# Attributes definitions
########################################################################################################################


def get_adcs_info_attribute():
    properties = get_info_attribute_properties(
        AUTHORITY_ADCS_INFO_ATTRIBUTE_LABEL,
        is_visible=True)
    markdown_string = """### ADCS authority instance configuration using WinRM protocol

Choose the credential and server configuration to proceed."""
    content = [
        {"data": markdown_string},
    ]

    return build_attribute(AUTHORITY_ADCS_INFO_ATTRIBUTE_NAME,
                           AUTHORITY_ADCS_INFO_ATTRIBUTE_UUID,
                           "info",
                           "text",
                           AUTHORITY_ADCS_INFO_ATTRIBUTE_DESCRIPTION,
                           properties,
                           content,
                           None,
                           None)


def get_credential_type_attribute():
    properties = get_data_attribute_properties(
        AUTHORITY_CREDENTIAL_TYPE_ATTRIBUTE_LABEL,
        is_required=True,
        is_read_only=False,
        is_visible=True,
        is_list=True,
        is_multi_select=False)
    content = [
        {"reference": "Basic", "data": "Basic"},
    ]

    return build_attribute(AUTHORITY_CREDENTIAL_TYPE_ATTRIBUTE_NAME,
                           AUTHORITY_CREDENTIAL_TYPE_ATTRIBUTE_UUID,
                           "data",
                           "string",
                           AUTHORITY_CREDENTIAL_TYPE_ATTRIBUTE_DESCRIPTION,
                           properties,
                           content,
                           None,
                           None)


def get_credential_attribute():
    properties = get_data_attribute_properties(
        AUTHORITY_CREDENTIAL_ATTRIBUTE_LABEL,
        is_required=True,
        is_read_only=False,
        is_visible=True,
        is_list=True,
        is_multi_select=False)
    callback = {
        "callbackContext": "core/getCredentials",
        "callbackMethod": "GET",
        "mappings": [
            {
                "from": "authority_credential_type",
                "to": "credentialKind",
                "targets": [
                    "pathVariable"
                ]
            }
        ]
    }

    return build_attribute(AUTHORITY_CREDENTIAL_ATTRIBUTE_NAME,
                           AUTHORITY_CREDENTIAL_ATTRIBUTE_UUID,
                           "data",
                           "credential",
                           AUTHORITY_CREDENTIAL_ATTRIBUTE_DESCRIPTION,
                           properties,
                           None,
                           callback,
                           None)


def get_winrm_transport_attribute():
    properties = get_data_attribute_properties(
        AUTHORITY_WINRM_TRANSPORT_ATTRIBUTE_LABEL,
        is_required=True,
        is_read_only=False,
        is_visible=True,
        is_list=True,
        is_multi_select=False)
    content = [
        {"reference": "CredSSP", "data": "credssp"},
    ]

    return build_attribute(AUTHORITY_WINRM_TRANSPORT_ATTRIBUTE_NAME,
                           AUTHORITY_WINRM_TRANSPORT_ATTRIBUTE_UUID,
                           "data",
                           "string",
                           AUTHORITY_WINRM_TRANSPORT_ATTRIBUTE_DESCRIPTION,
                           properties,
                           content,
                           None,
                           None)


def get_winrm_transport_config_attribute(kind):
    callback = {
        "callbackContext": "/v1/callbacks/authority/winrmConfig/{kind}/{winrm_transport}",
        "callbackMethod": "GET",
        "mappings": [
            {
                "from": "authority_winrm_transport.data",
                "to": "winrm_transport",
                "targets": [
                    "pathVariable"
                ]
            },
            {
                "to": "kind",
                "targets": [
                    "pathVariable"
                ],
                "value": kind
            }
        ]
    }

    return build_attribute(AUTHORITY_WINRM_TRANSPORT_CONFIG_ATTRIBUTE_NAME,
                           AUTHORITY_WINRM_TRANSPORT_CONFIG_ATTRIBUTE_UUID,
                           "group",
                           None,
                           AUTHORITY_WINRM_TRANSPORT_CONFIG_ATTRIBUTE_DESCRIPTION,
                           None,
                           None,
                           callback,
                           None)


def get_server_attribute():
    properties = get_data_attribute_properties(
        AUTHORITY_SERVER_ADDRESS_ATTRIBUTE_LABEL,
        is_required=True,
        is_read_only=False,
        is_visible=True,
        is_list=False,
        is_multi_select=False)
    server_regexp_constraint = dict()
    server_regexp_constraint["type"] = "regExp"
    server_regexp_constraint["description"] = "Address of ADCS Server"
    server_regexp_constraint["errorMessage"] = "Enter Valid Address"
    server_regexp_constraint["data"] = ("^((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}([0-9]|"
                                        "[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])|(([a-zA-Z0-9]|[a-zA-Z0-9]"
                                        "[a-zA-Z0-9\\-]*[a-zA-Z0-9])\\.)*([A-Za-z0-9]|[A-Za-z0-9]"
                                        "[A-Za-z0-9\\-]*"
                                        "[A-Za-z0-9]))$")
    constraints = [server_regexp_constraint]

    return build_attribute(AUTHORITY_SERVER_ADDRESS_ATTRIBUTE_NAME,
                           AUTHORITY_SERVER_ADDRESS_ATTRIBUTE_UUID,
                           "data",
                           "string",
                           AUTHORITY_SERVER_ADDRESS_ATTRIBUTE_DESCRIPTION,
                           properties,
                           None,
                           None,
                           constraints)


def get_use_https_attribute():
    properties = get_data_attribute_properties(
        AUTHORITY_USE_HTTPS_ATTRIBUTE_LABEL,
        is_required=False,
        is_read_only=False,
        is_visible=True,
        is_list=False,
        is_multi_select=False)
    content = [
        {"reference": "True", "data": "true"},
    ]
    return build_attribute(AUTHORITY_USE_HTTPS_ATTRIBUTE_NAME,
                           AUTHORITY_USE_HTTPS_ATTRIBUTE_UUID,
                           "data",
                           "boolean",
                           AUTHORITY_USE_HTTPS_ATTRIBUTE_DESCRIPTION,
                           properties,
                           content,
                           None,
                           None)


def get_winrm_port_attribute():
    properties = get_data_attribute_properties(
        AUTHORITY_WINRM_PORT_ATTRIBUTE_LABEL,
        is_required=True,
        is_read_only=False,
        is_visible=True,
        is_list=False,
        is_multi_select=False)
    content = [
        {"reference": "5985", "data": "5985"},
    ]
    return build_attribute(AUTHORITY_WINRM_PORT_ATTRIBUTE_NAME,
                           AUTHORITY_WINRM_PORT_ATTRIBUTE_UUID,
                           "data",
                           "integer",
                           AUTHORITY_WINRM_PORT_ATTRIBUTE_DESCRIPTION,
                           properties,
                           content,
                           None,
                           None)


def get_winrm_transport_configuration_attributes_list(kind, winrm_transport):
    validate_authority_kind(kind)

    if winrm_transport != "credssp":
        raise ValueError("Unrecognized protocol: %s" % winrm_transport)

    # attribute_list = []

    match winrm_transport:
        case "credssp":
            return


########################################################################################################################
# Constants
########################################################################################################################

# ADCS Info Attribute
AUTHORITY_ADCS_INFO_ATTRIBUTE_NAME = "authority_adcs_info"
AUTHORITY_ADCS_INFO_ATTRIBUTE_UUID = "870b612e-fd82-446f-bb5e-e9078ca117cc"
AUTHORITY_ADCS_INFO_ATTRIBUTE_LABEL = "ADCS Information"
AUTHORITY_ADCS_INFO_ATTRIBUTE_DESCRIPTION = "How to use ADCS Attributes"

# WinRM Transport Attribute
AUTHORITY_WINRM_TRANSPORT_ATTRIBUTE_NAME = "authority_winrm_transport"
AUTHORITY_WINRM_TRANSPORT_ATTRIBUTE_UUID = "06cf66eb-5c1e-4edf-8308-617565a5d6b4"
AUTHORITY_WINRM_TRANSPORT_ATTRIBUTE_LABEL = "WinRM Transport"
AUTHORITY_WINRM_TRANSPORT_ATTRIBUTE_DESCRIPTION = "Choose the transport type to use for communication with ADCS"

# WinRM Transport Config Attribute
AUTHORITY_WINRM_TRANSPORT_CONFIG_ATTRIBUTE_NAME = "authority_winrm_transport_config"
AUTHORITY_WINRM_TRANSPORT_CONFIG_ATTRIBUTE_UUID = "dd12711e-2daa-4b82-b167-0c2ee5f71df6"
AUTHORITY_WINRM_TRANSPORT_CONFIG_ATTRIBUTE_LABEL = "WinRM Transport Configuration"
AUTHORITY_WINRM_TRANSPORT_CONFIG_ATTRIBUTE_DESCRIPTION = "Configure transport specific attributes"

# Server Attribute
AUTHORITY_SERVER_ADDRESS_ATTRIBUTE_NAME = "authority_server_address"
AUTHORITY_SERVER_ADDRESS_ATTRIBUTE_UUID = "f2ee713a-c7cf-4b27-ae91-a84606b4877a"
AUTHORITY_SERVER_ADDRESS_ATTRIBUTE_LABEL = "ADCS server address"
AUTHORITY_SERVER_ADDRESS_ATTRIBUTE_DESCRIPTION = "Server hostname where ADCS is running"

# Use HTTPS Attribute
AUTHORITY_USE_HTTPS_ATTRIBUTE_NAME = "authority_use_https"
AUTHORITY_USE_HTTPS_ATTRIBUTE_UUID = "645d3690-b460-43e7-94c9-9374cf5f14b3"
AUTHORITY_USE_HTTPS_ATTRIBUTE_LABEL = "Use HTTPS"
AUTHORITY_USE_HTTPS_ATTRIBUTE_DESCRIPTION = "Use HTTPS to connect to ADCS"

# WinRM Port Attribute
AUTHORITY_WINRM_PORT_ATTRIBUTE_NAME = "authority_winrm_port"
AUTHORITY_WINRM_PORT_ATTRIBUTE_UUID = "079f9f93-adc0-48bd-96f1-095991295cb9"
AUTHORITY_WINRM_PORT_ATTRIBUTE_LABEL = "WinRM Port"
AUTHORITY_WINRM_PORT_ATTRIBUTE_DESCRIPTION = "WinRM port, default port for http is 5985 and for https 5986"

# SSH Port Attribute
AUTHORITY_SSH_PORT_ATTRIBUTE_NAME = "authority_ssh_port"
AUTHORITY_SSH_PORT_ATTRIBUTE_UUID = "1731ad64-e986-4b0d-b1cd-48d59f33e56a"
AUTHORITY_SSH_PORT_ATTRIBUTE_LABEL = "SSH Port"
AUTHORITY_SSH_PORT_ATTRIBUTE_DESCRIPTION = "SSH port, default port is 22"

# Credential Type Attribute
AUTHORITY_CREDENTIAL_TYPE_ATTRIBUTE_NAME = "authority_credential_type"
AUTHORITY_CREDENTIAL_TYPE_ATTRIBUTE_UUID = "e05beb6a-90fe-4f85-bd9f-2394d70a0a29"
AUTHORITY_CREDENTIAL_TYPE_ATTRIBUTE_LABEL = "Credential Type"
AUTHORITY_CREDENTIAL_TYPE_ATTRIBUTE_DESCRIPTION = ("Choose the credential type to use for authentication, it should be "
                                                   "compatible with selected protocol")

# Credential Attribute
AUTHORITY_CREDENTIAL_ATTRIBUTE_NAME = "authority_credential"
AUTHORITY_CREDENTIAL_ATTRIBUTE_UUID = "93d77f65-d9c4-497c-bdee-f3330eb0f209"
AUTHORITY_CREDENTIAL_ATTRIBUTE_LABEL = "Credential"
AUTHORITY_CREDENTIAL_ATTRIBUTE_DESCRIPTION = "Credential to authenticate with ADCS"
