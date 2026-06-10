import logging
import time
from typing import BinaryIO, Callable

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings

logger = logging.getLogger(__name__)


class S3Service:
    def __init__(self) -> None:
        # Explicit timeouts + retries so a stalled chunk fails fast instead of
        # hanging forever (e.g. expired session token mid multipart download).
        logger.info(
            "S3Service init: region=%s bucket=%s",
            settings.COGNITO["REGION"],
            settings.S3["BUCKET"],
        )
        self._client = boto3.client(
            "s3",
            region_name=settings.COGNITO["REGION"],
            config=Config(
                connect_timeout=10,
                read_timeout=60,
                retries={"max_attempts": 5, "mode": "standard"},
            ),
        )
        self._bucket = settings.S3["BUCKET"]

    @property
    def bucket(self) -> str:
        return self._bucket

    def upload_fileobj(self, key: str, fileobj: BinaryIO, content_type: str | None = None) -> None:
        logger.info("S3 upload start: bucket=%s key=%s content_type=%s", self._bucket, key, content_type)
        extra = {"ContentType": content_type} if content_type else {}
        t0 = time.monotonic()
        self._client.upload_fileobj(fileobj, self._bucket, key, ExtraArgs=extra)
        logger.info("S3 upload done: key=%s elapsed=%.2fs", key, time.monotonic() - t0)

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
        # Single-threaded, sequential ranged download. boto3's default
        # multi-threaded transfer (max_concurrency=10) deadlocks mid-file
        # behind Docker Desktop's WSL2 NAT; one connection at a time is robust
        # and, combined with the client's read_timeout, lets a real stall
        # fail-and-retry instead of wedging forever.
        self._client.download_file(
            self._bucket,
            key,
            dest_path,
            Callback=callback,
            Config=TransferConfig(use_threads=False),
        )
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
        ttl = ttl_seconds or settings.S3["PRESIGN_TTL_SECONDS"]
        logger.info("S3 presign: key=%s ttl=%ss", key, ttl)
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=ttl,
        )
