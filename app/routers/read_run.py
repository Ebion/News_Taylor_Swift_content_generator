from __future__ import annotations

from fastapi import APIRouter, HTTPException

from services import run_store

router = APIRouter(tags=["runs"])


@router.get("/projects/{project_id}/runs/{run_id}", summary="Get run state")
def get_run(project_id: str, run_id: str):
    try:
        return run_store.load_run(project_id=project_id, run_id=run_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
