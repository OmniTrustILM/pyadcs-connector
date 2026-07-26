import logging
import threading

from django.db import connection, transaction

from pyadcs_connector.settings import ADCS_SEARCH_PAGE_SIZE, CERTIFICATE_CLEANUP_LOCK_KEY
from PyADCSConnector.exceptions.already_exist_exception import AlreadyExistException
from PyADCSConnector.models.certificate import Certificate
from PyADCSConnector.models.discovery_certificate import DiscoveryCertificate
from PyADCSConnector.models.discovery_history import DiscoveryHistory
from PyADCSConnector.objects.authority_instance_attribute import AuthorityInstanceAttribute
from PyADCSConnector.objects.discovery_certificate_dto import DiscoveryCertificateDto
from PyADCSConnector.objects.discovery_history_request_dto import DiscoveryHistoryRequestDto
from PyADCSConnector.objects.discovery_history_response_dto import DiscoveryHistoryResponseDto
from PyADCSConnector.remoting.winrm.scripts import get_cas_script, dump_certificates_script
from PyADCSConnector.remoting.winrm_remoting import create_session_from_authority_instance
from PyADCSConnector.services.attributes.discovery_attributes import *
from PyADCSConnector.services.attributes.metadata_attributes import get_ca_name_metadata_attribute, \
    get_template_name_metadata_attribute, get_failed_reason_metadata_attribute
from PyADCSConnector.utils import attribute_definition_utils
from PyADCSConnector.utils.certificate_fingerprint import certificate_fingerprint
from PyADCSConnector.utils.discovery_status import DiscoveryStatus
from PyADCSConnector.utils.dump_parser import AuthorityData, TemplateData, DumpParser

logger = logging.getLogger(__name__)


@transaction.atomic
def create_discovery_history(request_dto):
    validate_discovery_kind(request_dto["kind"])

    if DiscoveryHistory.objects.filter(name=request_dto["name"]).exists():
        raise AlreadyExistException("DiscoveryHistory", request_dto["name"])

    discovery_history: DiscoveryHistory = DiscoveryHistory()
    discovery_history.name = request_dto["name"]
    discovery_history.status = DiscoveryStatus.IN_PROGRESS.value

    discovery_history.save()

    return discovery_history


# Run certificate discovery asynchronously
def run_discovery(form, discovery_history_uuid):
    logger.debug("Starting discovery for %s in a new thread %s" % (form["name"], threading.get_ident()))
    discovery_history = DiscoveryHistory.objects.get(uuid=discovery_history_uuid)
    try:
        discover_certificates(form, discovery_history)
    except Exception as e:
        # Filtered update (not discovery_history.save()) so a discovery deleted
        # concurrently during discovery is not resurrected.
        DiscoveryHistory.objects.filter(uuid=discovery_history_uuid).update(
            status=DiscoveryStatus.FAILED.value, meta=[get_failed_reason_metadata_attribute(str(e))])
        raise e


