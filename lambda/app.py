import json
from logging2slack import SlackLogger

from setting import set_config
from flinkmanager import get_job_manager

def flink_job_action(event, context):
    storage_config, flink_config, logging_config = set_config()
    logger = SlackLogger(**logging_config)

    try:
        body = event.get('body')
        request_info = {
            "httpMethod": event.get("httpMethod"),
            "Host": event.get("headers").get("Host"),
            "User-Agent": event.get("headers").get("User-Agent"),
            "X-Forwarded-For": event.get("headers").get("X-Forwarded-For"),
            "X-Forwarded-Port": event.get("headers").get("X-Forwarded-Port"),
            "X-Forwarded-Proto": event.get("headers").get("X-Forwarded-Proto"),
            "CloudFront-Viewer-Country": event.get("multiValueHeaders").get("CloudFront-Viewer-Country")[0],
            "queryStringParameters": event.get("queryStringParameters"),
            "multiValueQueryStringParameters": event.get("multiValueQueryStringParameters"),
            "requestTime": event.get("requestContext").get("requestTime"),
            "path": event.get("requestContext").get("path"),
            "accountId": event.get("requestContext").get("accountId"),
            "body": body
        }
        logger.info(request_info)

        job_manager = get_job_manager(storage_config, flink_config)

        if body:
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = {}
        else:
            data = {}

        action = event.get('pathParameters').get('action').lower()
        match action:
            case "submit":
                savepoint = data.get('savepoint')
                jobid = job_manager.submit_job(savepoint)
                res_info = json.dumps({
                    "action": action,
                    "jobid": jobid,
                    "savepoint": savepoint
                })

            case "stop":
                jobid = data.get('jobid')
                savepoint = job_manager.stop_job(jobid)
                res_info = json.dumps({
                    "action": action,
                    "jobid": jobid,
                    "savepoint": savepoint
                })

            case "restart":
                jobid = data.get('jobid')
                job_info = job_manager.restart_job(jobid)
                res_info = json.dumps({
                    "action": action,
                    "jobid": jobid,
                    "job_info": job_info
                })

            case _:
                return {
                    "statusCode": 400,
                    "body": "action limit in [submit, stop, restart]",
                }
        
        logger.info(res_info)
        return {
            "statusCode": 200,
            "body": res_info,
        }    
    except Exception as e:
        logger.error(str(e))
        return {
            "statusCode": 400,
            "body": str(e),
        }