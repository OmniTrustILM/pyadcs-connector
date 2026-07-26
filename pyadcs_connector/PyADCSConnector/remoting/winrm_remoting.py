import logging
from base64 import b64encode

import winrm

from PyADCSConnector.exceptions.winrm_execution_exception import WinRMExecutionException
from PyADCSConnector.models.authority_instance import AuthorityInstance
from PyADCSConnector.utils import attribute_definition_utils

logger = logging.getLogger(__name__)


class WinRmRemoting(object):
    def __init__(self, username, password, hostname, use_https=False, port=5985, transport='credssp'):
        self.shell_id = None
        self.username = username
        self.password = password
        self.hostname = hostname
        self.use_https = use_https
        self.port = port
        self.transport = transport
        self.protocol = None

    def connect(self):
        self.protocol = winrm.Protocol(
            endpoint='http' + ('s' if self.use_https else '') + '://' + self.hostname + ':' + str(self.port) + '/wsman',
            transport=self.transport,
            username=self.username,
            password=self.password)
        self.shell_id = self.protocol.open_shell()

    def run(self, command, args=()):
        logger.debug("Running command: " + command + " " + str(args))
        command_id = self.protocol.run_command(self.shell_id, command, args)
        result = winrm.Response(self.protocol.get_command_output(self.shell_id, command_id))
        self.protocol.cleanup_command(self.shell_id, command_id)

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Return code: " + str(result.status_code))
            if result.status_code != 0:
                logger.debug("Error: " + result.std_err.decode(encoding='utf-8'))
            else:
                logger.debug("Output: " + result.std_out.decode(encoding='utf-8'))

        check_result(result)
        return result

    def run_ps(self, script):
        """base64 encodes a Powershell script and executes the powershell encoded script command"""
        logger.debug("Running Powershell script: " + script)
        # must use utf16 little endian on windows
        encoded_ps = b64encode(script.encode('utf_16_le')).decode('ascii')
        result = self.run('powershell -encodedcommand {0}'.format(encoded_ps))
        return result

    def disconnect(self):
        self.protocol.close_shell(self.shell_id)
        self.protocol = None
        self.shell_id = None


def check_result(result):
    if result.status_code != 0:
        raise WinRMExecutionException(result.status_code, result.std_err.decode('utf-8'))


def create_session_from_authority_instance_name(authority_instance_name):
    authority_instance = AuthorityInstance.objects.get(name=authority_instance_name)
    return create_session_from_authority_instance(authority_instance)


def create_session_from_authority_instance_uuid(authority_instance_uuid):
    authority_instance = AuthorityInstance.objects.get(uuid=authority_instance_uuid)
    return create_session_from_authority_instance(authority_instance)


def create_session_from_authority_instance(authority_instance):
    username = attribute_definition_utils.get_attribute_value("username",
                                                              authority_instance.credential.get("attributes"))
    password = attribute_definition_utils.get_attribute_value("password",
                                                              authority_instance.credential.get("attributes"))

    # check if password is in the form { "secret": "password" } and if yes, extract the password only
    # this is related to the change in the ILM platform version 2.12.0
    if isinstance(password, dict):
        password = password.get("secret")

    session = WinRmRemoting(username, password, authority_instance.address, authority_instance.https,
                            authority_instance.port)
    return session
