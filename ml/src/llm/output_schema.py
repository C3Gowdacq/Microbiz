"""
output_schema.py -- Pydantic structured output schema for LLM explanations.

Defines RecommendationExplanation schema enforcing structured JSON output
containing summary, reasoning, and optional customer outreach message.
"""

from typing import Optional
from pydantic import BaseModel, Field


class RecommendationExplanation(BaseModel):
    """Structured explanation of a deterministic decision recommendation."""

    summary: str = Field(
        description="1-2 sentence plain-language summary of the business situation."
    )
    reasoning: str = Field(
        description=(
            "Why this action is recommended, in simple terms a shopkeeper would "
            "understand, using ONLY the facts provided."
        )
    )
    suggested_customer_message: Optional[str] = Field(
        default=None,
        description=(
            "If the recommendation involves contacting a customer (e.g. payment reminder), "
            "a short polite message draft; otherwise null."
        ),
    )
