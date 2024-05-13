import requests
import json
import time

class FlinkJobManager:
    def __init__(self, storage_client, flink_ip, flink_port, jar_id, program_args):
        self.storage = storage_client
        self.flink_ip = flink_ip
        self.flink_port = flink_port
        self.jar_id = jar_id
        self.program_args = program_args
        self.base_url = f"http://{self.flink_ip}:{self.flink_port}"

    def submit_job(self, savepoint=None):
        headers = {'Content-Type': 'application/json'}
        payload = {'programArgs': self.program_args}
        if savepoint:
            payload['savepointPath'] = savepoint
        try:
            response = requests.post(
                f"{self.base_url}/jars/{self.jar_id}/run", 
                headers=headers, 
                data=json.dumps(payload)
            )
            response_data = response.json()
            jobid = response_data.get('jobid')
            if jobid:
                self.storage.create_record(self.jar_id, jobid, savepoint)
                return jobid
            raise RuntimeError("Failed to get jobid")
        except Exception as e:
            raise RuntimeError(f"Failed to submit job, error: {e}")

    def stop_job(self, jobid=None):
        if not jobid:
            jobid = self.storage.get_running_job()
            if not jobid:
                raise RuntimeError("Failed to get jobid")
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(
                f"{self.base_url}/jobs/{jobid}/stop", 
                headers=headers
            )
            request_id = response.json().get('request-id')
            for _ in range(5):
                status_response = requests.get(
                    f"{self.base_url}/jobs/{jobid}/savepoints/{request_id}"
                )
                status_data = status_response.json()
                if status_data.get('status', {}).get('id') == 'COMPLETED':
                    operation = status_data.get('operation', {})
                    failure = operation.get('failure-cause', {}).get('stack-trace')
                    if failure:
                        raise RuntimeError(failure)
                    location = operation.get('location')
                    savepoint = location.split("file:")[-1]
                    self.storage.update_record(jobid, savepoint)
                    return savepoint
                time.sleep(5)
            raise RuntimeError(status_response)
        except Exception as e:
            raise RuntimeError(f"Failed to stop job, error: {e}")

    def restart_job(self, jobid=None):
        try:
            savepoint = self.stop_job(jobid)
            if not savepoint:
                raise RuntimeError("Failed to get savepoint")
            jobid = self.submit_job(savepoint=savepoint)
            if not jobid:
                raise RuntimeError("Failed to get jobid")
            return {'jobid': jobid, 'start-savepoint': savepoint}
        except Exception as e:
            raise RuntimeError(f"Failed to restart job, error: {e}")