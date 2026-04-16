"""LLM service wrapper.

This module is intentionally *thin*:
- Centralizes OpenAI client creation
- Enforces structured outputs via `client.beta.chat.completions.parse(..., response_format=...)`
- Delegates logging to `utils/logging_utils.py` (single source of truth)
"""

from __future__ import annotations

import os
import time
from typing import Optional, Type, TypeVar

from openai import OpenAI
from pydantic import BaseModel

from utils.logging_utils import log_openai_response


DEFAULT_MODEL = os.getenv("LLM_MODEL_NAME", "gpt-5-nano")

T = TypeVar("T", bound=BaseModel)


def _client() -> OpenAI:
    # OpenAI() reads OPENAI_API_KEY from env.
    return OpenAI()


def log_openai_call(
    *,
    response,
    prompt: str,
    task_name: str = "general",
    run_id: Optional[str] = None,
) -> str:
    """Compatibility wrapper used by agents.

    Delegates to `utils.logging_utils.log_openai_response`.
    """
    return log_openai_response(response, prompt, task_name=task_name, run_id=run_id)


def call_structured_llm(
    *,
    system_prompt: str,
    user_prompt: str,
    schema: Type[T],
    model: Optional[str] = None,
    temperature: float = 0.2,
    task_name: str = "general",
    run_id: Optional[str] = None,
) -> T:
    """Call the LLM and parse output into a Pydantic model."""

    chosen_model = model or DEFAULT_MODEL
    prompt_for_logging = f"SYSTEM:\n{system_prompt}\n\nUSER:\n{user_prompt}"

    start = time.time()
    response = _client().beta.chat.completions.parse(
        model=chosen_model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=schema,
    )
    _ = round(time.time() - start, 2)

    # Log (best-effort)
    try:
        log_openai_call(response=response, prompt=prompt_for_logging, task_name=task_name, run_id=run_id)
    except Exception:
        pass

    parsed = response.choices[0].message.parsed
    if parsed is None:
        raise ValueError("Structured parsing failed: parsed object is None")
    return parsed
