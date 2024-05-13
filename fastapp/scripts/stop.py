from setting import set_config
from flinkmanager import get_job_manager

def stop(jobid=None):
    storage_config, flink_config, _ = set_config()
    job_manager = get_job_manager(storage_config, flink_config)

    return job_manager.stop_job(jobid)

if __name__ == '__main__':
    savepoint = stop()
    print(f"savepoints: {savepoint}")