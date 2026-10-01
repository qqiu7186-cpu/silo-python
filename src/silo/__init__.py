"""Unofficial Silo Python SDK, powered by minio 7.2.20."""
from minio import Minio
from minio.error import S3Error

from .client import Silo

__version__ = "0.1.0"
__all__ = ["Silo", "Minio", "S3Error", "__version__"]
