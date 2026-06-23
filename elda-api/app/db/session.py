"""Async database session."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.db.models import Base

logger = logging.getLogger(__name__)

engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


def _run_alembic_upgrade() -> None:
    from alembic import command
    from alembic.config import Config

    ini = Path(__file__).resolve().parents[2] / "alembic.ini"
    cfg = Config(str(ini))
    command.upgrade(cfg, "head")


async def _create_tables_fallback() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def init_db() -> None:
    try:
        await asyncio.to_thread(_run_alembic_upgrade)
    except ImportError:
        logger.warning("Alembic not installed — falling back to create_all()")
        await _create_tables_fallback()
    except Exception as exc:
        logger.warning("Alembic upgrade failed (%s) — falling back to create_all()", exc)
        await _create_tables_fallback()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
