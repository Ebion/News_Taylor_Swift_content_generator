"""Run-scoped workflow orchestration.

Implements the core lifecycle:
- generate: dynamic samples -> characterization -> writer -> persist version 1
- review: load latest -> reviewer -> attach review_artifact
- rewrite: load latest -> apply selected violations + user comments -> rewriter -> append new version
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Optional

from agents.characterization_agent import characterize
from agents.reviewer_agent import review as review_agent
from agents.rewriter_agent import rewrite as rewrite_agent
from agents.writer_agent import write_with_style
from app.domain.models import RunMetadata, RunState, VersionState
from services.data_loader import get_samples
from services.run_store import save_run, update_run


def _new_project_id() -> str:
    return f"proj_{uuid.uuid4().hex[:8]}"


def _new_run_id() -> str:
    return f"run_{uuid.uuid4().hex[:8]}"


def generate(*, topic: str, persona: str, run_id: Optional[str] = None) -> dict:
    """Create a new run and persist version 1."""
    canonical_persona = "bbc" if persona.strip().lower() == "bbc" else "taylor_swift"
    project_id = _new_project_id()
    run_id_final = run_id or _new_run_id()

    samples = get_samples(persona=canonical_persona)
    dna = characterize(persona=canonical_persona, samples=samples, run_id=run_id_final)

    # Writer expects style_dna as string (as notebook did). If dict, serialize.
    style_dna_str = dna.style_guide if isinstance(dna.style_guide, str) else json.dumps(dna.style_guide, indent=2)
    draft = write_with_style(
        topic=topic,
        persona=canonical_persona,
        style_dna=style_dna_str,
        corpus_exemplar=dna.representative_sample,
        run_id=run_id_final,
    )

    v1 = VersionState(version_number=1, content=draft.content)
    state = RunState(
        project_id=project_id,
        run_id=run_id_final,
        topic=topic,
        persona=canonical_persona,
        characterization_artifact=dna,
        runs_metadata=RunMetadata(status="ACTIVE", latest_version=1),
        versions=[v1],
    )
    save_run(state)

    return {
        "project_id": project_id,
        "run_id": run_id_final,
        "version_number": 1,
        "content": draft.content,
    }


def review(*, project_id: str, run_id: str) -> Dict[str, Any]:
    """Review the latest version and attach review_artifact."""

    def _mutate(state: RunState) -> Dict[str, Any]:
        latest = state.get_latest_version()
        style_dna = state.characterization_artifact.style_guide
        style_dna_str = style_dna if isinstance(style_dna, str) else json.dumps(style_dna, indent=2)

        review_out = review_agent(
            draft=latest.content,
            style_dna=style_dna_str,
            persona=state.persona,
            run_id=run_id,
        )
        latest.review_artifact = review_out.model_dump()
        
        return latest.review_artifact

    return update_run(project_id, run_id, _mutate)


def rewrite(
    *,
    project_id: str,
    run_id: str,
    accepted_violation_indices: List[int],
    user_comments: str,
) -> Dict[str, Any]:
    """Rewrite the latest draft based on selected reviewer violations."""

    def _mutate(state: RunState) -> Dict[str, Any]:
        latest = state.get_latest_version()
        if not latest.review_artifact:
            raise ValueError("Cannot rewrite before review: latest version has no review_artifact")

        violations = (latest.review_artifact.get("violations") or [])
        filtered = []
        for i in accepted_violation_indices:
            if i < 0 or i >= len(violations):
                raise ValueError(f"accepted_violation_indices contains out-of-range index: {i}")
            filtered.append(violations[i])

        reviewer_notes = {
            "overall_fidelity_score": latest.review_artifact.get("overall_fidelity_score"),
            "critique_summary": latest.review_artifact.get("critique_summary"),
            "violations": filtered,
            "user_comments": user_comments,
        }

        style_dna = state.characterization_artifact.style_guide
        style_dna_str = style_dna if isinstance(style_dna, str) else json.dumps(style_dna, indent=2)

        rewrite_out = rewrite_agent(
            ai_draft=latest.content,
            user_modified_content=user_comments,
            reviewer_notes=reviewer_notes,
            style_dna=style_dna_str,
            persona=state.persona,
            run_id=run_id,
        )

        new_version_number = state.runs_metadata.latest_version + 1
        state.versions.append(
            VersionState(
                version_number=new_version_number,
                content=rewrite_out.rewritten_content,
                review_artifact=None,
                rewrite_metadata={
                    "based_on_version": latest.version_number,
                    "accepted_violation_indices": accepted_violation_indices,
                    "warnings": rewrite_out.warnings,
                    "fact_check_passed": rewrite_out.fact_check_passed,
                    "markdown_check_passed": rewrite_out.markdown_check_passed,
                },
            )
        )
        state.runs_metadata.latest_version = new_version_number

        return {
            "version_number": new_version_number,
            "content": rewrite_out.rewritten_content,
        }

    return update_run(project_id, run_id, _mutate)
