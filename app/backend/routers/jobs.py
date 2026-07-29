from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException

from ..auth import sp_client

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

FORWARD_ETL_JOB_ID = os.environ.get("FORWARD_ETL_JOB_ID")


@router.post("/run-forward-etl")
def run_forward_etl():
    if not FORWARD_ETL_JOB_ID:
        raise HTTPException(status_code=500, detail="FORWARD_ETL_JOB_ID not configured")
    run = sp_client().jobs.run_now(job_id=int(FORWARD_ETL_JOB_ID))
    return {"run_id": run.run_id}


@router.get("/")
def recent_runs():
    if not FORWARD_ETL_JOB_ID:
        return {"runs": []}
    runs = sp_client().jobs.list_runs(job_id=int(FORWARD_ETL_JOB_ID), limit=10)
    return {
        "runs": [
            {
                "run_id": r.run_id,
                "life_cycle_state": str(r.state.life_cycle_state) if r.state else None,
                "result_state": str(r.state.result_state) if r.state and r.state.result_state else None,
                "start_time": r.start_time,
            }
            for r in runs
        ]
    }


@router.get("/{run_id}")
def get_run(run_id: int):
    run = sp_client().jobs.get_run(run_id=run_id)
    state = run.state
    return {
        "run_id": run_id,
        "life_cycle_state": str(state.life_cycle_state) if state else None,
        "result_state": str(state.result_state) if state and state.result_state else None,
        "start_time": run.start_time,
        "run_page_url": run.run_page_url,
    }
