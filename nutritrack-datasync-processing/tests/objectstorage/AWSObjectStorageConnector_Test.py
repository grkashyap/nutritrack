import gzip
import io
import json
from collections.abc import Generator
from operator import is_not
import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from src.objectstorage.GetObjectStorage import get_object_storage

@mock_aws
def test_stream_gzip_file_content_from_object_storage(monkeypatch):
    monkeypatch.setenv('CLOUD_PROVIDER','aws')
    bucket_name = 'test-bucket'
    file_name = 'test.json.gz'
    json_text = [{'key1':'test1'},{'key2':'test2'}]
    json_string = json.dumps(json_text)
    compressed_stream = io.BytesIO()
    with gzip.GzipFile(mode='wb', fileobj=compressed_stream) as gz:
        gz.write(json_string.encode('utf-8'))
    compressed_data = compressed_stream.getvalue()
    with open('test_data.json.gz', 'wb') as f:
        f.write(compressed_data)

    client = boto3.client('s3')
    client.create_bucket(Bucket=bucket_name)
    client.upload_fileobj(io.BytesIO(compressed_data), bucket_name, file_name)
    response = client.get_object(Bucket=bucket_name, Key=file_name)
    assert is_not(response, None)

    object_storage_adapter = get_object_storage(bucket_name)
    file_content = object_storage_adapter.stream_gzip_file_content_from_object_storage(file_name)
    assert isinstance(file_content, Generator)
    first = next(file_content)
    assert first == json_text

@mock_aws
def test_remove_file_from_object_storage(monkeypatch):
    monkeypatch.setenv('CLOUD_PROVIDER', 'aws')
    bucket_name = 'test-bucket'
    file_name = 'test.txt'
    client = boto3.client('s3')
    client.create_bucket(Bucket=bucket_name)
    client.put_object(Bucket=bucket_name, Key=file_name, Body='Test file')
    response = client.get_object(Bucket=bucket_name, Key=file_name)
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200

    object_storage_adapter = get_object_storage(bucket_name)
    object_storage_adapter.remove_file_from_object_storage(file_name)

    try:
        client.get_object(Bucket=bucket_name, Key=file_name)
        pytest.fail('This should fail')
    except ClientError:
        pass

if __name__ == 'main':
    pytest.main()