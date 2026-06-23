"""Unit tests for secrets loading (no network)."""

from pathlib import Path

from app.secrets_loader import load_api_secrets, merge_model_keys


def test_merge_model_keys_defaults():
    payload = merge_model_keys({})
    assert "model_keys" in payload
    assert "code_model" in payload
    assert "embedding_model" in payload


def test_load_secrets_from_repo(monkeypatch):
    root = Path(__file__).resolve().parents[2]
    secrets_file = root / "secrets" / "api_keys.example.yaml"
    if not secrets_file.is_file():
        return
    monkeypatch.setenv("ELDA_SECRETS_FILE", str(secrets_file))
    load_api_secrets.cache_clear()
    secrets = load_api_secrets()
    assert secrets.bailian.base_url.startswith("https://")
    assert secrets.deepseek.base_url.startswith("https://")
