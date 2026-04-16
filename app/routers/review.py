from __future__ import annotations

from fastapi import APIRouter, HTTPException

from services import workflow


router = APIRouter(tags=["review"])


@router.post(
    "/projects/{project_id}/runs/{run_id}/review",
    summary="Review the latest draft",
    description=(
        "Loads the run state from disk, finds the latest version, and runs the Reviewer agent.\n\n"
        "The structured review artifact is attached to the latest version (history is not overwritten)."
    ),
    responses={
        404: {"description": "Run not found."},
        500: {"description": "Internal error (LLM failure or persistence errors)."},
    },
)
def review(project_id: str, run_id: str):
    try:
        return workflow.review(project_id=project_id, run_id=run_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
