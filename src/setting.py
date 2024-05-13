import os
import json
import boto3
from botocore.exceptions import ClientError

def set_config():
    try:
        secret_name = os.getenv("SECRET_NAME")
        region = os.getenv("REGION")
        flink_manager_setting = get_secret(secret_name, region)

        storage_config = flink_manager_setting['storage_config']
        flink_config = flink_manager_setting['flink_config']
        logging_config = flink_manager_setting['logging_config']
        return(storage_config, flink_config, logging_config)
    except Exception as e:
        raise e

def get_secret(secret_name, region):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    try:
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            return json.loads(secret)
        else:
            binary_secret_data = get_secret_value_response['SecretBinary']
            return json.loads(binary_secret_data.decode('utf-8'))
    except Exception as e:
        raise e