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

PyADCS `Connector` requires the PostgreSQL database version 12+.

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
