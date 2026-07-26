import base64
import logging

from cryptography import x509
from cryptography.hazmat.backends import default_backend

from pyadcs_connector.settings import ADCS_ISSUE_POLLING_INTERVAL, ADCS_ISSUE_POLLING_TIMEOUT
from PyADCSConnector.exceptions.not_found_exception import NotFoundException
from PyADCSConnector.exceptions.validation_exception import ValidationException
from PyADCSConnector.objects.certificate_dto import CertificateDto
from PyADCSConnector.remoting.winrm.scripts import get_revoke_script, identify_certificate_script, \
    submit_certificate_request_script
from PyADCSConnector.remoting.winrm_remoting import create_session_from_authority_instance_uuid
from PyADCSConnector.services.attributes.raprofile_attributes import RAPROFILE_TEMPLATE_NAME_ATTRIBUTE_NAME, \
    RAPROFILE_SELECT_CA_METHOD_ATTRIBUTE_NAME, RAPROFILE_CA_NAME_ATTRIBUTE_NAME, RAPROFILE_CONFIGSTRING_ATTRIBUTE_NAME
from PyADCSConnector.utils import attribute_definition_utils
from PyADCSConnector.utils.ca_select_method import CaSelectMethod
from PyADCSConnector.utils.cms_utils import create_cms
from PyADCSConnector.utils.dump_parser import TemplateData, DumpParser, AuthorityData
from PyADCSConnector.objects.certificate_request_format import CertificateRequestFormat

logger = logging.getLogger(__name__)


def issue(request_dto, uuid):
    logger.debug("Issuing new certificate with request: %s" % request_dto["request"])
    return prepare_and_issue(request_dto, uuid)


def renew(request_dto, uuid):
    serial_number = get_certificate_serial_number(request_dto["certificate"])
    logger.debug("Renew certificate with serial number %s" % serial_number)
    return prepare_and_issue(request_dto, uuid)


def revoke(request_dto, uuid):
    ca = get_ca_from_attributes(request_dto)

    reason = request_dto["reason"]
    serial_number = get_certificate_serial_number(request_dto["certificate"])

    session = create_session_from_authority_instance_uuid(uuid)
    session.connect()
    session.run_ps(get_revoke_script(ca, serial_number, reason))
    session.disconnect()

    return


def identify(request_dto, uuid):
    ca = get_ca_from_attributes(request_dto)

    template = TemplateData.from_dict(
        attribute_definition_utils.get_attribute_value(
            RAPROFILE_TEMPLATE_NAME_ATTRIBUTE_NAME, request_dto["raProfileAttributes"]))
    certificate = request_dto["certificate"]

    # Convert certificate to x509 using cryptography module, it should be in base64 format
    x509_cert = x509.load_der_x509_certificate(base64.b64decode(certificate), default_backend())
    serial_number = '{0:x}'.format(x509_cert.serial_number)

    session = create_session_from_authority_instance_uuid(uuid)
    session.connect()
    logger.debug("Identify certificate with serial number %s" % serial_number)
    result = session.run_ps(identify_certificate_script(serial_number, ca))
    session.disconnect()

    parsed = DumpParser.parse_identified_certificates(result)
    if not parsed:
        raise NotFoundException("Certificate not found")
    elif len(parsed) > 1:  # this should not happen, CA should not issue 2 certificates with the same SN
        raise ValidationException("More than one certificate found")
    else:  # we have one certificate issued by the CA
        if parsed[0].certificate_template == template.oid or parsed[0].certificate_template == template.name:
            response = dict()
            response["meta"] = []
            return response
        else:
            raise ValidationException("Certificate found but template does not match according to"
                                      " RA Profile attributes")


def prepare_and_issue(request_dto, uuid):
    ca = get_ca_from_attributes(request_dto)

    template = TemplateData.from_dict(
        attribute_definition_utils.get_attribute_value(
            RAPROFILE_TEMPLATE_NAME_ATTRIBUTE_NAME, request_dto["raProfileAttributes"]))

    try:
        request_format = CertificateRequestFormat(request_dto["format"])
    except ValueError:
        raise ValidationException("Certificate request format '" + request_dto["format"] + "' is not supported.")

    return issue_new_certificate(uuid, request_dto["request"], request_format, ca, template)


def issue_new_certificate(uuid, certificate_request, request_format: CertificateRequestFormat, ca: AuthorityData,
                          template: TemplateData):
    if request_format == CertificateRequestFormat.CRMF:
        certificate_request = create_cms(certificate_request, ca.name, template).decode()
    session = create_session_from_authority_instance_uuid(uuid)
    session.connect()
    result = session.run_ps(
        submit_certificate_request_script(
            certificate_request, ca, template, ADCS_ISSUE_POLLING_INTERVAL, ADCS_ISSUE_POLLING_TIMEOUT
        )
    )
    session.disconnect()

    # Remove new lines and empty lines to form one Base64 string
    certificate = get_certificate_data(result)
    # If certificate is empty
    if not certificate:
        raise ValidationException("Output of the certificate is empty, check the logs of the ADCS server.")

    certificate_dto = CertificateDto(certificate, None, None)
    return certificate_dto


def get_certificate_data(result):
    input_string = result.std_out.decode('utf-8')
    return ''.join(input_string.splitlines())


def get_certificate_serial_number(certificate):
    """
    Get serial number from certificate in base64 format
    :param certificate: certificate in base64 format
    :return: serial number in hex format
    """
    x509_cert = x509.load_der_x509_certificate(base64.b64decode(certificate), default_backend())
    return '{0:x}'.format(x509_cert.serial_number)


def get_ca_from_attributes(request_dto):
    select_ca_method = attribute_definition_utils.get_attribute_value(
        RAPROFILE_SELECT_CA_METHOD_ATTRIBUTE_NAME, request_dto["raProfileAttributes"])

    if select_ca_method == CaSelectMethod.SEARCH.method:
        ca = AuthorityData.from_dict(
            attribute_definition_utils.get_attribute_value(
                RAPROFILE_CA_NAME_ATTRIBUTE_NAME, request_dto["raProfileAttributes"]))
    elif select_ca_method == CaSelectMethod.CONFIGSTRING.method:
        config_string = attribute_definition_utils.get_attribute_value(
            RAPROFILE_CONFIGSTRING_ATTRIBUTE_NAME, request_dto["raProfileAttributes"])
        if not config_string:
            raise Exception("ConfigString is required with selected CA Method: " + select_ca_method)
        ca_name = config_string.split("\\")[1]
        computer_name = config_string.split("\\")[0]
        if not ca_name or not computer_name:
            raise Exception("Wrong format of ConfigString: " + config_string)
        ca = AuthorityData(
            config_string.split("\\")[1], config_string.split("\\")[1], config_string.split("\\")[0],
            config_string, "", None, None, None, None)
    else:
        raise Exception("Unknown CA Select Method: " + select_ca_method)

    return ca
