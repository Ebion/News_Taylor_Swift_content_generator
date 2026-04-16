"""
Review Models - Pydantic models for structured review output.
"""

from typing import List
from pydantic import BaseModel, Field

class StyleViolation(BaseModel):
    """A specific violation of the style guide."""
    aspect: str = Field(description="The category from DNA (e.g., Tone, Punctuation, Structure)")
    issue: str = Field(description="What the draft did wrong or missed")
    suggestion: str = Field(description="How to fix it to match the DNA")


class ReviewOutput(BaseModel):
    """The structured output from the Review Agent."""
    overall_fidelity_score: int = Field(description="1-10 score on how well the draft matches the DNA")
    violations: List[StyleViolation] = Field(description="List of style violations found in the draft")
    critique_summary: str = Field(description="A brief note to the human editor summarizing the issues")
