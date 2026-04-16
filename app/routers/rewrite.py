from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.http import RewriteRequest, RewriteResponse
from services import workflow


router = APIRouter(tags=["rewrite"])


@router.post(
    "/projects/{project_id}/runs/{run_id}/rewrite",
    response_model=RewriteResponse,
    summary="Rewrite using selected reviewer feedback",
    description=(
        "Rewrites the latest version using a subset of reviewer violations (by index) plus user comments.\n\n"
        "Appends a new version (version+1) and updates `runs_metadata.latest_version`."
    ),
    responses={
        400: {"description": "Bad request (rewrite before review, invalid indices)."},
        404: {"description": "Run not found."},
        500: {"description": "Internal error (LLM failure or persistence errors)."},
    },
)
def rewrite(project_id: str, run_id: str, req: RewriteRequest):
    try:
        return workflow.rewrite(
            project_id=project_id,
            run_id=run_id,
            accepted_violation_indices=req.accepted_violation_indices,
            user_comments=req.user_comments,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
