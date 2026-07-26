import logging
import threading
import time
from datetime import timedelta

from django.conf import settings
from django.db import close_old_connections, connection, transaction
from psycopg2 import sql

from PyADCSConnector.models.certificate_cleanup_state import CertificateCleanupState

logger = logging.getLogger(__name__)

_started = False
_lock = threading.Lock()


def _schema():
    return settings.DATABASE_SCHEMA


def _claim_lease() -> int | None:
    """Take the exclusive lock and claim the interval lease in one short transaction.

    Returns the highest certificate id present at claim time (the sweep's upper
    bound), or None if this process must not sweep now. The lease is claimed up
    front (not after the deletes) so that at most one sweep per interval runs even
    if the batched deletion below is interrupted; leftover orphans are simply
    picked up by the next due sweep.
    """
    interval = timedelta(seconds=settings.CERTIFICATE_CLEANUP_INTERVAL_SECONDS)
    with transaction.atomic():
        with connection.cursor() as cur:
            cur.execute("SELECT pg_try_advisory_xact_lock(%s)", [settings.CERTIFICATE_CLEANUP_LOCK_KEY])
            if not cur.fetchone()[0]:
                return None  # a discovery or another sweep holds the lock

            # order_by(pk): migration 0002 seeds exactly one row, but pin the choice
            # so the lease stays deterministic even if a second row ever appeared.
            state = CertificateCleanupState.objects.select_for_update().order_by("pk").first()

            cur.execute("SELECT now()")
            now = cur.fetchone()[0]

            if state and state.last_run_at and (now - state.last_run_at) < interval:
                return None  # not due yet

            if state is None:
                state = CertificateCleanupState()
            state.last_run_at = now
            state.save()

            cur.execute(
                sql.SQL("SELECT coalesce(max(id), 0) FROM {schema}.{certificate}").format(
                    schema=sql.Identifier(_schema()),
                    certificate=sql.Identifier("certificate"),
                ))
            return cur.fetchone()[0]


def _delete_orphan_batch(batch_size: int, max_certificate_id: int) -> int:
    """Delete at most batch_size orphaned certificates with id <= max_certificate_id,
    in one short transaction.

    Re-takes the exclusive lock per batch and releases it on commit, so concurrent
    discovery persistence (shared lock) only ever waits for a single batch.
    """
    with transaction.atomic():
        with connection.cursor() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(%s)", [settings.CERTIFICATE_CLEANUP_LOCK_KEY])
            cur.execute(
                sql.SQL(
                    "DELETE FROM {schema}.{certificate} "
                    "WHERE id IN ("
                    "SELECT c.id FROM {schema}.{certificate} c "
                    "WHERE c.id <= %s AND NOT EXISTS ("
                    "SELECT 1 FROM {schema}.{discovery_certificate} dc "
                    "WHERE dc.certificate_id = c.id) "
                    "LIMIT %s)"
                ).format(
                    schema=sql.Identifier(_schema()),
                    certificate=sql.Identifier("certificate"),
                    discovery_certificate=sql.Identifier("discovery_certificate"),
                ),
                [max_certificate_id, batch_size])
            return cur.rowcount


def run_cleanup_once() -> int | None:
    """Lease-gated, advisory-locked orphan sweep. Returns deleted count if it ran, else None.

    Each sweep only considers certificates that already existed when it claimed the
    lease, so it always terminates: rows created while it runs (including newly
    orphaned ones) are left for the next due sweep instead of extending this one
    indefinitely under continuous churn.
    """
    max_certificate_id = _claim_lease()
    if max_certificate_id is None:
        return None

    batch_size = max(1, settings.CERTIFICATE_CLEANUP_BATCH_SIZE)
    deleted = 0
    while True:
        in_batch = _delete_orphan_batch(batch_size, max_certificate_id)
        deleted += in_batch
        if in_batch < batch_size:
            break

    logger.info("Orphan certificate cleanup removed %d certificate(s)", deleted)
    return deleted


def _loop():
    poll = min(settings.CERTIFICATE_CLEANUP_INTERVAL_SECONDS, 3600)
    while True:
        close_old_connections()
        try:
            run_cleanup_once()
        except Exception:
            logger.exception("Orphan certificate cleanup failed")
        finally:
            close_old_connections()
        time.sleep(poll)


def start_cleanup_scheduler():
    global _started
    if not settings.CERTIFICATE_CLEANUP_ENABLED:
        return
    if settings.CERTIFICATE_CLEANUP_INTERVAL_SECONDS <= 0:
        logger.warning("CERTIFICATE_CLEANUP_INTERVAL_SECONDS must be positive; scheduler disabled")
        return
    with _lock:
        if _started:
            return
        _started = True
    threading.Thread(target=_loop, name="certificate-cleanup", daemon=True).start()
    logger.info("Certificate cleanup scheduler started")
