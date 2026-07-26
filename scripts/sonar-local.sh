#!/usr/bin/env bash
# Local SonarCloud analysis: run the test suite with coverage to produce the
# report Sonar consumes, then invoke sonar-scanner against SonarCloud. Requires
# SONAR_TOKEN. A PostgreSQL reachable via the DATABASE_* environment variables
# must be available (the Django test runner creates a test database).
set -euo pipefail
cd "$(dirname "$0")/.."

: "${SONAR_TOKEN:?SONAR_TOKEN must be set}"
# Capture the token and remove it from the ambient environment immediately: the
# test suite can execute repository code and must not be able to read or
# exfiltrate SONAR_TOKEN.
_sonar_token="$SONAR_TOKEN"
unset SONAR_TOKEN

# Database connection for the Django test runner. Override any of these by
# exporting them before running this script.
export DATABASE_SCHEMA="${DATABASE_SCHEMA:-pyadcs}"
export DATABASE_NAME="${DATABASE_NAME:-pyadcs}"
export DATABASE_USER="${DATABASE_USER:-pyadcs}"
export DATABASE_PASSWORD="${DATABASE_PASSWORD:-pyadcs}"
export DATABASE_HOST="${DATABASE_HOST:-localhost}"
export DATABASE_PORT="${DATABASE_PORT:-5432}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Run from the repository root so coverage file paths align with sonar.sources.
coverage run pyadcs_connector/manage.py test PyADCSConnector
coverage xml -o coverage.xml

BRANCH=$(git rev-parse --abbrev-ref HEAD)
# SONAR_TOKEN is read from the environment by sonar-scanner; never pass it as a
# CLI property (visible in process listings). It is scoped to this single
# command only, never exported globally. Project identity, sources, and the
# coverage report path come from sonar-project.properties.
SONAR_TOKEN="$_sonar_token" sonar-scanner \
  -Dsonar.host.url=https://sonarcloud.io \
  -Dsonar.branch.name="${BRANCH}" \
  -Dsonar.qualitygate.wait=true
