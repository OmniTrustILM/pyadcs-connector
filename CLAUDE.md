# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run

```bash
# From the Django project dir
cd pyadcs_connector
python manage.py check
python manage.py test                 # requires a PostgreSQL reachable via DATABASE_* env

# From the repo root (.coveragerc's source is repo-root-relative)
coverage run pyadcs_connector/manage.py test PyADCSConnector && coverage xml   # coverage report

# Container
docker build -f Dockerfile -t pyadcs-connector .
```

## Architecture

An ILM platform connector for Microsoft ADCS (via WinRM). It implements two function groups,
both kind `PyADCS-WinRM`:
- **Authority Provider** — issue / renew / revoke / identify certificates (v2 interface).
- **Discovery Provider** — discover certificates.

Django project layout:
- `pyadcs_connector/` — Django config package (`settings`, `urls`, `wsgi`, `asgi`).
- `PyADCSConnector/` — the application (**app label `PyADCSConnector`**), with `views/`,
  `services/`, `serializers/`, `objects/`, `models/`, `utils/`, and `remoting/` (WinRM).

## Database & compatibility invariant

PostgreSQL (14+). Tables live in the schema from `DATABASE_SCHEMA` (default `pyadcs`) and are pinned
via each model's `db_table`. **Do not** rename the app label `PyADCSConnector` or change the schema
default — both are part of the upgrade contract and would break existing deployments.

## Required environment variables

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_NAME` | — | required |
| `DATABASE_USER` | — | required |
| `DATABASE_PASSWORD` | — | required |
| `DATABASE_HOST` | `localhost` | |
| `DATABASE_PORT` | `5432` | |
| `DATABASE_SCHEMA` | `pyadcs` | table schema/prefix |
| `LOG_LEVEL` | `INFO` | |
| `ADCS_SEARCH_PAGE_SIZE` | `1000` | |
| `ADCS_ISSUE_POLLING_INTERVAL` | `100` | ms |
| `ADCS_ISSUE_POLLING_TIMEOUT` | `3000` | ms |
| `GUNICORN_WORKERS` | CPU count | container |
| `GUNICORN_THREADS` | `4` | container |
| `CERTIFICATE_CLEANUP_ENABLED` | `true` | scheduled orphan-certificate sweep |
| `CERTIFICATE_CLEANUP_INTERVAL_SECONDS` | `86400` | at most one sweep per interval across workers |
| `CERTIFICATE_CLEANUP_BATCH_SIZE` | `1000` | rows per transaction; lock released between batches |
