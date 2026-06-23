"""ChatAgent — read-only Q&A."""

from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.rag.service import rag_service


class ChatAgent(BaseAgent):
    async def reply(
        self,
        project_id: str,
        message: str,
        history: list[dict[str, str]],
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = payload or {}
        self.bind(payload)
        rag = await rag_service.search_all(message, payload, top_k=6)
        hw = payload.get("hardware_context", "")

        sys = (
            f"ELDA read-only assistant for '{project_id}'. "
            "Answer using RAG and hardware facts. Do NOT propose file changes or patches."
        )
        messages = [
            {"role": "system", "content": sys},
            {"role": "system", "content": f"RAG:\n{rag}\n\nHardware:\n{hw[:6000]}"},
            *history,
            {"role": "user", "content": message},
        ]
        text = await self.reasoner.chat(messages)
        return {"reply": text}
