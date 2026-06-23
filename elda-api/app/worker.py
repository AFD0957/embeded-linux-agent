"""Redis-backed background task worker."""

from __future__ import annotations

import asyncio
import logging

from app.orchestrator.pipeline import orchestrator
from app.storage.redis_queue import pop_background

logger = logging.getLogger(__name__)


async def run_task_worker(stop_event: asyncio.Event) -> None:
    logger.info("Task worker started (Redis queue)")
    while not stop_event.is_set():
        try:
            task_id = await pop_background(timeout=2)
            if task_id:
                logger.info("Dequeued task %s", task_id)
                await orchestrator.run_task(task_id)
        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("Task worker error")
            await asyncio.sleep(1.0)
    logger.info("Task worker stopped")
