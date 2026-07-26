from django.http import JsonResponse

import logging

from PyADCSConnector.exceptions.authority_exception import AuthorityException
from PyADCSConnector.exceptions.discovery_exception import DiscoveryException
from PyADCSConnector.exceptions.not_found_exception import NotFoundException
from PyADCSConnector.exceptions.validation_exception import ValidationException
from PyADCSConnector.exceptions.winrm_execution_exception import WinRMExecutionException

logger = logging.getLogger(__name__)


class ExceptionHandlerMiddleware:
    """Handle uncaught exceptions instead of raising a 500.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    @staticmethod
    def process_exception(request, exception):
        """
        Handle uncaught exceptions.
        """
        if isinstance(exception, NotFoundException):
            logger.info("(404) NotFoundException occurred: " + str(exception))
            # logger.exception(exception)
            return JsonResponse({'message': str(exception)}, status=404)
        if isinstance(exception, ValidationException):
            logger.info("(422) ValidationException occurred: " + str(exception))
            # logger.exception(exception)
            return JsonResponse([str(exception)], status=422, safe=False)
        if isinstance(exception, WinRMExecutionException):
            logger.info("(400) WinRMExecutionException occurred: " + str(exception))
            # logger.exception(exception)
            return JsonResponse({'message': str(exception)}, status=400)
        if isinstance(exception, AuthorityException):
            logger.info("(400) AuthorityException occurred: " + str(exception))
            # logger.exception(exception)
            return JsonResponse({'message': str(exception)}, status=400)
        if isinstance(exception, DiscoveryException):
            logger.info("(400) DiscoveryException occurred: " + str(exception))
            # logger.exception(exception)
            return JsonResponse({'message': str(exception)}, status=400)
        if isinstance(exception, Exception):
            logger.error("(500) Exception occurred: " + str(exception))
            logger.exception(exception)
            # Or you could return json for your frontend app
            return JsonResponse({'message': str(exception)}, status=500)

        return None  # Middlewares should return None when not applied
