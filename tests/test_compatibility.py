"""Catch omitted upstream APIs, changed signatures and duplicated model types."""
import importlib
import inspect
import pkgutil

import minio
import pytest


def test_client_preserves_every_upstream_method():
    silo = importlib.import_module('silo')
    assert issubclass(silo.Silo, minio.Minio)
    assert inspect.signature(silo.Silo) == inspect.signature(minio.Minio)
    methods = [name for name in dir(minio.Minio)
               if not name.startswith('_') and callable(getattr(minio.Minio, name))]
    assert len(methods) >= 60
    for name in methods:
        actual = getattr(silo.Silo, name)
        expected = getattr(minio.Minio, name)
        assert actual is expected, name
        assert inspect.signature(actual) == inspect.signature(expected), name


MODULES = [item.name for item in pkgutil.walk_packages(minio.__path__, 'minio.')
           if not any(part.startswith('_') for part in item.name.split('.')[1:])]


@pytest.mark.parametrize('module_name', MODULES)
def test_all_public_auxiliary_symbols(module_name):
    upstream = importlib.import_module(module_name)
    compatible = importlib.import_module(module_name.replace('minio.', 'silo.', 1))
    for name in dir(upstream):
        if not name.startswith('_'):
            assert getattr(compatible, name) is getattr(upstream, name), name


def test_errors_preserve_identity():
    from silo import S3Error
    from minio.error import S3Error as UpstreamS3Error
    assert S3Error is UpstreamS3Error


def test_symbol_identity_after_all_submodule_imports():
    # Importing a child package must not replace exported upstream module objects.
    for name in MODULES:
        importlib.import_module(name.replace('minio.', 'silo.', 1))
    for name in MODULES:
        upstream = importlib.import_module(name)
        compatible = importlib.import_module(name.replace('minio.', 'silo.', 1))
        for symbol in dir(upstream):
            if not symbol.startswith('_'):
                assert getattr(compatible, symbol) is getattr(upstream, symbol), (name, symbol)


def test_no_upstream_implementation_is_overridden():
    from silo import Silo
    # Includes __init__ and private transport/signing/region-cache helpers.
    for name, function in minio.Minio.__dict__.items():
        if inspect.isfunction(function):
            assert inspect.getattr_static(Silo, name) is function, name


@pytest.mark.parametrize('options', [
    {},
    {'access_key': 'example', 'secret_key': 'example-secret', 'secure': False},
    {'access_key': 'example', 'secret_key': 'example-secret', 'session_token': 'token',
     'secure': True, 'region': 'eu-west-1', 'cert_check': False},
])
def test_constructor_state_and_credentials_match(options):
    from silo import Silo
    original = minio.Minio('localhost:9000', **options)
    compatible = Silo('localhost:9000', **options)
    assert original._base_url.host == compatible._base_url.host
    assert original._base_url.is_https == compatible._base_url.is_https
    assert original._base_url.region == compatible._base_url.region
    assert original._user_agent == compatible._user_agent
    assert original._region_map == compatible._region_map
    if original._provider:
        left = original._provider.retrieve()
        right = compatible._provider.retrieve()
        assert (left.access_key, left.secret_key, left.session_token) == (
            right.access_key, right.secret_key, right.session_token)
    else:
        assert compatible._provider is None


def test_constructor_accepts_upstream_provider_and_http_client():
    import urllib3
    from silo import Silo
    from silo.credentials import StaticProvider
    provider = StaticProvider('access', 'secret', 'session')
    transport = urllib3.PoolManager(timeout=2, retries=False)
    try:
        original = minio.Minio('localhost:9000', credentials=provider, http_client=transport,
                               secure=False, region='us-east-1')
        compatible = Silo('localhost:9000', credentials=provider, http_client=transport,
                          secure=False, region='us-east-1')
        assert original._provider is compatible._provider is provider
        assert original._http is compatible._http is transport
    finally:
        transport.clear()


def test_presigned_url_matches_upstream_byte_for_byte():
    from datetime import datetime, timedelta, timezone
    from silo import Silo
    config = dict(access_key='example', secret_key='example-secret', session_token='token',
                  secure=True, region='us-east-1')
    original = minio.Minio('localhost:9000', **config)
    compatible = Silo('localhost:9000', **config)
    options = dict(expires=timedelta(minutes=5),
                   request_date=datetime(2026, 10, 1, 12, tzinfo=timezone.utc),
                   response_headers={'response-content-type': 'text/plain'},
                   version_id='version')
    for method in ('GET', 'PUT', 'HEAD', 'DELETE'):
        assert compatible.get_presigned_url(method, 'example', 'folder/中文.txt', **options) == (
            original.get_presigned_url(method, 'example', 'folder/中文.txt', **options))
