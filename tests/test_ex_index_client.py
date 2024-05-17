import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from flinkmanager.storageclient import EsIndexClient

@pytest.fixture
def es_client_mock():
    return MagicMock()

@pytest.fixture
def es_index_client(es_client_mock):
    return EsIndexClient(es_client=es_client_mock, es_index="test_index")

def test_get_latest_record_success(es_index_client, es_client_mock):
    es_client_mock.search.return_value = {
        "hits": {
            "hits": [
                {"_source": {"id": 10, "jobid": "job1"}}
            ]
        }
    }
    
    result = es_index_client._EsIndexClient__get_latest_record()
    assert result == {"id": 10, "jobid": "job1"}

def test_get_latest_record_failure(es_index_client, es_client_mock):
    es_client_mock.search.side_effect = Exception("Search failed")
    
    with pytest.raises(
        RuntimeError, 
        match="Failed to get latest record, error: Search failed"
    ):
        es_index_client._EsIndexClient__get_latest_record()

def test_next_id_existing_record(es_index_client, es_client_mock):
    es_client_mock.search.return_value = {
        "hits": {
            "hits": [
                {"_source": {"id": 10}}
            ]
        }
    }
    
    result = es_index_client._EsIndexClient__next_id()
    assert result == 11

def test_next_id_no_existing_record(es_index_client, es_client_mock):
    es_client_mock.search.side_effect = Exception("No records found")
    
    result = es_index_client._EsIndexClient__next_id()
    assert result == 1

def test_query_job_success(es_index_client, es_client_mock):
    es_client_mock.search.return_value = {
        "hits": {
            "hits": [
                {"_source": {"jobid": "job1", "id": 10}}
            ]
        }
    }
    
    result = es_index_client._EsIndexClient__query_job("job1")
    assert result == {"jobid": "job1", "id": 10}

def test_query_job_failure(es_index_client, es_client_mock):
    es_client_mock.search.side_effect = Exception("Search failed")
    
    with pytest.raises(
        RuntimeError, 
        match="Failed to query job, error: Search failed"
    ):
        es_index_client._EsIndexClient__query_job("job1")

@patch('flinkmanager.storageclient.datetime')
def test_create_record_success(mock_datetime, es_index_client, es_client_mock):
    mock_datetime.now.return_value = datetime(2024, 5, 17)
    es_client_mock.index.return_value = {"result": "created"}
    es_client_mock.search.return_value = {
        "hits": {
            "hits": [
                {"_source": {"id": 10, "jobid": "job1"}}
            ]
        }
    }

    es_index_client.create_record("jar1", "job1", "savepoint1")
    
    es_client_mock.index.assert_called_with(
        index="test_index",
        id=11,
        document={
            "id": 11,
            "jarid": "jar1",
            "jobid": "job1",
            "start_timestamp": datetime(2024, 5, 17),
            "start_savepoint": "savepoint1"
        },
        op_type='create'
    )

def test_create_record_failure(es_index_client, es_client_mock):
    es_client_mock.index.side_effect = Exception("Indexing failed")
    
    with pytest.raises(
        RuntimeError, 
        match="Failed to create record: job1, error: Indexing failed"
    ):
        es_index_client.create_record("jar1", "job1", "savepoint1")

def test_get_running_job(es_index_client, es_client_mock):
    es_client_mock.search.return_value = {
        "hits": {
            "hits": [
                {"_source": {"jobid": "job1"}}
            ]
        }
    }
    
    result = es_index_client.get_running_job()
    assert result == "job1"

@patch('flinkmanager.storageclient.datetime')
def test_update_record_success(mock_datetime, es_index_client, es_client_mock):
    mock_datetime.now.return_value = datetime(2024, 5, 17)
    es_client_mock.search.return_value = {
        "hits": {
            "hits": [
                {"_source": {"jobid": "job1", "id": 10}}
            ]
        }
    }
    es_client_mock.index.return_value = {"result": "updated"}

    es_index_client.update_record("job1", "savepoint1")

    es_client_mock.index.assert_called_with(
        index="test_index",
        id=10,
        document={
            "jobid": "job1",
            "id": 10,
            "stop_timestamp": datetime(2024, 5, 17),
            "stop_savepoint": "savepoint1"
        }
    )

def test_update_record_failure(es_index_client, es_client_mock):
    es_client_mock.search.side_effect = Exception("Search failed")
    
    with pytest.raises(
        RuntimeError, 
        match="Failed to update record: job1, error: Failed to query job, error: Search failed"
    ):
        es_index_client.update_record("job1", "savepoint1")
