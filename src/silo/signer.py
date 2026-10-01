"""Compatibility exports from minio.signer (minio 7.2.20)."""
from minio.signer import (
    Credentials as Credentials,
    DictType as DictType,
    Mapping as Mapping,
    OrderedDict as OrderedDict,
    SIGN_V4_ALGORITHM as SIGN_V4_ALGORITHM,
    SplitResult as SplitResult,
    absolute_import as absolute_import,
    annotations as annotations,
    cast as cast,
    datetime as datetime,
    get_credential_string as get_credential_string,
    hashlib as hashlib,
    hmac as hmac,
    post_presign_v4 as post_presign_v4,
    presign_v4 as presign_v4,
    queryencode as queryencode,
    re as re,
    sha256_hash as sha256_hash,
    sign_v4_s3 as sign_v4_s3,
    sign_v4_sts as sign_v4_sts,
    time as time,
)

__all__ = ['Credentials', 'DictType', 'Mapping', 'OrderedDict', 'SIGN_V4_ALGORITHM', 'SplitResult', 'absolute_import', 'annotations', 'cast', 'datetime', 'get_credential_string', 'hashlib', 'hmac', 'post_presign_v4', 'presign_v4', 'queryencode', 're', 'sha256_hash', 'sign_v4_s3', 'sign_v4_sts', 'time']
