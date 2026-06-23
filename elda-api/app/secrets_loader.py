"""Load API keys from secrets/api_keys.yaml (shared with elda CLI)."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class BailianSecrets(BaseModel):
    api_key: str = ""
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    code_model: str = "qwen3-coder-plus"
    reasoning_model: str = "qwen3-max"
    embedding_model: str = "text-embedding-v4"
    embedding_dimensions: int = 1024


class DeepSeekSecrets(BaseModel):
    api_key: str = ""
    base_url: str = "https://api.deepseek.com"
    reasoning_model: str = "deepseek-v4-pro"
    thinking_enabled: bool = True
    reasoning_effort: str = "high"


class ApiSecrets(BaseModel):
    bailian: BailianSecrets = Field(default_factory=BailianSecrets)
    deepseek: DeepSeekSecrets = Field(default_factory=DeepSeekSecrets)


def _find_secrets_file() -> Path | None:
    env_path = os.environ.get("ELDA_SECRETS_FILE")
    if env_path and Path(env_path).is_file():
        return Path(env_path)
    candidates = [Path("/app/secrets/api_keys.yaml"), Path.cwd() / "secrets" / "api_keys.yaml"]
    for parent in Path(__file__).resolve().parents:
        candidates.append(parent / "secrets" / "api_keys.yaml")
    seen: set[Path] = set()
    for c in candidates:
        c = c.resolve()
        if c in seen:
            continue
        seen.add(c)
        if c.is_file():
            return c
    return None


@lru_cache(maxsize=1)
def load_api_secrets() -> ApiSecrets:
    path = _find_secrets_file()
    if not path:
        return ApiSecrets()
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return ApiSecrets.model_validate(raw)


def merge_model_keys(payload: dict[str, Any]) -> dict[str, Any]:
    secrets = load_api_secrets()
    merged = dict(payload)
    keys = dict(merged.get("model_keys") or {})
    if not keys.get("bailian"):
        keys["bailian"] = secrets.bailian.api_key
    if not keys.get("deepseek"):
        keys["deepseek"] = secrets.deepseek.api_key
    merged["model_keys"] = keys
    merged.setdefault("code_model", secrets.bailian.code_model)
    merged.setdefault("bailian_reasoning_model", secrets.bailian.reasoning_model)
    merged.setdefault("reasoning_model", secrets.deepseek.reasoning_model)
    merged.setdefault("embedding_model", secrets.bailian.embedding_model)
    merged.setdefault("embedding_dimensions", secrets.bailian.embedding_dimensions)
    merged.setdefault("bailian_base_url", secrets.bailian.base_url)
    merged.setdefault("deepseek_base_url", secrets.deepseek.base_url)
    return merged
