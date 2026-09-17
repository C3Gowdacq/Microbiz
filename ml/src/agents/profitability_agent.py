"""
profitability_agent.py -- Standalone Profitability Analysis Agent.

Takes structured inputs (product pricing and sales volume) and returns
profit margin classification and business-level profitability summaries.

This module is a pure-function module with no database or API dependencies.

Public API:
  - calculate_profitability(product_id, selling_price, cost_price, quantity_sold) -> dict
  - summarize_business_profitability(product_profitability_list) -> dict
"""


def calculate_profitability(product_id, selling_price, cost_price, quantity_sold):
    """
    Calculate profitability metrics for a single product.

    Args:
        product_id:    Identifier for the product (str or int).
        selling_price: Revenue per unit sold (float).
        cost_price:    Cost per unit (float).
        quantity_sold: Number of units sold in the period (int or float >= 0).

    Returns:
        dict with keys:
            product_id, selling_price, cost_price, unit_profit,
            gross_profit, profit_margin (%), classification
            ("loss_making" | "low_margin" | "healthy_margin" | "highly_profitable")
    """
    # ── Core calculations ────────────────────────────────────────────────

    unit_profit = selling_price - cost_price
    gross_profit = unit_profit * quantity_sold

    if selling_price > 0:
        profit_margin = (unit_profit / selling_price) * 100.0
    else:
        profit_margin = 0.0

    # ── Classification ───────────────────────────────────────────────────

    if unit_profit < 0:
        classification = "loss_making"
    elif profit_margin < 10:
        classification = "low_margin"
    elif profit_margin < 30:
        classification = "healthy_margin"
    else:
        classification = "highly_profitable"

    # ── Build output contract ────────────────────────────────────────────

    return {
        "product_id": product_id,
        "selling_price": round(float(selling_price), 2),
        "cost_price": round(float(cost_price), 2),
        "unit_profit": round(float(unit_profit), 2),
        "gross_profit": round(float(gross_profit), 2),
        "profit_margin": round(float(profit_margin), 2),
        "classification": classification,
    }


def summarize_business_profitability(product_profitability_list):
    """
    Aggregate product-level profitability into a business-level summary.

    Args:
        product_profitability_list: List of dicts from calculate_profitability().

    Returns:
        dict with keys:
            total_gross_profit, average_profit_margin,
            num_products, classification_counts (dict mapping each
            classification bucket to its count)
    """
    if not product_profitability_list:
        return {
            "total_gross_profit": 0.0,
            "average_profit_margin": 0.0,
            "num_products": 0,
            "classification_counts": {},
        }

    total_gross = sum(p["gross_profit"] for p in product_profitability_list)
    avg_margin = sum(p["profit_margin"] for p in product_profitability_list) / len(product_profitability_list)

    # Count products in each classification bucket
    classification_counts = {}
    for p in product_profitability_list:
        cls = p["classification"]
        classification_counts[cls] = classification_counts.get(cls, 0) + 1

    return {
        "total_gross_profit": round(float(total_gross), 2),
        "average_profit_margin": round(float(avg_margin), 2),
        "num_products": len(product_profitability_list),
        "classification_counts": classification_counts,
    }
