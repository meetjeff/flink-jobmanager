from setting import set_config
from flinkmanager import get_job_manager

def restart(jobid=None):
    storage_config, flink_config, _ = set_config()
    job_manager = get_job_manager(storage_config, flink_config)
    
    return job_manager.restart_job(jobid)

if __name__ == '__main__':
    job_info = restart()
    print(f"job_info: {job_info}")