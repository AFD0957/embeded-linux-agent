#!/bin/sh
set -e
# DB init: alembic (needs psycopg2) or create_all via asyncpg — must not silently skip.
python - <<'PY'
import asyncio
import logging

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    from app.db.session import _create_tables_fallback, _run_alembic_upgrade

    try:
        await asyncio.to_thread(_run_alembic_upgrade)
        print("==> alembic upgrade: OK")
    except Exception as exc:
        print(f"==> alembic upgrade: WARN ({exc}) — falling back to create_all")
        await _create_tables_fallback()
        print("==> create_all: OK")


asyncio.run(main())
PY
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --loop asyncio --http h11
