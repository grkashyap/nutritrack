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
from src.ProcessUploadedFile import lambda_handler

@mock_aws
def test_stream_gzip_file_content_from_object_storage(monkeypatch):
    provider = 'aws'
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

    object_storage_adapter = get_object_storage(provider=provider, bucket_name=bucket_name)
    file_content = object_storage_adapter.stream_gzip_file_content_from_object_storage(file_name)
    assert isinstance(file_content, Generator)
    first = next(file_content)
    assert first == json_text

@mock_aws
def test_remove_file_from_object_storage(monkeypatch):
    provider = 'aws'
    bucket_name = 'test-bucket'
    file_name = 'test.txt'
    client = boto3.client('s3')
    client.create_bucket(Bucket=bucket_name)
    client.put_object(Bucket=bucket_name, Key=file_name, Body='Test file')
    response = client.get_object(Bucket=bucket_name, Key=file_name)
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200

    object_storage_adapter = get_object_storage(provider=provider, bucket_name=bucket_name)
    object_storage_adapter.remove_file_from_object_storage(file_name)

    try:
        client.get_object(Bucket=bucket_name, Key=file_name)
        pytest.fail('This should fail')
    except ClientError:
        pass

@mock_aws
def test_process_file_from_event(monkeypatch):
    monkeypatch.setenv('CLOUD_PROVIDER','aws')

    # create aws dynamo db table
    table_name = 'nutri_fact'
    client = boto3.resource('dynamodb', region_name='us-east-1')
    client.create_table(TableName=table_name,
                                KeySchema=[{'AttributeName': '_id', 'KeyType': 'HASH'},{'AttributeName': 'nutriscore_tags', 'KeyType': 'HASH'}],
                                AttributeDefinitions=[{'AttributeName': '_id', 'AttributeType': 'S'}, {'AttributeName': 'nutriscore_tags', 'AttributeType': 'S'}],
                                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5})

    # create s3 bucket
    bucket_name = 'test-bucket'
    file_name = 'test.json.gz'
    json_text = {
            '_id': '5350804020038',
            'nutriscore_tags': 'not-applicable'
            }
    json_string = json.dumps(json_text)
    compressed_stream = io.BytesIO()

    with gzip.open(file_name, 'wt', encoding='utf-8') as gz_file:
        json.dump(json_text, gz_file)

    client = boto3.client('s3')
    client.create_bucket(Bucket=bucket_name)
    client.upload_file(file_name, bucket_name, file_name)
    response = client.get_object(Bucket=bucket_name, Key=file_name)
    assert is_not(response, None)

    # simulate the event
    event = {
        'Records':[
            {
                's3': {
                    'bucket':{
                        'name': bucket_name
                    },
                    'object': {
                        'key': file_name
                    }
                }
            }
        ]
    }

    response = lambda_handler(event, None)
    assert response['statusCode'] == 200

if __name__ == 'main':
    pytest.main()
