"""Rewrite agent.

Aligned to `notebooks/rewrite_agent_test.ipynb`.

Note:
- Notebook uses OpenAI Responses API and returns a dict.
- Here we keep the project’s existing structured model: `utils.rewrite_models.RewriteOutput`.
- Fact/markdown checks are stubbed to True for now; we can harden later.
"""

from __future__ import annotations

import json
import os
from typing import Optional

from openai import OpenAI

from agents.prompts.rewriter import build_rewrite_prompt
from services.llm_service import log_openai_call
from utils.rewrite_models import RewriteOutput


DEFAULT_MODEL = os.getenv("LLM_MODEL_NAME", "gpt-4o-mini")


def rewrite(
    *,
    ai_draft: str,
    user_modified_content: str,
    reviewer_notes: dict,
    style_dna: str,
    persona: str,
    model: Optional[str] = None,
    run_id: Optional[str] = None,
) -> RewriteOutput:
    client = OpenAI()
    chosen_model = model or DEFAULT_MODEL
    canonical = "bbc" if persona.strip().lower() == "bbc" else "taylor_swift"

    prompt = build_rewrite_prompt(
        ai_draft=ai_draft,
        user_modified_content=user_modified_content,
        reviewer_notes_json=json.dumps(reviewer_notes, indent=2),
        style_dna=style_dna,
    )

    response = client.responses.create(model=chosen_model, input=prompt)
    log_openai_call(response=response, prompt=prompt, task_name=f"{canonical}_Rewriter", run_id=run_id)

    rewritten_content = getattr(response, "output_text", "") or ""
    return RewriteOutput(
        rewritten_content=rewritten_content,
        fact_check_passed=True,
        markdown_check_passed=True,
        warnings=[],
    )
