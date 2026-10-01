"""Catch insecure env defaults, invalid configuration and leaked responses."""
import io

import pytest
from minio.helpers import ObjectWriteResult
from silo import Silo


@pytest.fixture
def env(monkeypatch):
    for key in ('SILO_ENDPOINT', 'SILO_ACCESS_KEY', 'SILO_SECRET_KEY', 'SILO_SECURE'):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv('SILO_ENDPOINT', 'localhost:9000')
    monkeypatch.setenv('SILO_ACCESS_KEY', 'user')
    monkeypatch.setenv('SILO_SECRET_KEY', ' secret with spaces ')
    return monkeypatch


def test_from_env_defaults_to_https(env):
    client = Silo.from_env()
    assert client._base_url.is_https
    assert client._base_url.host == 'localhost:9000'
    creds = client._provider.retrieve()
    assert creds.access_key == 'user'
    assert creds.secret_key == ' secret with spaces '


@pytest.mark.parametrize('value,want', [('true', True), (' TRUE ', True),
                                        ('false', False), ('False', False)])
def test_env_secure(env, value, want):
    env.setenv('SILO_SECURE', value)
    assert Silo.from_env()._base_url.is_https is want


@pytest.mark.parametrize('key', ['SILO_ENDPOINT', 'SILO_ACCESS_KEY', 'SILO_SECRET_KEY'])
@pytest.mark.parametrize('value', [None, '', '   '])
def test_missing_env_fails_without_exposing_secret(env, key, value):
    if value is None:
        env.delenv(key)
    else:
        env.setenv(key, value)
    with pytest.raises(ValueError) as caught:
        Silo.from_env()
    assert key in str(caught.value)
    assert 'secret with spaces' not in str(caught.value)


@pytest.mark.parametrize('value', ['', 'typo', '0', '1'])
def test_env_invalid_secure(env, value):
    env.setenv('SILO_SECURE', value)
    with pytest.raises(ValueError, match='SILO_SECURE'):
        Silo.from_env()


@pytest.mark.parametrize('data', [b'', '中文'.encode(), b'\x00\xff'])
def test_upload_bytes_passes_stream_length_and_content_type(monkeypatch, data):
    result = ObjectWriteResult('bucket', 'folder/中文', None, 'etag', {})
    def transport(self, bucket_name, object_name, stream, length, content_type):
        assert (bucket_name, object_name) == ('bucket', 'folder/中文')
        assert length == len(data)
        assert stream.read() == data
        assert content_type == 'text/plain'
        return result
    monkeypatch.setattr(Silo, 'put_object', transport)
    assert Silo('localhost:9000').upload_bytes(
        'bucket', 'folder/中文', data, 'text/plain') is result


class Response:
    def __init__(self, read_error=False, close_error=False):
        self.buffer = io.BytesIO(b'\x00hello')
        self.closed = False
        self.read_error = read_error
        self.close_error = close_error
        self.released = False

    def read(self, *args):
        if self.read_error:
            raise OSError('read failed')
        return self.buffer.read(*args)

    def close(self):
        self.buffer.close()
        self.closed = True
        if self.close_error:
            self.close_error = False
            raise OSError('close failed')

    def release_conn(self):
        self.released = True


@pytest.mark.parametrize('read_error,close_error', [(False, False), (True, False), (False, True)])
def test_download_always_releases_response(monkeypatch, read_error, close_error):
    response = Response(read_error, close_error)
    def transport(self, bucket_name, object_name):
        assert (bucket_name, object_name) == ('bucket', 'object')
        return response
    monkeypatch.setattr(Silo, 'get_object', transport)
    client = Silo('localhost:9000')
    if read_error or close_error:
        with pytest.raises(OSError):
            client.download_bytes('bucket', 'object')
    else:
        assert client.download_bytes('bucket', 'object') == b'\x00hello'
    assert response.closed
    assert response.released
