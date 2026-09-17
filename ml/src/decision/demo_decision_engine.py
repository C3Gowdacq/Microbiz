"""
demo_decision_engine.py -- Integration demonstration of the Decision Engine
using the exact "Rosa's Retail Store" scenario output from Part 6 (demo_all_agents.py).

Feeds outputs from Inventory, Cash Flow, Expense, Credit, and Profitability agents
into make_decision() and prints the prioritized primary & secondary recommendations.

Run with:  python ml/src/decision/demo_decision_engine.py
"""

import os
import sys
import json
from datetime import date

# Ensure imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.inventory_agent import calculate_inventory_risk
from agents.cashflow_agent import calculate_cashflow_risk
from agents.expense_agent import analyze_expense_trend
from agents.credit_agent import analyze_customer_credit
from agents.profitability_agent import calculate_profitability
from decision.engine import make_decision


def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 80)
    print("MICROBIZAI DECISION ENGINE -- ROSA'S RETAIL STORE INTEGRATION DEMO")
    print("=" * 80)

    TODAY = date(2025, 7, 16)

    # ── 1. Run Inventory Agent (3 products) ─────────────────────────────
    inventory_scenarios = [
        {
            "product_id": "SKU_ELECTRONICS_001",
            "current_stock": 150,
            "forecast_demand": 200,
            "reorder_level": 100,
            "safety_stock": 40,
            "lead_time_days": 5,
        },
        {
            "product_id": "SKU_APPAREL_042",
            "current_stock": 500,
            "forecast_demand": 120,
            "reorder_level": 80,
            "safety_stock": 25,
            "lead_time_days": 3,
        },
        {
            "product_id": "SKU_GROCERY_108",
            "current_stock": 30,
            "forecast_demand": 300,
            "reorder_level": 150,
            "safety_stock": 50,
            "lead_time_days": 2,
        },
    ]
    inventory_results = [
        calculate_inventory_risk(**s) for s in inventory_scenarios
    ]

    # ── 2. Run Cash Flow Agent ───────────────────────────────────────────
    avg_unit_price = 15.0
    total_forecast_demand = sum(s["forecast_demand"] for s in inventory_scenarios)
    expected_revenue = total_forecast_demand * avg_unit_price

    cashflow_result = calculate_cashflow_risk(
        current_cash=25000,
        expected_sales_revenue=expected_revenue,  # EUR 9,300
        upcoming_expenses=6500,
        planned_purchase_cost=4200,
        min_cash_reserve=5000,
    )

    # ── 3. Run Expense Agent (6 categories) ──────────────────────────────
    expense_categories = [
        ("Rent", 3000, 3000),
        ("Employee Wages", 8500, 7200),
        ("Utilities", 1200, 900),     # HIGH spike (+33.3%)
        ("Marketing", 2500, 1800),    # HIGH spike (+38.9%)
        ("Inventory COGS", 4200, 4000),
        ("New SaaS Tools", 800, 0),
    ]
    expense_results = [
        analyze_expense_trend(cat, curr, prior)
        for cat, curr, prior in expense_categories
    ]

    # ── 4. Run Credit Agent (4 invoices) ─────────────────────────────────
    credit_scenarios = [
        {"customer_id": "CUST_RELIABLE", "invoice_amount": 5000, "amount_paid": 5000, "due_date": date(2025, 7, 1)},
        {"customer_id": "CUST_LATE_PAY", "invoice_amount": 8000, "amount_paid": 3000, "due_date": date(2025, 6, 25)}, # 21d overdue (MEDIUM)
        {"customer_id": "CUST_DELINQUENT", "invoice_amount": 12000, "amount_paid": 0, "due_date": date(2025, 6, 1)},   # 45d overdue (HIGH)
        {"customer_id": "CUST_NEW", "invoice_amount": 3000, "amount_paid": 0, "due_date": date(2025, 7, 20)},
    ]
    credit_results = [
        analyze_customer_credit(
            customer_id=s["customer_id"],
            invoice_amount=s["invoice_amount"],
            amount_paid=s["amount_paid"],
            due_date=s["due_date"],
            today=TODAY,
        )
        for s in credit_scenarios
    ]

    # ── 5. Run Profitability Agent (5 products) ─────────────────────────
    product_portfolio = [
        ("Electronics Premium", 299.99, 180.00, 45),
        ("Electronics Budget", 49.99, 42.00, 200),
        ("Apparel T-Shirts", 24.99, 8.00, 350),
        ("Clearance Items", 9.99, 12.00, 100),       # Loss-making (-20.1%)
        ("Accessories", 14.99, 5.00, 500),
    ]
    profitability_results = [
        calculate_profitability(name, sell, cost, qty)
        for name, sell, cost, qty in product_portfolio
    ]

    # ── 6. FEED ALL AGENT OUTPUTS INTO DECISION ENGINE ──────────────────
    print("\nProcessing agent outputs through Decision Engine (make_decision)...\n")

    decision = make_decision(
        inventory_result=inventory_results,
        cashflow_result=cashflow_result,
        credit_result=credit_results,
        expense_result=expense_results,
        profitability_result=profitability_results,
    )

    # ── 7. Display Decision Results ─────────────────────────────────────

    primary = decision["primary_recommendation"]
    print("-" * 80)
    print("PRIMARY RECOMMENDATION (Highest Priority Single Action)")
    print("-" * 80)
    print(f"  Action:   {primary['action']}")
    print(f"  Priority: {primary['priority'].upper()}")
    print(f"  Reason:   {primary['reason']}")

    secondaries = decision["secondary_recommendations"]
    print("\n" + "-" * 80)
    print(f"SECONDARY RECOMMENDATIONS ({len(secondaries)} Concurrent Issues Detected)")
    print("-" * 80)
    for i, sec in enumerate(secondaries, 1):
        print(f"  {i}. [{sec['priority'].upper()}] Action: {sec['action']}")
        print(f"     Reason: {sec['reason']}")

    print("\n" + "-" * 80)
    print("BUSINESS EXECUTIVE SUMMARY")
    print("-" * 80)
    print(f"  {decision['summary']}")

    print("\n" + "-" * 80)
    print("DECISION ENGINE JSON CONTRACT OUTPUT")
    print("-" * 80)
    print(json.dumps(decision, indent=2))

    print("\n" + "=" * 80)
    print("INTEGRATION DEMO COMPLETE -- Decision Engine is fully operational.")
    print("=" * 80)


if __name__ == "__main__":
    main()
