#!/bin/sh

CPU_COUNT=$(getconf _NPROCESSORS_ONLN)   # honours the cgroup CPU quota
: "${GUNICORN_WORKERS:=${CPU_COUNT:-1}}"
: "${GUNICORN_THREADS:=${GUNICORN_THREADS:-4}}"

pyadcsHome="/opt/pyadcs"
source ${pyadcsHome}/static-functions

log "INFO" "Launching PyADCS Connector"

cd /opt/pyadcs
#python manage.py migrate
python migrate.py

exec gunicorn \
  --worker-class gthread \
  --workers "$GUNICORN_WORKERS" \
  --threads  "$GUNICORN_THREADS" \
  --timeout  600 \
  --bind     0.0.0.0:8080 \
  --worker-tmp-dir /dev/shm \
  pyadcs_connector.wsgi:application

#exec "$@"
