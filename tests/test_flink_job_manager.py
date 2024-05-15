import pytest
from unittest.mock import Mock, patch
from requests.exceptions import ConnectionError

from flinkmanager import FlinkJobManager

class TestFlinkJobManager:
    @pytest.fixture
    def storage_client(self):
        """Mock the storage client used in FlinkJobManager."""
        return Mock()

    @pytest.fixture
    def manager(self, storage_client):
        """Create a FlinkJobManager instance with mocked dependencies."""
        return FlinkJobManager(storage_client, 'localhost', '8081', 'jar_id', 'args')

    @patch('requests.post')
    def test_submit_job_success(self, mock_post, manager):
        """Test successful job submission."""
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = {'jobid': '1234'}
        mock_post.return_value = mock_response
        
        job_id = manager.submit_job()
        
        assert job_id == '1234'
        manager.storage.create_record.assert_called_once_with('jar_id', '1234', None)

    @patch('requests.post')
    def test_submit_job_failure(self, mock_post, manager):
        """Test job submission failure due to missing jobid."""
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response
        
        with pytest.raises(RuntimeError):
            manager.submit_job()

    @patch('requests.post')
    @patch('requests.get')
    def test_stop_job_success(self, mock_get, mock_post, manager, storage_client):
        """Test successful job stopping."""
        mock_stop_response = Mock(status_code=200)
        mock_stop_response.json.return_value = {'request-id': 'req123'}
        mock_post.return_value = mock_stop_response
        
        mock_status_response = Mock(status_code=200)
        mock_status_response.json.return_value = {
            'status': {'id': 'COMPLETED'},
            'operation': {'location': 'file:/path/to/savepoint'}
        }
        mock_get.return_value = mock_status_response
        
        storage_client.get_running_job.return_value = 'job123'
        
        savepoint = manager.stop_job()
        
        assert savepoint == '/path/to/savepoint'
        storage_client.update_record.assert_called_once_with('job123', '/path/to/savepoint')
    
    @patch('requests.post')
    def test_stop_job_no_jobid_found(self, mock_post, manager, storage_client):
        """Test stop job failure due to missing running job."""
        storage_client.get_running_job.return_value = None
        
        with pytest.raises(RuntimeError) as excinfo:
            manager.stop_job()
        
        assert "Failed to get jobid" in str(excinfo.value)
        mock_post.assert_not_called()

    def test_stop_job_http_request_fails(self, manager, storage_client):
        """Test HTTP request failure."""
        storage_client.get_running_job.return_value = 'job123'

        with patch('requests.post') as mock_post:
            mock_post.side_effect = ConnectionError("Failed to establish a new connection: [WinError 10061]")

            with pytest.raises(RuntimeError) as excinfo:
                manager.stop_job()
            
            assert "Failed to stop job, error: Failed to establish a new connection" in str(excinfo.value)
