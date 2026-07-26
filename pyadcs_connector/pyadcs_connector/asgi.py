"""
ASGI config for pyadcs_connector project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pyadcs_connector.settings')

application = get_asgi_application()

# Started from the WSGI/ASGI entrypoints (see wsgi.py for the full notes on
# `runserver` and gunicorn --preload), not from AppConfig.ready(), so the scheduler
# runs only when the app is actually served -- never during `manage.py migrate` /
# `manage.py test` / `manage.py check`. Starting it from both entrypoints is safe:
# start_cleanup_scheduler() starts at most once.
from PyADCSConnector.services.certificate_cleanup import start_cleanup_scheduler

start_cleanup_scheduler()
