from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.http import GenerateRequest, GenerateResponse
from services import workflow


router = APIRouter(tags=["generate"])


@router.post(
    "/generate",
    response_model=GenerateResponse,
    summary="Generate a draft (version 1)",
    description=(
        "Creates a new `{project_id, run_id}` and runs the full pipeline: "
        "CSV sampling → characterization → writer.\n\n"
        "Persists run state as a JSON file under `db/` and returns version 1 content."
    ),
    responses={
        500: {
            "description": "Internal error (LLM failure, CSV issues, persistence errors).",
        }
    },
)
def generate(req: GenerateRequest):
    try:
        return workflow.generate(topic=req.topic, persona=req.persona)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
