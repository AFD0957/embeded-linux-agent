"""Pytest fixtures for API tests."""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    async def _noop_init() -> None:
        return None

    async def _noop_worker(stop_event: asyncio.Event) -> None:
        stop_event.set()

    monkeypatch.setattr("app.main.init_db", _noop_init)
    monkeypatch.setattr("app.main.run_task_worker", _noop_worker)

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
