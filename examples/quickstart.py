"""Run after installing the SDK and exporting the four SILO_* variables."""
from uuid import uuid4
from silo import Silo


def main():
    client = Silo.from_env()
    bucket = 'silo-python-example-' + uuid4().hex
    client.make_bucket(bucket)
    data = '你好，Silo！'.encode('utf-8')
    result = client.upload_bytes(bucket, 'hello.txt', data, 'text/plain; charset=utf-8')
    downloaded = client.download_bytes(bucket, 'hello.txt')
    if downloaded != data:
        raise RuntimeError('Downloaded content differs from uploaded content')
    print('Bucket:', bucket)
    print('ETag:', result.etag)
    print(downloaded.decode('utf-8'))
    print('Example bucket and object retained for inspection.')


if __name__ == '__main__':
    main()
