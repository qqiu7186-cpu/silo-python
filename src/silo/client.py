"""Silo convenience methods; all upstream MinIO methods remain inherited."""
import os
from io import BytesIO

from minio import Minio
from minio.helpers import ObjectWriteResult


class Silo(Minio):
    """Silo S3 client with the unchanged Minio constructor and public API."""

    @classmethod
    def from_env(cls) -> "Silo":
        """Read SILO_* credentials; HTTPS defaults on, booleans are true/false.

        SILO_ENDPOINT uses the upstream host:port format, without a URL scheme.
        Missing credentials or an invalid SILO_SECURE value raise ValueError.
        """
        values = {}
        for key in ("SILO_ENDPOINT", "SILO_ACCESS_KEY", "SILO_SECRET_KEY"):
            value = os.environ.get(key)
            if value is None or not value.strip():
                raise ValueError(f"{key} is required")
            values[key] = value
        secure = os.environ.get("SILO_SECURE", "true").strip().lower()
        if secure not in ("true", "false"):
            raise ValueError("SILO_SECURE must be 'true' or 'false'")
        return cls(
            values["SILO_ENDPOINT"].strip(),
            access_key=values["SILO_ACCESS_KEY"],
            secret_key=values["SILO_SECRET_KEY"],
            secure=secure == "true",
        )

    def upload_bytes(
        self,
        bucket_name: str,
        object_name: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> ObjectWriteResult:
        """Upload in-memory bytes and return the upstream ObjectWriteResult.

        For streams, metadata, encryption or large files, use inherited
        put_object/fput_object with their complete upstream options.
        """
        return self.put_object(
            bucket_name, object_name, BytesIO(data), len(data),
            content_type=content_type,
        )

    def download_bytes(self, bucket_name: str, object_name: str) -> bytes:
        """Read an object fully into memory, always releasing the connection.

        For large objects, ranges or version IDs, use inherited get_object
        or fget_object. S3/network errors propagate unchanged.
        """
        response = self.get_object(bucket_name, object_name)
        try:
            return response.read()
        finally:
            try:
                response.close()
            finally:
                response.release_conn()
