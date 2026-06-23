"""Integration tests — local Docker services (Redis / MinIO / Milvus / Postgres).

Services run via docker compose on localhost; no public network required.

Skipped by default unless ELDA_RUN_INTEGRATION_TESTS=1.

  docker compose up -d
  export ELDA_RUN_INTEGRATION_TESTS=1
  pytest elda-api/tests/test_docker_services.py -v
"""

from __future__ import annotations

import os

import httpx
import pytest

from test_support import should_run_integration

pytestmark = pytest.mark.integration

API_URL = os.environ.get("ELDA_API_URL", "http://localhost:8000")
REDIS_URL = os.environ.get("ELDA_REDIS_URL", "redis://localhost:6379/0")
MINIO_ENDPOINT = os.environ.get("ELDA_MINIO_ENDPOINT", "localhost:9000")
MILVUS_HOST = os.environ.get("ELDA_MILVUS_HOST", "localhost")
MILVUS_PORT = int(os.environ.get("ELDA_MILVUS_PORT", "19530"))


def _reachable(host: str, port: int, timeout: float = 2.0) -> bool:
    import socket

    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


@pytest.mark.skipif(not should_run_integration(), reason="Set ELDA_RUN_INTEGRATION_TESTS=1")
def test_elda_api_health():
    try:
        r = httpx.get(f"{API_URL.rstrip('/')}/health", timeout=5.0)
    except httpx.HTTPError:
        pytest.skip(f"elda-api not reachable at {API_URL}")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


@pytest.mark.skipif(not should_run_integration(), reason="Set ELDA_RUN_INTEGRATION_TESTS=1")
@pytest.mark.asyncio
async def test_redis_ping():
    if not _reachable("localhost", 6379):
        pytest.skip("Redis not listening on localhost:6379")
    import redis.asyncio as aioredis

    client = aioredis.from_url(REDIS_URL)
    try:
        assert await client.ping()
    finally:
        await client.aclose()


@pytest.mark.skipif(not should_run_integration(), reason="Set ELDA_RUN_INTEGRATION_TESTS=1")
def test_minio_bucket():
    if not _reachable("localhost", 9000):
        pytest.skip("MinIO not listening on localhost:9000")
    from minio import Minio

    access_key = os.environ.get("ELDA_MINIO_ACCESS_KEY", "")
    secret_key = os.environ.get("ELDA_MINIO_SECRET_KEY", "")
    if not access_key or not secret_key:
        pytest.skip("ELDA_MINIO_ACCESS_KEY / ELDA_MINIO_SECRET_KEY not set (source .env)")
    client = Minio(
        MINIO_ENDPOINT,
        access_key=access_key,
        secret_key=secret_key,
        secure=False,
    )
    bucket = os.environ.get("ELDA_MINIO_BUCKET", "elda-artifacts")
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    assert client.bucket_exists(bucket)


@pytest.mark.skipif(not should_run_integration(), reason="Set ELDA_RUN_INTEGRATION_TESTS=1")
def test_milvus_connect():
    if not _reachable(MILVUS_HOST, MILVUS_PORT):
        pytest.skip(f"Milvus not reachable at {MILVUS_HOST}:{MILVUS_PORT}")
    from pymilvus import connections, utility

    connections.connect(alias="test", host=MILVUS_HOST, port=str(MILVUS_PORT))
    try:
        utility.list_collections(using="test")
    finally:
        connections.disconnect("test")


@pytest.mark.skipif(not should_run_integration(), reason="Set ELDA_RUN_INTEGRATION_TESTS=1")
def test_postgres_port():
    if not _reachable("localhost", 5432):
        pytest.skip("PostgreSQL not listening on localhost:5432")
    # port probe only; full DB coverage requires asyncpg connection string
    assert True
