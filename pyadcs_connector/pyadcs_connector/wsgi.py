"""
WSGI config for pyadcs_connector project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pyadcs_connector.settings')

application = get_wsgi_application()

# Started from the WSGI/ASGI entrypoints (see also asgi.py), not from
# AppConfig.ready(), so the scheduler runs only when the app is actually served --
# never during `manage.py migrate` / `manage.py test` / `manage.py check`. Starting
# it from both entrypoints is safe: start_cleanup_scheduler() starts at most once.
#
# Two consequences of starting it here:
#   - `manage.py runserver` also imports this module, so a development server runs
#     the sweep against its database too. Set CERTIFICATE_CLEANUP_ENABLED=false to
#     turn it off there.
#   - Do not run gunicorn with --preload: the app is then imported by the pre-fork
#     master, so the thread starts there and is not inherited by the forked workers.
#     Ownership of the sweep would move to the master process, outside the worker
#     lifecycle that supervises it. The shipped docker/opt/pyadcs/entry.sh
#     deliberately does not use --preload.
from PyADCSConnector.services.certificate_cleanup import start_cleanup_scheduler

start_cleanup_scheduler()