def discover_certificates(request_dto, discovery_history):
    logger.info("Starting discovery for %s" % request_dto["name"])

    select_ca_method = attribute_definition_utils.get_attribute_value(
        DISCOVERY_SELECT_CA_METHOD_ATTRIBUTE_NAME, request_dto["attributes"])
    authority_instance = AuthorityInstanceAttribute.from_dict(
        attribute_definition_utils.get_attribute_value(
            DISCOVERY_AUTHORITY_INSTANCE_ATTRIBUTE_NAME, request_dto["attributes"]))

    authority = AuthorityInstance.objects.get(uuid=authority_instance.uuid)

    if select_ca_method == CaSelectMethod.SEARCH.method:
        cas = AuthorityData.from_dicts(
            attribute_definition_utils.get_attribute_value_list(
                DISCOVERY_CA_NAME_ATTRIBUTE_NAME, request_dto["attributes"]))
    elif select_ca_method == CaSelectMethod.CONFIGSTRING.method:
        config_string = attribute_definition_utils.get_attribute_value(
            DISCOVERY_CONFIGSTRING_ATTRIBUTE_NAME, request_dto["attributes"])
        if not config_string:
            raise Exception("ConfigString is required with selected CA Method: " + select_ca_method)
        ca_name = config_string.split("\\")[1]
        computer_name = config_string.split("\\")[0]
        if not ca_name or not computer_name:
            raise Exception("Wrong format of ConfigString: " + config_string)
        cas = [AuthorityData(
            config_string.split("\\")[1], config_string.split("\\")[1], config_string.split("\\")[0],
            config_string, "", None, None, None, None)]
    else:
        raise Exception("Unknown CA Select Method: " + select_ca_method)

    templates = TemplateData.from_dicts(
        attribute_definition_utils.get_attribute_value_list(
            DISCOVERY_TEMPLATE_NAME_ATTRIBUTE_NAME, request_dto["attributes"]))
    issued_after = attribute_definition_utils.get_attribute_value(
        DISCOVERY_ISSUED_AFTER_ATTRIBUTE_NAME, request_dto["attributes"])

    logger.debug("Authority instance: %s, CA names: %s, Template names: %s" %
                 (authority_instance, cas, templates))

    session = create_session_from_authority_instance(authority)
    session.connect()

    # if ca_names is empty, then get all CAs
    # Listing many CAs can be slow when some are unreachable; results are returned once collection completes.
    if not cas:
        result = session.run_ps(get_cas_script())
        cas = DumpParser.parse_authority_data(result)

    total_certificates = []
    for ca in cas:
        if not templates:
            page = 1
            result = session.run_ps(dump_certificates_script(
                ca, None, issued_after, 1, ADCS_SEARCH_PAGE_SIZE))
            certificates = DumpParser.parse_certificates(result)
            total_certificates.extend(certificates)
            while len(certificates) == ADCS_SEARCH_PAGE_SIZE:
                page += 1
                result = session.run_ps(dump_certificates_script(
                    ca, None, issued_after, page, ADCS_SEARCH_PAGE_SIZE))
                certificates = DumpParser.parse_certificates(result)
                total_certificates.extend(certificates)
        else:
            for template in templates:
                page = 1
                result = session.run_ps(dump_certificates_script(
                    ca, template, issued_after, page, ADCS_SEARCH_PAGE_SIZE))
                certificates = DumpParser.parse_certificates(result)
                total_certificates.extend(certificates)
                while len(certificates) == ADCS_SEARCH_PAGE_SIZE:
                    page += 1
                    result = session.run_ps(dump_certificates_script(
                        ca, template, issued_after, page, ADCS_SEARCH_PAGE_SIZE))
                    certificates = DumpParser.parse_certificates(result)
                    total_certificates.extend(certificates)

    session.disconnect()

    logger.info("Discovery %s has total %d certificates" % (request_dto["name"], len(total_certificates)))

    # Persistence happens in one short transaction, after all WinRM I/O has
    # completed, so we don't hold DB locks for the duration of the (slow,
    # network-bound) collection above.
    fingerprints = [certificate_fingerprint(c.certificate) for c in total_certificates]
    with transaction.atomic():
        with connection.cursor() as cur:
            # Shared lock: coordinates with the certificate cleanup sweep's
            # exclusive lock so a concurrent sweep can't remove certificates
            # this discovery is about to (re)link.
            cur.execute("SELECT pg_advisory_xact_lock_shared(%s)", [CERTIFICATE_CLEANUP_LOCK_KEY])

        # Abort if the discovery was deleted while we were collecting via WinRM
        # (no resurrection of a deleted discovery).
        dh = DiscoveryHistory.objects.select_for_update().filter(id=discovery_history.id).first()
        if dh is None:
            logger.info("Discovery %s was deleted during collection; skipping persistence" % request_dto["name"])
            return

        unique = dict(zip(fingerprints, total_certificates))
        # Insert in deterministic (ascending fingerprint) order: two concurrent
        # discoveries inserting overlapping NEW fingerprints in different orders
        # can otherwise deadlock against each other in Postgres.
        Certificate.objects.bulk_create(
            [Certificate(fingerprint=fp, base64content=c.certificate) for fp, c in sorted(unique.items())],
            ignore_conflicts=True)
        id_by_fp = dict(Certificate.objects.filter(fingerprint__in=unique.keys())
                         .values_list("fingerprint", "id"))
        DiscoveryCertificate.objects.bulk_create([
            DiscoveryCertificate(discovery_id=dh.id, certificate_id=id_by_fp[fp],
                                  meta=get_certificate_meta(cas, cert.template))
            for fp, cert in zip(fingerprints, total_certificates)])

        dh.status = DiscoveryStatus.COMPLETED.value
        dh.save(update_fields=["status"])

    logger.info("Discovery %s completed" % request_dto["name"])


def get_discovery_history_data(discovery_history_request: DiscoveryHistoryRequestDto, discovery_history):

    discovery_history_response = DiscoveryHistoryResponseDto()
    discovery_history_response.name = discovery_history.name
    discovery_history_response.uuid = discovery_history.uuid
    discovery_history_response.status = discovery_history.status
    discovery_history_response.meta = discovery_history.meta

    total_certificates = DiscoveryCertificate.objects.filter(discovery_id=discovery_history.id).count()

    discovery_history_response.total_certificates_discovered = total_certificates

    if discovery_history.status == DiscoveryStatus.IN_PROGRESS:
        discovery_history_response.certificate_data = []
        discovery_history_response.total_certificates_discovered = 0
    else:
        page_number = 0 if discovery_history_request.page_number <= 0 else discovery_history_request.page_number - 1
        items_per_page = discovery_history_request.items_per_page

        # select from DiscoveryCertificate where discovery_id = discovery_history.id limit items_per_page offset
        # page_number * items_per_page
        # discovery_certificates = DiscoveryCertificate.objects.filter(
        #     discovery_id=discovery_history.id)[page_number * items_per_page:items_per_page]
        discovery_certificates = DiscoveryCertificate.objects.filter(
            discovery_id=discovery_history.id
        ).select_related('certificate').order_by('uuid')[
            page_number * items_per_page:(page_number + 1) * items_per_page]

        discovery_history_response.certificate_data = [
            DiscoveryCertificateDto(val.uuid, val.certificate.base64content, val.meta).to_json()
            for val in discovery_certificates
        ]

    return discovery_history_response


def get_certificate_meta(cas, template_name):
    meta_list = [get_ca_name_metadata_attribute(cas[0].name), get_template_name_metadata_attribute(template_name)]

    return meta_list
