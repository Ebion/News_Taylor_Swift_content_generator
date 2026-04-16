"""Writer agent.

Aligned to `notebooks/writer_agent_test.ipynb`:
- Uses OpenAI Responses API
- Enables the `web_search` tool
"""

from __future__ import annotations

import os
from typing import Optional

from openai import OpenAI
from pydantic import BaseModel

from agents.prompts.writer import build_writer_prompt
from services.llm_service import log_openai_call


DEFAULT_MODEL = os.getenv("LLM_MODEL_NAME", "gpt-4o-mini")


class DraftOutput(BaseModel):
    content: str


def write_with_style(
    *,
    topic: str,
    persona: str,
    style_dna: str,
    corpus_exemplar: Optional[str] = None,
    model: Optional[str] = None,
    run_id: Optional[str] = None,
) -> DraftOutput:
    client = OpenAI()
    chosen_model = model or DEFAULT_MODEL
    prompt = build_writer_prompt(topic=topic, style_dna=style_dna, persona=persona, corpus_exemplar=corpus_exemplar)

    response = client.responses.create(
        model=chosen_model,
        tools=[{"type": "web_search"}],
        input=prompt,
    )

    canonical = persona.strip().lower()
    if canonical not in {"bbc", "taylor_swift", "taylorswift", "taylor"}:
        canonical = "unknown"
    canonical = "bbc" if canonical == "bbc" else ("taylor_swift" if canonical != "unknown" else "unknown")

    log_openai_call(response=response, prompt=prompt, task_name=f"{canonical}_Writer", run_id=run_id)
    return DraftOutput(content=getattr(response, "output_text", "") or "")
