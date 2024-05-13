from .storageclient import get_storage_client
from .jobmanager import FlinkJobManager

def get_job_manager(storage_config, flink_config):
    try:
        storage_client = get_storage_client(**storage_config)
        return FlinkJobManager(storage_client, **flink_config)
    except Exception as e:
        raise RuntimeError(f"Failed to get job manager, error: {e}")