"""Background retry of pending CRM syncs, started with the app.

Every ``CRM_SYNC_INTERVAL`` seconds (default 15) it tries the pending syncs whose back-off has passed.
``CRM_SYNC_WORKER=0`` turns it off (the test suite does, and calls ``retry_due`` directly).
"""

import asyncio
import logging
import os

from starlette.concurrency import run_in_threadpool

from backend.crm import get_crm_registry
from backend.db import SessionLocal

from .crm_sync import retry_due

logger = logging.getLogger(__name__)


def worker_enabled() -> bool:
    return os.getenv("CRM_SYNC_WORKER", "1") != "0"


def _interval() -> float:
    try:
        return max(1.0, float(os.getenv("CRM_SYNC_INTERVAL", "15")))
    except ValueError:
        return 15.0


def run_once() -> int:
    db = SessionLocal()
    try:
        return retry_due(db, get_crm_registry())
    finally:
        db.close()


async def crm_sync_worker() -> None:
    while True:
        await asyncio.sleep(_interval())
        try:
            tried = await run_in_threadpool(run_once)
            if tried:
                logger.info("CRM sync worker retried %d order(s)", tried)
        except Exception:  # noqa: BLE001 - keep retrying on the next tick
            logger.exception("CRM sync worker tick failed")
