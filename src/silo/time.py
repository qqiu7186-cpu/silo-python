"""Compatibility exports from minio.time (minio 7.2.20)."""
from minio.time import (
    Optional as Optional,
    absolute_import as absolute_import,
    annotations as annotations,
    ctime as ctime,
    datetime as datetime,
    from_http_header as from_http_header,
    from_iso8601utc as from_iso8601utc,
    timezone as timezone,
    to_amz_date as to_amz_date,
    to_float as to_float,
    to_http_header as to_http_header,
    to_iso8601utc as to_iso8601utc,
    to_signer_date as to_signer_date,
    utcnow as utcnow,
)

__all__ = ['Optional', 'absolute_import', 'annotations', 'ctime', 'datetime', 'from_http_header', 'from_iso8601utc', 'timezone', 'to_amz_date', 'to_float', 'to_http_header', 'to_iso8601utc', 'to_signer_date', 'utcnow']

# datetime.UTC only exists on newer Python versions; mirror upstream exactly.
import minio.time as _upstream_time
if hasattr(_upstream_time, "UTC"):
    UTC = _upstream_time.UTC
    __all__.append("UTC")
