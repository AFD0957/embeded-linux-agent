"""LLM & embedding providers — Bailian + DeepSeek V4."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.secrets_loader import load_api_secrets, merge_model_keys

BAILIAN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"


class ProviderError(RuntimeError):
    pass


class ModelProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        response_format: dict[str, Any] | None = None,
    ) -> str:
        pass

    async def chat_json(self, messages: list[dict[str, str]], schema_hint: str = "") -> dict[str, Any]:
        sys = {
            "role": "system",
            "content": (
                "Respond with a single valid JSON object only, no markdown fences. "
                f"{schema_hint}"
            ),
        }
        text = await self.chat([sys, *messages], response_format={"type": "json_object"})
        return _parse_json(text)


class BailianProvider(ModelProvider):
    def __init__(
        self,
        api_key: str,
        model: str = "qwen3-coder-plus",
        base_url: str = BAILIAN_BASE_URL,
    ) -> None:
        if not api_key:
            raise ProviderError("Bailian API key missing — configure secrets/api_keys.yaml")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def chat(
        self,
        messages: list[dict[str, str]],
        response_format: dict[str, Any] | None = None,
    ) -> str:
        body: dict[str, Any] = {"model": self.model, "messages": messages}
        if response_format:
            body["response_format"] = response_format
        return await _post_chat(self.base_url, self.api_key, body)


class DeepSeekProvider(ModelProvider):
    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-v4-pro",
        base_url: str = DEEPSEEK_BASE_URL,
        thinking_enabled: bool = True,
        reasoning_effort: str = "high",
    ) -> None:
        if not api_key:
            raise ProviderError("DeepSeek API key missing — configure secrets/api_keys.yaml")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.thinking_enabled = thinking_enabled
        self.reasoning_effort = reasoning_effort

    async def chat(
        self,
        messages: list[dict[str, str]],
        response_format: dict[str, Any] | None = None,
    ) -> str:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "reasoning_effort": self.reasoning_effort,
        }
        if self.thinking_enabled:
            body["thinking"] = {"type": "enabled"}
        if response_format:
            body["response_format"] = response_format
        return await _post_chat(self.base_url, self.api_key, body)


class BailianEmbeddingProvider:
    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-v4",
        dimensions: int = 1024,
        base_url: str = BAILIAN_BASE_URL,
    ) -> None:
        if not api_key:
            raise ProviderError("Bailian API key required for embeddings")
        self.api_key = api_key
        self.model = model
        self.dimensions = dimensions
        self.base_url = base_url.rstrip("/")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        body = {
            "model": self.model,
            "input": texts,
            "dimensions": self.dimensions,
            "encoding_format": "float",
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                f"{self.base_url}/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=body,
            )
            if r.status_code >= 400:
                raise ProviderError(f"Bailian embedding error {r.status_code}: {r.text[:500]}")
            data = r.json()["data"]
            return [item["embedding"] for item in sorted(data, key=lambda x: x["index"])]


def get_providers(payload: dict[str, Any]) -> tuple[BailianProvider, DeepSeekProvider, BailianProvider]:
    """Returns (coder, deepseek_reasoner, bailian_reasoner)."""
    payload = merge_model_keys(payload)
    keys = payload.get("model_keys", {})
    secrets = load_api_secrets()
    coder = BailianProvider(
        keys.get("bailian", ""),
        payload.get("code_model", secrets.bailian.code_model),
        payload.get("bailian_base_url", BAILIAN_BASE_URL),
    )
    reasoner = DeepSeekProvider(
        keys.get("deepseek", ""),
        payload.get("reasoning_model", secrets.deepseek.reasoning_model),
        payload.get("deepseek_base_url", DEEPSEEK_BASE_URL),
        thinking_enabled=secrets.deepseek.thinking_enabled,
        reasoning_effort=secrets.deepseek.reasoning_effort,
    )
    bailian_reasoner = BailianProvider(
        keys.get("bailian", ""),
        payload.get("bailian_reasoning_model", secrets.bailian.reasoning_model),
        payload.get("bailian_base_url", BAILIAN_BASE_URL),
    )
    return coder, reasoner, bailian_reasoner


def get_embedder(payload: dict[str, Any]) -> BailianEmbeddingProvider:
    payload = merge_model_keys(payload)
    keys = payload.get("model_keys", {})
    secrets = load_api_secrets()
    return BailianEmbeddingProvider(
        keys.get("bailian", ""),
        payload.get("embedding_model", secrets.bailian.embedding_model),
        payload.get("embedding_dimensions", secrets.bailian.embedding_dimensions),
        payload.get("bailian_base_url", BAILIAN_BASE_URL),
    )


async def _post_chat(base_url: str, api_key: str, body: dict[str, Any]) -> str:
    async with httpx.AsyncClient(timeout=300.0) as client:
        r = await client.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json=body,
        )
        if r.status_code >= 400:
            raise ProviderError(f"LLM API error {r.status_code}: {r.text[:800]}")
        data = r.json()
        msg = data["choices"][0]["message"]
        return msg.get("content") or msg.get("reasoning_content") or ""


def _parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)
