import logging
import time
from typing import BinaryIO, Callable

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


class S3Service:
    def __init__(self) -> None:
        # Explicit timeouts + retries so a stalled chunk fails fast instead of
        # hanging forever (e.g. expired session token mid multipart download).
        logger.info(
            "S3Service init: region=%s bucket=%s",
            settings.aws_region,
            settings.s3_bucket,
        )
        self._client = boto3.client(
            "s3",
            region_name=settings.aws_region,
            config=Config(
                connect_timeout=10,
                read_timeout=60,
                retries={"max_attempts": 5, "mode": "standard"},
            ),
        )
        self._bucket = settings.s3_bucket

    @property
    def bucket(self) -> str:
        return self._bucket

    def upload_fileobj(self, key: str, fileobj: BinaryIO, content_type: str | None = None) -> None:
        logger.info("S3 upload start: bucket=%s key=%s content_type=%s", self._bucket, key, content_type)
        extra = {"ContentType": content_type} if content_type else {}
        t0 = time.monotonic()
        self._client.upload_fileobj(fileobj, self._bucket, key, ExtraArgs=extra)
        logger.info("S3 upload done: key=%s elapsed=%.2fs", key, time.monotonic() - t0)

    def upload_bytes(self, key: str, data: bytes, content_type: str | None = None) -> None:
        logger.info(
            "S3 put_object start: bucket=%s key=%s bytes=%d content_type=%s",
            self._bucket, key, len(data), content_type,
        )
        kwargs = {"Bucket": self._bucket, "Key": key, "Body": data}
        if content_type:
            kwargs["ContentType"] = content_type
        t0 = time.monotonic()
        self._client.put_object(**kwargs)
        logger.info("S3 put_object done: key=%s elapsed=%.2fs", key, time.monotonic() - t0)

    def head_object(self, key: str) -> dict | None:
        """Return metadata for an object (ContentLength etc.) or None if it
        doesn't exist. Useful as a fast sanity check before a slow download."""
        try:
            meta = self._client.head_object(Bucket=self._bucket, Key=key)
            logger.info(
                "S3 head_object: key=%s size=%s content_type=%s",
                key,
                meta.get("ContentLength"),
                meta.get("ContentType"),
            )
            return meta
        except ClientError as exc:
            logger.warning("S3 head_object failed: key=%s error=%s", key, exc)
            return None

    def download_to_path(
        self,
        key: str,
        dest_path: str,
        callback: Callable[[int], None] | None = None,
    ) -> None:
        logger.info("S3 download start: bucket=%s key=%s dest=%s", self._bucket, key, dest_path)
        t0 = time.monotonic()
        self._client.download_file(self._bucket, key, dest_path, Callback=callback)
        logger.info(
            "S3 download done: key=%s dest=%s elapsed=%.2fs",
            key, dest_path, time.monotonic() - t0,
        )

    def delete(self, key: str) -> None:
        logger.info("S3 delete: bucket=%s key=%s", self._bucket, key)
        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)
        except ClientError as exc:
            logger.warning("S3 delete failed: key=%s error=%s", key, exc)

    def presign_get(self, key: str, ttl_seconds: int | None = None) -> str:
        ttl = ttl_seconds or settings.s3_presign_ttl_seconds
        logger.info("S3 presign: key=%s ttl=%ss", key, ttl)
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=ttl,
        )


def get_s3_service() -> S3Service:
    return S3Service()
