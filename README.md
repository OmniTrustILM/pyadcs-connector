# PyADCS Connector

PyADCS `Connector` is an ILM connector for Microsoft ADCS, called by ILM Core to issue, renew, revoke, and discover certificates over WinRM.

PyADCS `Connector` is the implementation of the following `Function Groups` and `Kinds`:

| Function Group       | Kind           |
|----------------------|----------------|
| `Authority Provider` | `PyADCS-WinRM` |
| `Discovery Provider` | `PyADCS-WinRM` |

PyADCS `Connector` is the implementation of certificate management for Microsoft ADCS that is compatible with the v2 client operations interface. The `Connector` is currently developed to work with through the WinRM protocol.

> It is expected that the SSH PowerShell will be supported in the future.

PyADCS `Connector` allows you to perform the following operations:

`Authority Provider`
- Issue certificate
- Renew certificate
- Revoke certificate

`Discovery Provider`
- Discover certificates

## Database requirements

PyADCS `Connector` requires the **PostgreSQL 14+** database version.

## Docker container

PyADCS `Connector` is provided as a Docker container. Pull the image with `docker pull hub.omnitrustregistry.com/ilm/pyadcs-connector:tagname`. It can be configured using the following environment variables:

| Variable                      | Description                                                        | Required                                           | Default value |
|-------------------------------|--------------------------------------------------------------------|----------------------------------------------------|---------------|
| `DATABASE_HOST`               | Database host                                                      | ![](https://img.shields.io/badge/-NO-red.svg)      | `localhost`   |
| `DATABASE_PORT`               | Database port                                                      | ![](https://img.shields.io/badge/-NO-red.svg)      | `5432`        |
| `DATABASE_NAME`               | PostgreSQL database name                                           | ![](https://img.shields.io/badge/-YES-success.svg) | `N/A`         |
| `DATABASE_USER`               | Username to access the database                                    | ![](https://img.shields.io/badge/-YES-success.svg) | `N/A`         |
| `DATABASE_PASSWORD`           | Password to access the database                                    | ![](https://img.shields.io/badge/-YES-success.svg) | `N/A`         |
| `DATABASE_SCHEMA`             | Database schema to use                                             | ![](https://img.shields.io/badge/-NO-red.svg)      | `pyadcs`      |
| `LOG_LEVEL`                   | Logging level, allowed values are `INFO`, `DEBUG`, `ERROR`, `WARN` | ![](https://img.shields.io/badge/-NO-red.svg)      | `INFO`        |
| `ADCS_SEARCH_PAGE_SIZE`       | Number of entries to return in one page                            | ![](https://img.shields.io/badge/-NO-red.svg)      | `1000`        |
| `ADCS_ISSUE_POLLING_INTERVAL` | Interval in milliseconds to poll for issued certificates           | ![](https://img.shields.io/badge/-NO-red.svg)      | `100`         |
| `ADCS_ISSUE_POLLING_TIMEOUT`  | Timeout in milliseconds to wait for issued certificates            | ![](https://img.shields.io/badge/-NO-red.svg)      | `3000`        |
| `GUNICORN_WORKERS`            | Number of Gunicorn worker processes                                | ![](https://img.shields.io/badge/-NO-red.svg)      | CPU count     |
| `GUNICORN_THREADS`            | Number of threads per Gunicorn worker                              | ![](https://img.shields.io/badge/-NO-red.svg)      | `4`           |
| `CERTIFICATE_CLEANUP_ENABLED` | Enables the scheduled orphaned-certificate cleanup                 | ![](https://img.shields.io/badge/-NO-red.svg)      | `true`        |
| `CERTIFICATE_CLEANUP_INTERVAL_SECONDS` | Interval in seconds between orphaned-certificate cleanup runs | ![](https://img.shields.io/badge/-NO-red.svg)      | `86400`       |
| `CERTIFICATE_CLEANUP_BATCH_SIZE` | Certificates deleted per transaction by the cleanup            | ![](https://img.shields.io/badge/-NO-red.svg)      | `1000`        |

### Certificate cleanup

PyADCS `Connector` runs a scheduled background task that removes orphaned certificate records left behind by interrupted or failed operations. It is controlled by three environment variables:

- `CERTIFICATE_CLEANUP_ENABLED` — enables or disables the scheduled cleanup (default `true`).
- `CERTIFICATE_CLEANUP_INTERVAL_SECONDS` — interval, in seconds, between cleanup runs (default `86400`, i.e. once a day).
- `CERTIFICATE_CLEANUP_BATCH_SIZE` — how many certificates are removed per transaction (default `1000`). The cleanup deletes in batches and releases its lock between them, so a large backlog cannot hold up certificate discovery.

The cleanup runs in a background thread of the served application, at most once per interval across all workers. Two deployment notes: `manage.py runserver` also starts it (set `CERTIFICATE_CLEANUP_ENABLED=false` for local development if that is unwanted), and Gunicorn must not be run with `--preload`, which imports the application in the pre-fork master so the thread starts there and is not inherited by the workers, moving the cleanup outside the worker lifecycle.
