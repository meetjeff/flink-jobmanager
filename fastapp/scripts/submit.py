from setting import set_config
from flinkmanager import get_job_manager

def submit(savepoint=None):
    storage_config, flink_config, _ = set_config()
    job_manager = get_job_manager(storage_config, flink_config)

    return job_manager.submit_job(savepoint)

if __name__ == '__main__':
    jobid = submit()
    print(f"jobid: {jobid}")