"""Base agent — bind LLM providers per request."""

from __future__ import annotations

from typing import Any

from app.models.providers import BailianProvider, DeepSeekProvider, get_providers


class BaseAgent:
    def bind(
        self, payload: dict[str, Any]
    ) -> tuple[BailianProvider, DeepSeekProvider, BailianProvider]:
        self.coder, self.reasoner, self.bailian_reasoner = get_providers(payload)
        return self.coder, self.reasoner, self.bailian_reasoner
