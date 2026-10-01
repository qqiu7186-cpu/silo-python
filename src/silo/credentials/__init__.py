"""Compatibility exports from minio.credentials (minio 7.2.20)."""
from minio.credentials import (
    AWSConfigProvider as AWSConfigProvider,
    AssumeRoleProvider as AssumeRoleProvider,
    CertificateIdentityProvider as CertificateIdentityProvider,
    ChainedProvider as ChainedProvider,
    ClientGrantsProvider as ClientGrantsProvider,
    Credentials as Credentials,
    EnvAWSProvider as EnvAWSProvider,
    EnvMinioProvider as EnvMinioProvider,
    IamAwsProvider as IamAwsProvider,
    LdapIdentityProvider as LdapIdentityProvider,
    MinioClientConfigProvider as MinioClientConfigProvider,
    Provider as Provider,
    StaticProvider as StaticProvider,
    WebIdentityProvider as WebIdentityProvider,
    credentials as credentials,
    providers as providers,
)

__all__ = ['AWSConfigProvider', 'AssumeRoleProvider', 'CertificateIdentityProvider', 'ChainedProvider', 'ClientGrantsProvider', 'Credentials', 'EnvAWSProvider', 'EnvMinioProvider', 'IamAwsProvider', 'LdapIdentityProvider', 'MinioClientConfigProvider', 'Provider', 'StaticProvider', 'WebIdentityProvider', 'credentials', 'providers']

# Preserve upstream module identity even when consumers import child modules.
import sys as _sys
_sys.modules[__name__ + '.credentials'] = credentials
_sys.modules[__name__ + '.providers'] = providers
