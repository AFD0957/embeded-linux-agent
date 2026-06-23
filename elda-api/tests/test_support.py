"""Shared helpers for integration tests."""

from __future__ import annotations

import os

from app.secrets_loader import load_api_secrets


def is_real_api_key(key: str) -> bool:
    if not key or len(key.strip()) < 12:
        return False
    lowered = key.lower()
    placeholders = ("your-", "sk-your", "sk-xxx", "changeme", "placeholder")
    return not any(p in lowered for p in placeholders)


def bailian_configured() -> bool:
    load_api_secrets.cache_clear()
    return is_real_api_key(load_api_secrets().bailian.api_key)


def deepseek_configured() -> bool:
    load_api_secrets.cache_clear()
    return is_real_api_key(load_api_secrets().deepseek.api_key)


def integration_enabled() -> bool:
    """Explicit opt-in for CI or air-gapped runs."""
    return os.environ.get("ELDA_RUN_INTEGRATION_TESTS", "").lower() in ("1", "true", "yes")


def should_run_integration() -> bool:
    return integration_enabled()
