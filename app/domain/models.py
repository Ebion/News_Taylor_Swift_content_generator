"""Domain models for run-scoped workflow state.

This is the persisted state schema (file-based JSON DB under `db/`).

Aligned to:
- `notebooks/charaterization_agent.ipynb` which produces a style guide JSON with keys:
  Tone, Structure, Punctuation Quirk, Vocabulary Level, Formatting, Key Phrases
- `artifact/style_guides.json` which currently stores each style guide as a **JSON string**.

Design choices:
- `characterization_artifact.style_guide` is stored as either a dict (preferred) or raw JSON string.
- `review_artifact` is stored as a plain dict for persistence decoupling.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    """UTC timestamp string for persistence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


RunStatus = Literal["ACTIVE", "COMPLETED", "FAILED"]


class CharacterizationDNA(BaseModel):
    """Characterization artifact used by downstream writer/reviewer/rewriter."""

    persona: str = Field(description="Canonical persona identifier, e.g. 'bbc' or 'taylor_swift'")

    # Either a parsed style guide dict or a raw JSON string.
    # Raw string matches current `artifact/style_guides.json` representation.
    style_guide: Union[Dict[str, Any], str] = Field(
        description=(
            "Style guide derived from samples. Either dict or JSON string. "
            "Keys typically include Tone, Structure, Punctuation Quirk, Vocabulary Level, Formatting, Key Phrases."
        )
    )

    representative_sample: Optional[str] = Field(
        default=None,
        description=(
            "One verbatim exemplar chosen from the characterization corpus to help condition the writer. "
            "If present, it should be copied from the samples without paraphrasing."
        ),
    )

    # Useful for debugging/repro; optional to keep files small.
    sample_count: Optional[int] = None


class RunMetadata(BaseModel):
    status: RunStatus = Field(default="ACTIVE")
    latest_version: int = Field(default=1, ge=1)


class VersionState(BaseModel):
    version_number: int = Field(ge=1)
    created_at: str = Field(default_factory=utc_now_iso)
    content: str

    # Persisted artifacts
    review_artifact: Optional[Dict[str, Any]] = Field(default=None)
    rewrite_metadata: Optional[Dict[str, Any]] = Field(default=None)


class RunState(BaseModel):
    project_id: str
    run_id: str
    topic: str
    persona: str
    created_at: str = Field(default_factory=utc_now_iso)

    characterization_artifact: CharacterizationDNA
    runs_metadata: RunMetadata = Field(default_factory=RunMetadata)
    versions: List[VersionState] = Field(default_factory=list)

    def get_latest_version(self) -> VersionState:
        if not self.versions:
            raise ValueError("RunState has no versions")
        return max(self.versions, key=lambda v: v.version_number)

    def assert_invariants(self) -> None:
        """Basic consistency checks to avoid corrupt/partial persisted state."""
        if not self.versions:
            raise ValueError("RunState must have at least one version")

        latest = self.get_latest_version().version_number
        if self.runs_metadata.latest_version != latest:
            raise ValueError(
                f"runs_metadata.latest_version={self.runs_metadata.latest_version} does not match latest={latest}"
            )
