"""Characterization agent.

Implements the style-guide extraction behavior tested in
`notebooks/charaterization_agent.ipynb`, but with structured outputs.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import os

from pydantic import BaseModel, Field

from agents.prompts.characterization import build_characterization_prompt
from app.domain.models import CharacterizationDNA
from services.llm_service import call_structured_llm


def _count_input_tokens(*, model: str, text: str) -> int:
    """Count input tokens for text using OpenAI's token counter.

    Best-effort: if token counting fails (network issues, unsupported model), we fall back
    to a rough character heuristic.
    """
    try:
        # Lazy import to keep module import light.
        from openai import OpenAI

        client = OpenAI()
        resp = client.responses.input_tokens.count(model=model, input=text)
        return int(getattr(resp, "input_tokens", 0) or 0)
    except Exception:
        # Rough fallback: ~4 chars/token is a common rule of thumb for English.
        return max(1, int(len(text) / 4))


def _truncate_corpus_to_token_budget(
    *,
    samples: List[str],
    max_tokens: int,
    token_count_model: str,
) -> str:
    """Join samples into a corpus string truncated to a token budget.

    Strategy:
    - Keep as many full samples as possible (preserves contextual clues).
    - If even the first sample exceeds budget, truncate within that sample.
    """

    if max_tokens <= 0:
        return "\n---\n".join(samples)

    joined: List[str] = []
    for s in samples:
        candidate = ("\n---\n".join(joined + [s])) if joined else s
        if _count_input_tokens(model=token_count_model, text=candidate) <= max_tokens:
            joined.append(s)
            continue
        break

    if joined:
        return "\n---\n".join(joined)

    # Budget is smaller than the first sample: truncate inside the first sample.
    first = samples[0] if samples else ""
    lo, hi = 0, len(first)
    best = ""
    # Binary search for the largest prefix that fits.
    while lo <= hi:
        mid = (lo + hi) // 2
        candidate = first[:mid]
        if _count_input_tokens(model=token_count_model, text=candidate) <= max_tokens:
            best = candidate
            lo = mid + 1
        else:
            hi = mid - 1
    return best


class StyleGuideSchema(BaseModel):
    # Keep keys aligned with the notebook output.
    # BBC tone is a string; Taylor tone is a list of tone objects.
    Tone: Union[str, List["ToneItem"]]

    # BBC structure is an object; Taylor structure is a list of strings.
    Structure: Union[Dict[str, str], List[str]]

    # Notebook key: "Punctuation Quirk"
    Punctuation_Quirk: List[str] = Field(alias="Punctuation Quirk")
    # Notebook key: "Vocabulary Level"
    Vocabulary_Level: Union[str, Dict[str, str]] = Field(alias="Vocabulary Level")

    # BBC formatting is an object; Taylor formatting is a list of strings.
    Formatting: Union[Dict[str, str], List[str]]

    # Notebook key: "Key Phrases"
    Key_Phrases: List[str] = Field(alias="Key Phrases")

    # Chosen exemplar snippet for downstream few-shot conditioning.
    Representative_Sample: str = Field(alias="Representative Sample")


class ToneItem(BaseModel):
    label: str
    description: str
    examples: Optional[List[str]] = None


def characterize(
    *,
    persona: str,
    samples: List[str],
    model: str | None = None,
    run_id: str | None = None,
) -> CharacterizationDNA:
    """Generate a CharacterizationDNA object from runtime samples."""
    p = persona.strip().lower()
    if p not in {"bbc", "taylor_swift", "taylorswift", "taylor"}:
        raise ValueError("persona must be 'bbc' or 'taylor_swift'")

    canonical = "bbc" if p == "bbc" else "taylor_swift"
    source_type = "BBC News Articles" if canonical == "bbc" else "Taylor Swift Tweets"

    # Env-driven corpus token budget (applies to the corpus block only).
    max_corpus_tokens = int(os.getenv("CHAR_CORPUS_MAX_INPUT_TOKENS", "8000"))
    token_count_model = os.getenv("CHAR_CORPUS_TOKEN_COUNT_MODEL") or os.getenv("LLM_MODEL_NAME", "gpt-5")

    corpus = _truncate_corpus_to_token_budget(
        samples=samples,
        max_tokens=max_corpus_tokens,
        token_count_model=token_count_model,
    )

    user_prompt = build_characterization_prompt(corpus=corpus, source_type=source_type)
    system_prompt = "You are a careful analyst. Output valid JSON only."

    parsed = call_structured_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema=StyleGuideSchema,
        model=model,
        temperature=1,
        task_name=f"{canonical}_Style_Extraction",
        run_id=run_id,
    )

    style_guide_dict: Dict[str, Any] = parsed.model_dump(by_alias=True)
    return CharacterizationDNA(
        persona=canonical,
        style_guide=style_guide_dict,
        representative_sample=style_guide_dict.get("Representative Sample"),
        sample_count=len(samples),
    )
