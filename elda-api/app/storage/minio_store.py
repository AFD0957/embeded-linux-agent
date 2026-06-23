"""MinIO object storage for PDFs, logs, reports, patches."""

from __future__ import annotations

import io
import logging
from pathlib import Path

from minio import Minio
from minio.error import S3Error

from app.config import settings

logger = logging.getLogger(__name__)
_client: Minio | None = None


def get_minio() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        _ensure_bucket()
    return _client


def _ensure_bucket() -> None:
    client = _client
    if not client:
        return
    try:
        if not client.bucket_exists(settings.minio_bucket):
            client.make_bucket(settings.minio_bucket)
            logger.info("Created MinIO bucket %s", settings.minio_bucket)
    except S3Error as exc:
        logger.error("MinIO bucket setup failed: %s", exc)
        raise


def upload_bytes(object_name: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    client = get_minio()
    client.put_object(
        settings.minio_bucket,
        object_name,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return f"{settings.minio_bucket}/{object_name}"


def upload_file(object_name: str, path: Path, content_type: str = "application/octet-stream") -> str:
    return upload_bytes(object_name, path.read_bytes(), content_type)


def download_bytes(object_name: str) -> bytes:
    client = get_minio()
    resp = client.get_object(settings.minio_bucket, object_name)
    try:
        return resp.read()
    finally:
        resp.close()
        resp.release_conn()
