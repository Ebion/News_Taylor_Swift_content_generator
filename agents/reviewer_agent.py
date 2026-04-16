"""Reviewer agent.

Aligned to `notebooks/review_agent_test.ipynb`.

Implementation note:
- Notebook uses LangChain structured output.
- Backend uses OpenAI structured parsing via `services.llm_service.call_structured_llm`.
"""

from __future__ import annotations

from typing import Optional

from agents.prompts.reviewer import build_review_prompts
from services.llm_service import call_structured_llm
from utils.review_models import ReviewOutput


def review(
    *,
    draft: str,
    style_dna: str,
    persona: str,
    model: Optional[str] = None,
    run_id: Optional[str] = None,
) -> ReviewOutput:
    canonical, system_prompt, user_prompt = build_review_prompts(
        draft=draft,
        style_dna=style_dna,
        persona=persona,
    )
    return call_structured_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema=ReviewOutput,
        model=model,
        temperature=1,
        task_name=f"{canonical}_Reviewer",
        run_id=run_id,
    )
