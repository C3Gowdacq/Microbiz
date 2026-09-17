"""
llm package -- LLM Explanation Layer & Numeric Guardrail for MicroBizAI.
"""

from .client import get_llm_client
from .output_schema import RecommendationExplanation
from .explain_chain import explain_decision
from .guardrail import check_for_hallucinated_numbers, build_allowed_numbers_set

__all__ = [
    "get_llm_client",
    "RecommendationExplanation",
    "explain_decision",
    "check_for_hallucinated_numbers",
    "build_allowed_numbers_set",
]
