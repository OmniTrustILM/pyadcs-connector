from PyADCSConnector.exceptions.authority_exception import AuthorityException
from PyADCSConnector.exceptions.remoting_exception import RemotingException
from PyADCSConnector.models.authority_instance import AuthorityInstance
from PyADCSConnector.remoting.winrm.scripts import verify_connection_script, get_cas_script, get_templates_script
from PyADCSConnector.remoting.winrm_remoting import create_session_from_authority_instance, \
    create_session_from_authority_instance_uuid
from PyADCSConnector.services.attributes.authority_attributes import *
from PyADCSConnector.utils import attribute_definition_utils
from PyADCSConnector.utils.dump_parser import DumpParser


def create_authority_instance(request_dto):
    if AuthorityInstance.objects.filter(name=request_dto["name"]).exists():
        raise AuthorityException("Authority instance with name %s already exists" % request_dto["name"])

    authority_instance: AuthorityInstance = AuthorityInstance()
    authority_instance.name = request_dto["name"]
    authority_instance.kind = request_dto["kind"]

    return update_authority_instance(request_dto, authority_instance)


def update_authority_instance(request_dto, authority_instance):
    validate_authority_kind(authority_instance.kind)

    request_attributes = request_dto["attributes"]
    authority_instance.transport = attribute_definition_utils.get_attribute_value(
        AUTHORITY_WINRM_TRANSPORT_ATTRIBUTE_NAME,
        request_attributes
    )

    original_attributes = get_all_authority_attributes_list(authority_instance.kind, authority_instance.transport)
    authority_instance.attributes = attribute_definition_utils.merge_attributes(request_attributes, original_attributes)
    authority_instance.address = attribute_definition_utils.get_attribute_value(AUTHORITY_SERVER_ADDRESS_ATTRIBUTE_NAME,
                                                                                authority_instance.attributes)
    authority_instance.https = attribute_definition_utils.get_attribute_value(AUTHORITY_USE_HTTPS_ATTRIBUTE_NAME,
                                                                              authority_instance.attributes)
    authority_instance.port = attribute_definition_utils.get_attribute_value(AUTHORITY_WINRM_PORT_ATTRIBUTE_NAME,
                                                                             authority_instance.attributes)
    authority_instance.credential = attribute_definition_utils.get_attribute_value(AUTHORITY_CREDENTIAL_ATTRIBUTE_NAME,
                                                                                   authority_instance.attributes)

    verify_connection(authority_instance)

    authority_instance.save()

    return authority_instance


def verify_connection(authority_instance):
    if authority_instance.transport == "credssp":
        session = create_session_from_authority_instance(authority_instance)
        session.connect()
        session.run_ps(verify_connection_script())
        session.disconnect()
    else:
        raise RemotingException("Unsupported transport type: %s" % authority_instance.transport)


def get_cas(authority_instance_uuid):
    session = create_session_from_authority_instance_uuid(authority_instance_uuid)
    session.connect()
    result = session.run_ps(get_cas_script())
    session.disconnect()

    # Convert string to lines
    # regular_string = result.std_out.decode('utf-8')
    cas = DumpParser.parse_authority_data(result)

    content = [
        {"reference": ca.display_name, "data": ca.__dict__} for ca in cas
    ]

    return content


def get_templates(authority_instance_uuid):
    session = create_session_from_authority_instance_uuid(authority_instance_uuid)
    session.connect()
    result = session.run_ps(get_templates_script())
    session.disconnect()

    # Convert string to lines
    # regular_string = result.std_out.decode('utf-8')
    templates = DumpParser.parse_template_data(result)

    content = [
        {"reference": template.display_name, "data": template.__dict__} for template in templates
    ]

    return content
