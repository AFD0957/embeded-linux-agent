"""Integration tests — external LLM / embedding APIs (require network + API keys).

Services:
  - Bailian DashScope: chat/completions (Coder, Extractor), embeddings (RAG)
  - DeepSeek: chat/completions (Planner, Fixer, Diagnostician, Chat)

Skipped by default unless ELDA_RUN_INTEGRATION_TESTS=1 and API keys are set.

  export ELDA_RUN_INTEGRATION_TESTS=1
  pytest elda-api/tests/test_external_apis.py -v
"""

from __future__ import annotations

import pytest

from app.models.providers import (
    BailianEmbeddingProvider,
    BailianProvider,
    DeepSeekProvider,
    get_embedder,
    get_providers,
)
from app.secrets_loader import load_api_secrets

from test_support import bailian_configured, deepseek_configured, should_run_integration

pytestmark = pytest.mark.integration


@pytest.fixture
def secrets():
    load_api_secrets.cache_clear()
    return load_api_secrets()


@pytest.mark.skipif(not should_run_integration(), reason="Set ELDA_RUN_INTEGRATION_TESTS=1")
@pytest.mark.skipif(not bailian_configured(), reason="Bailian API key not in secrets/api_keys.yaml")
@pytest.mark.asyncio
async def test_bailian_chat_completion(secrets):
    provider = BailianProvider(
        secrets.bailian.api_key,
        secrets.bailian.code_model,
        secrets.bailian.base_url,
    )
    text = await provider.chat(
        [{"role": "user", "content": "Reply with exactly: ELDA_OK"}],
    )
    assert text
    assert len(text.strip()) > 0


@pytest.mark.skipif(not should_run_integration(), reason="Set ELDA_RUN_INTEGRATION_TESTS=1")
@pytest.mark.skipif(not bailian_configured(), reason="Bailian API key not in secrets/api_keys.yaml")
@pytest.mark.asyncio
async def test_bailian_chat_json(secrets):
    provider = BailianProvider(
        secrets.bailian.api_key,
        secrets.bailian.code_model,
        secrets.bailian.base_url,
    )
    data = await provider.chat_json(
        [{"role": "user", "content": 'Return JSON: {"status":"ok","value":42}'}],
    )
    assert isinstance(data, dict)
    assert data.get("status") == "ok"


@pytest.mark.skipif(not should_run_integration(), reason="Set ELDA_RUN_INTEGRATION_TESTS=1")
@pytest.mark.skipif(not bailian_configured(), reason="Bailian API key not in secrets/api_keys.yaml")
@pytest.mark.asyncio
async def test_bailian_embedding(secrets):
    embedder = BailianEmbeddingProvider(
        secrets.bailian.api_key,
        secrets.bailian.embedding_model,
        secrets.bailian.embedding_dimensions,
        secrets.bailian.base_url,
    )
    vectors = await embedder.embed(["ICM20608 SPI IIO driver"])
    assert len(vectors) == 1
    assert len(vectors[0]) == secrets.bailian.embedding_dimensions


@pytest.mark.skipif(not should_run_integration(), reason="Set ELDA_RUN_INTEGRATION_TESTS=1")
@pytest.mark.skipif(not deepseek_configured(), reason="DeepSeek API key not in secrets/api_keys.yaml")
@pytest.mark.asyncio
async def test_deepseek_chat_completion(secrets):
    provider = DeepSeekProvider(
        secrets.deepseek.api_key,
        secrets.deepseek.reasoning_model,
        secrets.deepseek.base_url,
        thinking_enabled=secrets.deepseek.thinking_enabled,
        reasoning_effort=secrets.deepseek.reasoning_effort,
    )
    text = await provider.chat(
        [{"role": "user", "content": "Reply with exactly: ELDA_OK"}],
    )
    assert text
    assert len(text.strip()) > 0


@pytest.mark.skipif(not should_run_integration(), reason="Set ELDA_RUN_INTEGRATION_TESTS=1")
@pytest.mark.skipif(
    not (bailian_configured() and deepseek_configured()),
    reason="Both Bailian and DeepSeek keys required",
)
def test_get_providers_factory(secrets):
    payload = {"model_keys": {"bailian": secrets.bailian.api_key, "deepseek": secrets.deepseek.api_key}}
    coder, reasoner, bailian_reasoner = get_providers(payload)
    assert isinstance(coder, BailianProvider)
    assert isinstance(reasoner, DeepSeekProvider)
    assert isinstance(bailian_reasoner, BailianProvider)
    embedder = get_embedder(payload)
    assert isinstance(embedder, BailianEmbeddingProvider)
