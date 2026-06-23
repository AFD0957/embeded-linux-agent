"""Integration test — Bailian embedding client on elda CLI side."""

from __future__ import annotations

import os

import pytest

from elda.secrets_loader import load_api_secrets


def _is_real_key(key: str) -> bool:
    if not key or len(key.strip()) < 12:
        return False
    lowered = key.lower()
    return "your-" not in lowered and "placeholder" not in lowered


def _integration_enabled() -> bool:
    return os.environ.get("ELDA_RUN_INTEGRATION_TESTS", "").lower() in ("1", "true", "yes")


@pytest.mark.integration
@pytest.mark.skipif(not _integration_enabled(), reason="Set ELDA_RUN_INTEGRATION_TESTS=1")
def test_embedding_client_sync():
    load_api_secrets.cache_clear()
    secrets = load_api_secrets()
    if not _is_real_key(secrets.bailian.api_key):
        pytest.skip("Bailian API key not configured")

    from elda.rag.embeddings import EmbeddingClient

    client = EmbeddingClient()
    vectors = client.embed_sync(["imx6ull icm20608 spi"])
    assert len(vectors) == 1
    assert len(vectors[0]) == secrets.bailian.embedding_dimensions
