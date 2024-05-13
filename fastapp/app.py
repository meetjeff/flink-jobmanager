from fastapi import FastAPI, HTTPException, status, Body
from fastapi.responses import RedirectResponse
from typing import Annotated

from setting import set_config
from flinkmanager import get_job_manager

storage_config, flink_config, _ = set_config()
job_manager = get_job_manager(storage_config, flink_config)

app = FastAPI()

@app.get("/")
async def root():
    return RedirectResponse(
        url='/docs', 
        status_code=status.HTTP_307_TEMPORARY_REDIRECT
    )

@app.post('/submit')
async def submit(savepoint: Annotated[str, Body(embed=True)] = None):
    try:
        jobid = job_manager.submit_job(savepoint)
        return {'jobid': jobid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post('/stop')
async def stop(jobid: Annotated[str, Body(embed=True)] = None):
    try:
        savepoint = job_manager.stop_job(jobid)
        return {'savepoint': savepoint}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post('/restart')
async def restart(jobid: Annotated[str, Body(embed=True)] = None):
    try:
        job_info = job_manager.restart_job(jobid)
        return job_info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post('/test')
async def test(teststr: Annotated[str, Body(embed=True)] = None):
    try:
        return teststr
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))