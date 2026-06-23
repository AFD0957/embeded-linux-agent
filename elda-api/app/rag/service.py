"""RAG service — embed, index, search."""

from __future__ import annotations

import logging
import re
from typing import Any

from app.models.providers import get_embedder
from app.rag.milvus_store import milvus_store

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200


class RAGService:
    async def index_markdown(
        self,
        collection_key: str,
        doc_id: str,
        path: str,
        markdown: str,
        payload: dict[str, Any],
    ) -> int:
        chunks = chunk_text(markdown)
        embedder = get_embedder(payload)
        return await milvus_store.index_chunks(collection_key, doc_id, path, chunks, embedder)

    async def search(
        self,
        collection_key: str,
        query: str,
        payload: dict[str, Any],
        top_k: int = 8,
    ) -> list[dict[str, Any]]:
        embedder = get_embedder(payload)
        vectors = await embedder.embed([query])
        return milvus_store.search(collection_key, vectors[0], top_k=top_k)

    async def search_all(self, query: str, payload: dict[str, Any], top_k: int = 5) -> str:
        sections = []
        errors: list[str] = []
        for key, label in [
            ("kernel_drivers", "Kernel driver references"),
            ("dt_bindings", "Device tree bindings"),
            ("hardware_docs", "Datasheet / hardware docs"),
            ("vendor_drivers", "Vendor BSP driver references"),
        ]:
            try:
                hits = await self.search(key, query, payload, top_k=top_k)
            except Exception as exc:
                logger.warning("RAG search failed for %s: %s", key, exc)
                errors.append(f"{label}: {exc}")
                hits = []
            if hits:
                lines = [f"### {label}"]
                for h in hits:
                    lines.append(f"- [{h['path']}] (score={h['score']:.3f})\n{h['text'][:600]}")
                sections.append("\n".join(lines))
        if errors and not sections:
            return f"(RAG unavailable: {'; '.join(errors)})"
        if errors:
            sections.append("### RAG warnings\n" + "\n".join(f"- {e}" for e in errors))
        return "\n\n".join(sections) if sections else "(no RAG hits)"


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    if len(text) <= size:
        return [text] if text else []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return chunks


rag_service = RAGService()
