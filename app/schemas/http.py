from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Request body for `POST /generate`."""

    topic: str = Field(description="Topic to write about.")
    persona: str = Field(description="Persona pipeline to use. One of: bbc, taylor_swift")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"topic": "A new tech company announced a breakthrough in quantum computing", "persona": "bbc"},
                {"topic": "Taylor Swift announces her new album release date", "persona": "taylor_swift"},
            ]
        }
    }


class GenerateResponse(BaseModel):
    """Response body for `POST /generate`."""

    project_id: str
    run_id: str
    version_number: int
    content: str


class RewriteRequest(BaseModel):
    """Request body for `POST /projects/{project_id}/runs/{run_id}/rewrite`."""

    accepted_violation_indices: List[int] = Field(
        default_factory=list,
        description="Indices into the latest review artifact's `violations` array that the user wants applied.",
    )
    user_comments: str = Field(default="", description="Free-form user instruction/comments to guide the rewrite.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"accepted_violation_indices": [0, 2], "user_comments": "Make the headline sharper."}
            ]
        }
    }


class RewriteResponse(BaseModel):
    """Response body for rewrite. This always returns the newly appended version."""

    version_number: int
    content: str
