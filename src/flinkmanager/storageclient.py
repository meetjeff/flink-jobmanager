from elasticsearch import Elasticsearch
from datetime import datetime

def get_storage_client(es_ip, es_port, es_user, es_password, es_index):
    try:
        es_client = Elasticsearch(
            [f"http://{es_ip}:{es_port}"], 
            http_auth=(es_user, es_password)
        )
        return EsIndexClient(es_client, es_index)
    except Exception as e:
        raise RuntimeError(f"Failed to get storage client, error: {e}")

class EsIndexClient:
    def __init__(self, es_client, es_index):
        self.es = es_client
        self.index = es_index

    def __get_latest_record(self):
        try:
            query = {
                "size": 1,
                "sort": [
                    {"id": {"order": "desc"}} 
                ]
            }
            response = self.es.search(index=self.index, body=query)
            return response.get('hits').get('hits')[0].get('_source')
        except Exception as e:
            raise RuntimeError(f"Failed to get latest record, error: {e}")
    
    def __next_id(self):
        try:
            return self.__get_latest_record()['id'] + 1
        except Exception:
            return 1
        
    def __query_job(self, jobid):
        try:
            query = {
                "size": 1,
                "query": {
                    "match": {"jobid": jobid}
                },
                "sort": [
                    {"id": {"order": "desc"}} 
                ]
            }
            response = self.es.search(index=self.index, body=query)
            return response.get('hits').get('hits')[0].get('_source')
        except Exception as e:
            raise RuntimeError(f"Failed to query job, error: {e}")
    
    def create_record(self, jarid, jobid, start_savepoint=None):
        try:
            id = self.__next_id()
            doc = {
                "id": id,
                "jarid": jarid, 
                "jobid": jobid,
                "start_timestamp": datetime.now(),
                "start_savepoint": start_savepoint
            }
            res = self.es.index(
                index=self.index, 
                id=id,
                document=doc, 
                op_type='create'
            )
            if res['result'] != 'created':
                raise RuntimeError(res)
        except Exception as e:
            raise RuntimeError(f"Failed to create record: {jobid}, error: {e}")
        
    def get_running_job(self):
        return self.__get_latest_record()['jobid']
    
    def update_record(self, jobid, stop_savepoint):
        try:
            doc = self.__query_job(jobid)
            if not doc:
                doc = {
                    "jobid": jobid,
                    "id": self.__next_id()
                }
            doc['stop_timestamp'] = datetime.now()
            doc['stop_savepoint'] = stop_savepoint
            res = self.es.index(
                index=self.index, 
                id=doc['id'],
                document=doc
            )
            if res['result'] != 'updated':
                raise RuntimeError(res)
        except Exception as e:
            raise RuntimeError(f"Failed to update record: {jobid}, error: {e}")