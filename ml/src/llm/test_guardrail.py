"""
test_guardrail.py -- Unit tests for numeric guardrail verification.

Tests cover:
  1. Valid explanation where all numbers exist in allowed_numbers -> pass
  2. Fabricated explanation containing a hallucinated number ($50,000) -> guardrail flags & falls back
  3. Extract numbers helper function correctness
  4. Allowed numbers set construction

Run with:  python ml/src/llm/test_guardrail.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from llm.guardrail import (
    extract_numbers_from_text,
    build_allowed_numbers_set,
    check_for_hallucinated_numbers,
)


def test_extract_numbers():
    """Verify number extraction regex on various strings."""
    text = "Current cash is €25,000.00 and customer is 45 days overdue (+33.3% increase)."
    nums = extract_numbers_from_text(text)
    assert 25000.0 in nums
    assert 45.0 in nums
    assert 33.3 in nums
    print("  [PASS] test_extract_numbers")


def test_allowed_numbers_set():
    """Verify recursive allowed numbers set construction."""
    decision_dict = {
        "primary_recommendation": {"action": "full_replenishment", "priority": "high", "reason": "Demand 200 > stock 150"},
        "secondary_recommendations": [{"action": "review_expense", "reason": "Costs up 38.9%"}],
    }
    supporting_facts = {
        "cashflow_result": {"current_cash": 25000.0, "net_cash_flow": -1400.0},
    }
    allowed = build_allowed_numbers_set(decision_dict, supporting_facts)
    assert 200.0 in allowed
    assert 150.0 in allowed
    assert 38.9 in allowed
    assert 25000.0 in allowed
    assert 1400.0 in allowed or -1400.0 in allowed
    print("  [PASS] test_allowed_numbers_set")


def test_valid_explanation_passes():
    """Valid explanation using allowed numbers should pass guardrail."""
    allowed = {25000.0, 9300.0, 6500.0, 12000.0, 45.0, 33.3, 38.9, 0.0, 1.0, 2.0}
    valid_explanation = {
        "summary": "Full replenishment recommended. Customer owes €12,000.00 for 45 days.",
        "reasoning": "We have €25,000.00 cash and utilities increased by 33.3%.",
        "suggested_customer_message": None,
    }

    hallucination_detected, offending, result = check_for_hallucinated_numbers(
        valid_explanation, allowed
    )

    assert hallucination_detected is False, f"Expected valid explanation to pass, but got offending: {offending}"
    assert len(offending) == 0
    assert result["hallucination_detected"] is False
    print("  [PASS] test_valid_explanation_passes")


def test_fabricated_number_caught_by_guardrail():
    """Deliberately fake explanation with $50,000 should be caught and replaced with fallback."""
    allowed = {25000.0, 9300.0, 6500.0, 12000.0, 45.0, 33.3, 0.0, 1.0, 2.0}

    # Deliberately fake explanation containing $50,000 not in allowed set
    fabricated_explanation = {
        "summary": "Full replenishment recommended. You will save €50,000.00 this month!",
        "reasoning": "Our forecast shows huge revenue boost of €99,999.00 next week.",
        "suggested_customer_message": "Please pay your invoice of €50,000.00 immediately.",
    }

    hallucination_detected, offending, fallback_result = check_for_hallucinated_numbers(
        fabricated_explanation, allowed
    )

    assert hallucination_detected is True, "Guardrail failed to detect fabricated numbers!"
    assert 50000.0 in offending or 99999.0 in offending, f"Expected 50000.0 or 99999.0 in offending, got: {offending}"
    assert fallback_result.get("hallucination_detected") is True
    assert fallback_result.get("is_fallback") is True
    print("  [PASS] test_fabricated_number_caught_by_guardrail (Successfully caught 50,000.0 & fell back!)")


def main():
    print("=" * 70)
    print("LLM GUARDRAIL UNIT TESTS")
    print("=" * 70)

    tests = [
        test_extract_numbers,
        test_allowed_numbers_set,
        test_valid_explanation_passes,
        test_fabricated_number_caught_by_guardrail,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  [ERROR] {t.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print("-" * 70)
    print(f"Results: {passed} passed, {failed} failed, {len(tests)} total")
    if failed > 0:
        sys.exit(1)
    else:
        print("All guardrail tests passed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
