"""Compatibility exports from minio.credentials.credentials (minio 7.2.20)."""
from minio.credentials.credentials import (
    Credentials as Credentials,
    Optional as Optional,
    annotations as annotations,
    dataclass as dataclass,
    datetime as datetime,
    timedelta as timedelta,
    timezone as timezone,
)

__all__ = ['Credentials', 'Optional', 'annotations', 'dataclass', 'datetime', 'timedelta', 'timezone']
