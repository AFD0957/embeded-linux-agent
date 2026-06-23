"""Redis — task events, executor heartbeat, log streams."""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

_client: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _client
    if _client is None:
        _client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _client


async def publish_task_log(task_id: str, line: str) -> None:
    r = get_redis()
    key = f"elda:task:{task_id}:logs"
    await r.rpush(key, line)
    await r.expire(key, 86400 * 7)


async def get_task_logs(task_id: str, start: int = 0, end: int = -1) -> list[str]:
    r = get_redis()
    return await r.lrange(f"elda:task:{task_id}:logs", start, end)


async def set_executor_heartbeat(executor_id: str, meta: dict[str, Any]) -> None:
    r = get_redis()
    await r.setex(f"elda:executor:{executor_id}", 60, json.dumps(meta))


async def enqueue_background(task_id: str) -> None:
    r = get_redis()
    await r.lpush("elda:task_queue", task_id)


async def pop_background(timeout: int = 5) -> str | None:
    r = get_redis()
    item = await r.brpop("elda:task_queue", timeout=timeout)
    return item[1] if item else None
