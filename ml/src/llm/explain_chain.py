"""
explain_chain.py -- LangChain Groq Explanation Chain for MicroBizAI.

Constructs constrained explanation chain that takes a deterministic decision_dict
and supporting agent facts, invokes ChatGroq with RecommendationExplanation schema,
runs guardrail verification, and returns verified explanation.

References:
  - MicroBizAI_Architecture.md Section 14
"""

import os
import json
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from llm.client import get_llm_client
from llm.output_schema import RecommendationExplanation
from llm.guardrail import (
    build_allowed_numbers_set,
    check_for_hallucinated_numbers,
    create_safe_fallback_explanation,
)


SYSTEM_PROMPT = """You are a friendly, practical AI business assistant helping a small shopkeeper understand their automated business health report.

CRITICAL CONSTRAINTS:
1. Explain ONLY the exact primary and secondary recommendations provided in the Decision Data below.
2. NEVER suggest a different action than the ones given.
3. Use ONLY the facts, amounts, days, and percentages explicitly listed in the Decision Data and Supporting Agent Facts.
4. NEVER invent, estimate, extrapolate, or hallucinate any number, percentage, or currency amount not given in the input.
5. Use simple, clear language that a small shopkeeper would easily understand.
6. If a customer payment reminder is recommended, draft a short, polite payment reminder message for that customer in suggested_customer_message; otherwise set suggested_customer_message to null.

You MUST respond ONLY with a raw JSON object with keys "summary", "reasoning", "suggested_customer_message". Do NOT include markdown formatting or additional commentary outside the JSON object.
"""

HUMAN_PROMPT = """Here is the automated business analysis data for the store:

=== DETERMINISTIC DECISION RECOMMENDATIONS ===
Primary Recommendation: {primary_recommendation}
Secondary Recommendations: {secondary_recommendations}
Overall Executive Summary: {decision_summary}

=== SUPPORTING AGENT FACTS ===
Inventory Risk Analysis: {inventory_facts}
Cash Flow Projection: {cashflow_facts}
Expense Trend Analysis: {expense_facts}
Customer Credit Analysis: {credit_facts}
Product Profitability Analysis: {profitability_facts}

Provide your explanation matching the JSON schema.
"""


def explain_decision(decision_dict: Dict[str, Any], supporting_facts_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate plain-language explanation for a deterministic decision using ChatGroq.

    Args:
        decision_dict:         Primary & secondary recommendations from decision_engine
        supporting_facts_dict: Raw outputs from all 5 business agents

    Returns:
        Dict conforming to RecommendationExplanation schema (LLM generated or safe fallback)
    """
    # Build allowed grounding numbers set for guardrail check
    allowed_numbers = build_allowed_numbers_set(decision_dict, supporting_facts_dict)

    # Determine exact model name from env or default to active generation model
    model_name = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    print(f"\n  [LLM INVOCATION] Model string passed to ChatGroq: '{model_name}'")

    # Initialize LLM client
    llm = get_llm_client(model=model_name)

    if llm is None:
        print("  [LLM] GROQ_API_KEY not set. Using safe deterministic fallback explanation.")
        fallback = create_safe_fallback_explanation(decision_dict)
        fallback["is_fallback"] = True
        return fallback

    try:
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", HUMAN_PROMPT),
        ])

        chain = prompt | llm

        # Format input variables (using default=str for date serialization)
        primary_rec = json.dumps(decision_dict.get("primary_recommendation", {}), default=str)
        sec_recs = json.dumps(decision_dict.get("secondary_recommendations", []), default=str)
        summary = decision_dict.get("summary", "")

        inv_facts = json.dumps(supporting_facts_dict.get("inventory_result", []), default=str)
        cf_facts = json.dumps(supporting_facts_dict.get("cashflow_result", {}), default=str)
        exp_facts = json.dumps(supporting_facts_dict.get("expense_results", []), default=str)
        cred_facts = json.dumps(supporting_facts_dict.get("credit_results", []), default=str)
        prof_facts = json.dumps(supporting_facts_dict.get("profitability_results", []), default=str)

        # Invoke LLM chain
        raw_response = chain.invoke({
            "primary_recommendation": primary_rec,
            "secondary_recommendations": sec_recs,
            "decision_summary": summary,
            "inventory_facts": inv_facts,
            "cashflow_facts": cf_facts,
            "expense_facts": exp_facts,
            "credit_facts": cred_facts,
            "profitability_facts": prof_facts,
        })

        # BUG 1 LOG: Print the RAW, unprocessed response object returned by the Groq API call
        print(f"  [RAW GROQ RESPONSE OBJECT]\n  {repr(raw_response)}")

        raw_text = raw_response.content if hasattr(raw_response, "content") else str(raw_response)
        clean_text = raw_text.replace("```json", "").replace("```", "").strip()

        # Parse JSON and validate against RecommendationExplanation schema
        parsed_dict = json.loads(clean_text)
        obj = RecommendationExplanation(**parsed_dict)
        explanation_dict = obj.model_dump()

        # Mark as non-fallback for valid real LLM generation
        explanation_dict["is_fallback"] = False
        explanation_dict["model_used"] = model_name

        # Run guardrail verification against allowed numbers
        hallucination_detected, offending, verified_dict = check_for_hallucinated_numbers(
            explanation_dict, allowed_numbers
        )

        # BUG 2 SAFETY ENFORCEMENT: If hallucination was detected, fallback MUST have is_fallback=True
        if hallucination_detected or verified_dict.get("hallucination_detected"):
            verified_dict["is_fallback"] = True

        return verified_dict

    except Exception as e:
        print(f"  [LLM ERROR] Exception during LLM explanation generation: {str(e)}")
        print(f"              Falling back to safe deterministic template.")
        fallback = create_safe_fallback_explanation(decision_dict)
        fallback["is_fallback"] = True
        return fallback
