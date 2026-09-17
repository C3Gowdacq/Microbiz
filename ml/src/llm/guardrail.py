"""
guardrail.py -- Hallucination detection and numeric verification guardrail.

Ensures the LLM explanation never introduces fabricated numbers, inaccurate amounts,
or altered metrics not present in the original decision and agent outputs.
"""

import re
import math
from typing import Dict, Any, Set, Tuple, List


def extract_numbers_from_text(text: str) -> List[float]:
    """
    Extract all numeric values (integers, floats, currency amounts, percentages)
    from a string of text.

    Args:
        text: string to extract numbers from

    Returns:
        List of float values extracted from text
    """
    if not text:
        return []

    # Pattern matches integers, decimals, negatives, comma-separated numbers (e.g. 12,000.00)
    # Remove currency symbols (EUR, €, $) and commas before matching
    clean_text = text.replace("EUR", "").replace("€", "").replace("$", "").replace(",", "")

    # Match float numbers or integers
    pattern = r"[-+]?\d*\.\d+|\d+"
    matches = re.findall(pattern, clean_text)

    numbers = []
    for m in matches:
        try:
            val = float(m)
            numbers.append(val)
        except ValueError:
            continue

    return numbers


def build_allowed_numbers_set(decision_dict: Dict[str, Any], supporting_facts_dict: Dict[str, Any]) -> Set[float]:
    """
    Recursively extract every numeric value present in decision_dict and
    supporting_facts_dict to form the set of allowed grounding numbers.

    Args:
        decision_dict:         Primary & secondary decision recommendations dict
        supporting_facts_dict: Raw outputs from all 5 agents

    Returns:
        Set of float numbers found in the grounding data
    """
    allowed = set()

    def _extract_recursive(data: Any):
        if isinstance(data, (int, float)):
            if not isinstance(data, bool):  # skip booleans
                val = float(data)
                allowed.add(round(val, 2))
                allowed.add(round(val, 1))
                allowed.add(float(math.floor(val)))
                allowed.add(float(math.ceil(val)))
        elif isinstance(data, str):
            # Extract numbers from string values (e.g. reasons, category names)
            nums = extract_numbers_from_text(data)
            for n in nums:
                allowed.add(round(n, 2))
                allowed.add(round(n, 1))
                allowed.add(float(math.floor(n)))
        elif isinstance(data, dict):
            for v in data.values():
                _extract_recursive(v)
        elif isinstance(data, (list, tuple)):
            for item in data:
                _extract_recursive(item)

    _extract_recursive(decision_dict)
    _extract_recursive(supporting_facts_dict)

    # Standard small structural numbers (e.g. 1, 2, 7, 30 days) allowed as context
    allowed.update({0.0, 1.0, 2.0, 3.0, 5.0, 7.0, 14.0, 30.0})

    return allowed


def is_number_allowed(num: float, allowed_set: Set[float], tol: float = 1.0) -> bool:
    """
    Check if a candidate number is in the allowed set or within tolerance.
    """
    num_rounded = round(num, 2)
    if num_rounded in allowed_set or float(math.floor(num)) in allowed_set or float(math.ceil(num)) in allowed_set:
        return True

    # Tolerance check for small rounding differences
    for allowed in allowed_set:
        if abs(num - allowed) <= tol:
            return True

    return False


def create_safe_fallback_explanation(decision_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a deterministic, template-based explanation (no LLM) when
    hallucination is detected or LLM is unavailable.

    Args:
        decision_dict: Decision Engine output dict

    Returns:
        Dict conforming to RecommendationExplanation schema
    """
    primary = decision_dict.get("primary_recommendation", {})
    action = primary.get("action", "no_action")
    reason = primary.get("reason", "Operations are stable.")

    secondaries = decision_dict.get("secondary_recommendations", [])

    summary = f"Recommendation: {action.replace('_', ' ').title()}. {reason}"

    reasoning = (
        f"The system recommended '{action}' as the primary action based on automated business rules. "
    )
    if secondaries:
        actions_str = ", ".join([s.get("action", "").replace("_", " ") for s in secondaries])
        reasoning += f"Secondary alerts flagged for attention: {actions_str}."
    else:
        reasoning += "All supporting agent metrics are within normal parameters."

    # Customer message draft if payment reminder is present
    customer_msg = None
    for sec in secondaries:
        if sec.get("action") == "send_payment_reminder":
            customer_msg = (
                f"Hello, this is a friendly reminder regarding your outstanding invoice balance. "
                f"Please let us know when payment can be expected. Thank you for your business!"
            )
            break

    return {
        "summary": summary,
        "reasoning": reasoning,
        "suggested_customer_message": customer_msg,
        "is_fallback": True,
    }


def check_for_hallucinated_numbers(
    explanation_dict: Dict[str, Any],
    allowed_numbers: Set[float],
) -> Tuple[bool, List[float], Dict[str, Any]]:
    """
    Verify all numbers in the LLM's explanation against allowed grounding numbers.

    Args:
        explanation_dict: Dict containing summary, reasoning, suggested_customer_message
        allowed_numbers:  Set of float numbers allowed from grounding data

    Returns:
        Tuple of (hallucination_detected: bool, offending_numbers: list, final_explanation: dict)
    """
    summary = explanation_dict.get("summary", "")
    reasoning = explanation_dict.get("reasoning", "")
    cust_msg = explanation_dict.get("suggested_customer_message", "") or ""

    full_llm_text = f"{summary} {reasoning} {cust_msg}"
    extracted_nums = extract_numbers_from_text(full_llm_text)

    offending_numbers = []
    for num in extracted_nums:
        if not is_number_allowed(num, allowed_numbers):
            offending_numbers.append(num)

    if offending_numbers:
        print(f"\n  [WARNING] GUARDRAIL TRIGGERED: Hallucinated number(s) detected: {offending_numbers}")
        print(f"            Replacing LLM output with deterministic fallback explanation.")
        fallback = create_safe_fallback_explanation(explanation_dict)
        fallback["hallucination_detected"] = True
        fallback["offending_numbers"] = offending_numbers
        return True, offending_numbers, fallback

    explanation_dict["hallucination_detected"] = False
    explanation_dict["offending_numbers"] = []
    return False, [], explanation_dict
