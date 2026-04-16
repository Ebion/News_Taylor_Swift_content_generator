"""
Rewrite Models - Pydantic models for rewrite output.
"""

from pydantic import BaseModel, Field


class RewriteOutput(BaseModel):
    """The structured output from the Rewrite Agent."""
    rewritten_content: str = Field(description="The rewritten content after applying user modifications and reviewer feedback")
    fact_check_passed: bool = Field(description="Whether the fact check passed (no factual information was changed)")
    markdown_check_passed: bool = Field(description="Whether the markdown check passed (no leftover markdown syntax)")
    warnings: list = Field(description="Any warnings about the rewrite")
