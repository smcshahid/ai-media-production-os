"""MinIO/S3 client wrapper (T-05-01) implementing the ``BlobStore`` port.

The official ``minio`` SDK is synchronous, so blocking calls run in a worker
thread (``asyncio.to_thread``) to stay non-blocking on the event loop. All SDK
errors are translated to typed ``StorageError`` (or ``ObjectNotFoundError``) with
clear messages. ``upload_bytes`` verifies the object after writing: MinIO returns
the MD5 of the body as the ETag for a single-part PUT, so a mismatch means the
stored bytes differ from what we sent.
"""

from __future__ import annotations

import asyncio
import hashlib
import io
from dataclasses import dataclass

from aimpos_config import Settings
from minio import Minio
from minio.error import S3Error


class StorageError(Exception):
    """Object storage operation failed."""


class ObjectNotFoundError(StorageError):
    """Requested object key does not exist."""


@dataclass(frozen=True)
class ObjectStat:
    size: int
    etag: str
    content_type: str | None


class MinioClient:
    """Thin async wrapper over the MinIO SDK, scoped to one bucket."""

    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
    ) -> None:
        self._client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
        self._bucket = bucket

    @classmethod
    def from_settings(cls, settings: Settings) -> MinioClient:
        return cls(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            bucket=settings.minio_bucket,
            secure=settings.minio_secure,
        )

    async def upload_bytes(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        """Store ``data`` at ``key`` and return its ETag (verified against MD5)."""

        def _put() -> str:
            result = self._client.put_object(
                self._bucket,
                key,
                io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
            return str(result.etag)

        try:
            etag = (await asyncio.to_thread(_put)).strip('"')
        except S3Error as exc:
            raise StorageError(f"upload failed for {key!r}: {exc}") from exc

        # MD5 here is an integrity check against MinIO's single-PUT ETag, not security.
        expected = hashlib.md5(data).hexdigest()
        if etag != expected:
            raise StorageError(f"integrity check failed for {key!r}: etag {etag} != md5 {expected}")
        return etag

    async def download_bytes(self, key: str) -> bytes:
        """Return the bytes stored at ``key``."""

        def _get() -> bytes:
            response = self._client.get_object(self._bucket, key)
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()

        try:
            return await asyncio.to_thread(_get)
        except S3Error as exc:
            if exc.code in {"NoSuchKey", "NoSuchObject"}:
                raise ObjectNotFoundError(f"object not found: {key!r}") from exc
            raise StorageError(f"download failed for {key!r}: {exc}") from exc

    async def stat_object(self, key: str) -> ObjectStat:
        """Return size/etag/content-type for ``key`` (head-object)."""

        def _stat() -> ObjectStat:
            st = self._client.stat_object(self._bucket, key)
            return ObjectStat(
                size=st.size or 0,
                etag=(st.etag or "").strip('"'),
                content_type=st.content_type,
            )

        try:
            return await asyncio.to_thread(_stat)
        except S3Error as exc:
            if exc.code in {"NoSuchKey", "NoSuchObject"}:
                raise ObjectNotFoundError(f"object not found: {key!r}") from exc
            raise StorageError(f"stat failed for {key!r}: {exc}") from exc
