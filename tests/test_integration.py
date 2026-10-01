"""Live Silo acceptance tests; only random SDK-owned buckets are modified."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from io import BytesIO
import json
import uuid

import pytest
import urllib3
from silo import Silo, S3Error
from silo.commonconfig import CopySource, ComposeSource, ENABLED, Filter
from silo.deleteobjects import DeleteObject
from silo.lifecycleconfig import LifecycleConfig, Rule, Expiration
from silo.notificationconfig import NotificationConfig
from silo.tagging import Tags
from silo.versioningconfig import VersioningConfig

pytestmark = pytest.mark.integration


@pytest.fixture
def client():
    return Silo.from_env()


@pytest.fixture
def bucket(client):
    name = 'silo-sdk-test-' + uuid.uuid4().hex
    client.make_bucket(name)
    try:
        yield name
    finally:
        errors = list(client.remove_objects(name, (
            DeleteObject(obj.object_name, obj.version_id)
            for obj in client.list_objects(name, recursive=True, include_version=True)
        )))
        assert not errors, errors
        client.remove_bucket(name)


def read(client, bucket, key, **kwargs):
    response = client.get_object(bucket, key, **kwargs)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def test_bucket_and_bytes(client, bucket):
    assert client.bucket_exists(bucket)
    assert bucket in [item.name for item in client.list_buckets()]
    for key, data in [('空文件', b''), ('folder/中文.txt', '你好 Silo'.encode())]:
        result = client.upload_bytes(bucket, key, data)
        assert result.etag
        assert client.download_bytes(bucket, key) == data
    assert {item.object_name for item in client.list_objects(bucket, recursive=True)} == {
        '空文件', 'folder/中文.txt'}


def test_file_metadata_copy_range_and_compose(client, bucket, tmp_path):
    source = tmp_path / 'source.bin'
    source.write_bytes(b'0123456789')
    client.fput_object(bucket, 'original', str(source), content_type='text/plain',
                       metadata={'test-owner': 'sdk'})
    stat = client.stat_object(bucket, 'original')
    assert stat.size == 10
    assert stat.content_type == 'text/plain'
    assert stat.metadata['x-amz-meta-test-owner'] == 'sdk'
    target = tmp_path / 'download.bin'
    client.fget_object(bucket, 'original', str(target))
    assert target.read_bytes() == b'0123456789'
    client.copy_object(bucket, 'copy', CopySource(bucket, 'original'))
    assert client.download_bytes(bucket, 'copy') == b'0123456789'
    assert read(client, bucket, 'original', offset=2, length=4) == b'2345'
    client.compose_object(bucket, 'composed', [ComposeSource(bucket, 'original')])
    assert client.download_bytes(bucket, 'composed') == b'0123456789'


def test_multipart_upload(client, bucket):
    data = b'0123456789abcdef' * (7 * 1024 * 1024 // 16)
    result = client.put_object(bucket, 'multipart', BytesIO(data), len(data),
                               part_size=5 * 1024 * 1024)
    assert '-' in result.etag
    assert client.download_bytes(bucket, 'multipart') == data


def test_presigned_get_and_put(client, bucket):
    http = urllib3.PoolManager()
    try:
        url = client.presigned_put_object(bucket, 'signed', expires=timedelta(minutes=5))
        response = http.request('PUT', url, body=b'signed payload', timeout=10)
        assert response.status == 200, response.data
        url = client.presigned_get_object(bucket, 'signed', expires=timedelta(minutes=5))
        response = http.request('GET', url, timeout=10)
        assert response.status == 200
        assert response.data == b'signed payload'
    finally:
        http.clear()


def test_versioning_and_specific_version(client, bucket):
    client.set_bucket_versioning(bucket, VersioningConfig(ENABLED))
    assert client.get_bucket_versioning(bucket).status == ENABLED
    first = client.upload_bytes(bucket, 'versioned', b'v1')
    second = client.upload_bytes(bucket, 'versioned', b'v2')
    assert first.version_id and first.version_id != second.version_id
    assert read(client, bucket, 'versioned', version_id=first.version_id) == b'v1'
    assert client.download_bytes(bucket, 'versioned') == b'v2'
    client.remove_object(bucket, 'versioned')
    versions = list(client.list_objects(bucket, recursive=True, include_version=True))
    assert len(versions) == 3
    assert any(obj.is_delete_marker for obj in versions)


def test_lifecycle_policy_tags_and_notification(client, bucket):
    config = LifecycleConfig([Rule(ENABLED, Filter(prefix='temp/'),
                                  rule_id='expire-temp', expiration=Expiration(days=7))])
    client.set_bucket_lifecycle(bucket, config)
    assert client.get_bucket_lifecycle(bucket).rules[0].expiration.days == 7
    client.delete_bucket_lifecycle(bucket)
    assert client.get_bucket_lifecycle(bucket) is None
    policy = json.dumps({'Version': '2012-10-17', 'Statement': [{
        'Effect': 'Allow', 'Principal': {'AWS': ['*']}, 'Action': ['s3:GetObject'],
        'Resource': ['arn:aws:s3:::' + bucket + '/public/*']}]})
    client.set_bucket_policy(bucket, policy)
    assert json.loads(client.get_bucket_policy(bucket)) == json.loads(policy)
    client.delete_bucket_policy(bucket)
    tags = Tags.new_bucket_tags()
    tags['project'] = 'silo-sdk'
    client.set_bucket_tags(bucket, tags)
    assert client.get_bucket_tags(bucket)['project'] == 'silo-sdk'
    client.delete_bucket_tags(bucket)
    client.upload_bytes(bucket, 'tagged', b'tags')
    object_tags = Tags.new_object_tags()
    object_tags['kind'] = 'example'
    client.set_object_tags(bucket, 'tagged', object_tags)
    assert client.get_object_tags(bucket, 'tagged')['kind'] == 'example'
    client.delete_object_tags(bucket, 'tagged')
    assert not client.get_object_tags(bucket, 'tagged')
    client.set_bucket_notification(bucket, NotificationConfig())
    assert not client.get_bucket_notification(bucket).queue_config_list
    client.delete_bucket_notification(bucket)


def test_real_pagination_over_1000_objects(client, bucket):
    # More than S3's 1000-object page: missing the next-page request fails this test.
    keys = ['pages/' + str(index).zfill(4) for index in range(1005)]
    with ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(lambda key: client.upload_bytes(bucket, key, b''), keys))
    objects = list(client.list_objects(bucket, prefix='pages/', recursive=True))
    assert [obj.object_name for obj in objects] == keys
    assert len(list(client.list_objects(bucket, prefix='pages/', start_after='pages/0999'))) == 5


def test_error_types_and_codes(client, bucket):
    with pytest.raises(S3Error) as caught:
        client.download_bytes(bucket, 'missing')
    assert caught.value.code == 'NoSuchKey'
    invalid = Silo(client._base_url.host, access_key='nonexistent-sdk-user',
                   secret_key='invalid-sdk-secret', secure=client._base_url.is_https)
    with pytest.raises(S3Error) as caught:
        invalid.list_buckets()
    assert caught.value.code == 'InvalidAccessKeyId'


def test_original_minio_and_silo_live_results_match(client, bucket):
    from minio import Minio
    creds = client._provider.retrieve()
    original = Minio(client._base_url.host, access_key=creds.access_key,
                     secret_key=creds.secret_key, secure=client._base_url.is_https)
    payload = b'original-and-silo-parity'
    for implementation, key in [(original, 'upstream'), (client, 'silo')]:
        result = implementation.put_object(bucket, key, BytesIO(payload), len(payload),
                                            content_type='text/plain', metadata={'owner': 'parity'})
        assert result.etag
        assert read(implementation, bucket, key) == payload
    upstream_stat = original.stat_object(bucket, 'upstream')
    silo_stat = client.stat_object(bucket, 'silo')
    assert (upstream_stat.size, upstream_stat.etag, upstream_stat.content_type) == (
        silo_stat.size, silo_stat.etag, silo_stat.content_type)
    assert upstream_stat.metadata['x-amz-meta-owner'] == silo_stat.metadata['x-amz-meta-owner']
    for implementation in (original, client):
        assert [obj.object_name for obj in implementation.list_objects(bucket)] == ['silo', 'upstream']
        with pytest.raises(S3Error) as caught:
            implementation.get_object(bucket, 'missing')
        assert caught.value.code == 'NoSuchKey'
