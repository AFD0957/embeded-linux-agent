"""Milvus client for local kernel indexing."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

from elda.config import EldaConfig
from elda.rag.embeddings import EmbeddingClient

DIM = 1024
COLLECTIONS = {
    "kernel_drivers": "elda_kernel_drivers",
    "dt_bindings": "elda_dt_bindings",
    "hardware_docs": "elda_hardware_docs",
    "vendor_drivers": "elda_vendor_drivers",
}

CODE_EXT = {".c", ".h", ".dts", ".dtsi", ".txt", ".md", ".yaml", ".yml"}


def chunk_text(text: str, size: int = 1200, overlap: int = 200) -> list[str]:
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


class MilvusIndexer:
    def __init__(self, cfg: EldaConfig) -> None:
        self.cfg = cfg
        self.embedder = EmbeddingClient(
            cfg.model.bailian_api_key,
            cfg.model.embedding_model,
        )
        connections.connect(
            alias="default",
            host=cfg.milvus.host,
            port=str(cfg.milvus.port),
        )

    def _ensure_collection(self, name: str) -> Collection:
        if utility.has_collection(name):
            col = Collection(name)
            col.load()
            return col
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="path", dtype=DataType.VARCHAR, max_length=1024),
            FieldSchema(name="chunk_index", dtype=DataType.INT64),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=8192),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=DIM),
        ]
        schema = CollectionSchema(fields, description=f"ELDA {name}")
        col = Collection(name, schema)
        col.create_index(
            "embedding",
            {"index_type": "IVF_FLAT", "metric_type": "COSINE", "params": {"nlist": 128}},
        )
        col.load()
        return col

    def index_paths(
        self,
        collection_key: str,
        root: Path,
        rel_paths: list[str],
    ) -> dict[str, Any]:
        name = COLLECTIONS[collection_key]
        col = self._ensure_collection(name)
        total_chunks = 0
        files_indexed = 0

        for rel in rel_paths:
            base = root / rel
            if base.is_file():
                files = [base]
            elif base.is_dir():
                files = [p for p in base.rglob("*") if p.suffix in CODE_EXT and p.is_file()]
            else:
                continue
            for fpath in files:
                try:
                    text = fpath.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                if len(text.strip()) < 20:
                    continue
                chunks = chunk_text(text)
                if not chunks:
                    continue
                rel_path = str(fpath.relative_to(root))
                vectors = self.embedder.embed_sync(chunks)
                ids, doc_ids, paths, indices, texts = [], [], [], [], []
                for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
                    cid = hashlib.sha256(f"{rel_path}:{i}".encode()).hexdigest()[:32]
                    ids.append(cid)
                    doc_ids.append(rel_path[:500])
                    paths.append(rel_path[:1000])
                    indices.append(i)
                    texts.append(chunk[:8000])
                col.insert([ids, doc_ids, paths, indices, texts, vectors])
                total_chunks += len(chunks)
                files_indexed += 1
        col.flush()
        return {
            "collection": name,
            "files_indexed": files_indexed,
            "chunks_indexed": total_chunks,
        }

    def search(self, collection_key: str, query: str, top_k: int = 8) -> list[dict[str, Any]]:
        name = COLLECTIONS[collection_key]
        col = self._ensure_collection(name)
        vec = self.embedder.embed_sync([query])[0]
        results = col.search(
            data=[vec],
            anns_field="embedding",
            param={"metric_type": "COSINE", "params": {"nprobe": 16}},
            limit=top_k,
            output_fields=["doc_id", "path", "chunk_index", "text"],
        )
        hits: list[dict[str, Any]] = []
        for hit in results[0]:
            hits.append(
                {
                    "score": hit.score,
                    "path": hit.entity.get("path"),
                    "text": hit.entity.get("text"),
                }
            )
        return hits
