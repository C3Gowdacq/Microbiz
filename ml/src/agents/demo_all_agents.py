"""
demo_all_agents.py -- Combined demonstration of all five business agents
operating on a shared synthetic business snapshot.

IMPORTANT: All financial/customer/product data below is SYNTHETIC DEMONSTRATION
DATA, not derived from Rossmann. Rossmann only provides store-level daily sales
data. The synthetic data is constructed to exercise all five agents realistically
and to preview the combined output that the Decision Engine (Part 7) will consume.

Agents demonstrated:
  1. Inventory Agent  (using RF-based sales forecast from Rossmann test data)
  2. Cash Flow Agent  (synthetic financials)
  3. Expense Agent    (synthetic expense categories)
  4. Credit Agent     (synthetic customer invoices)
  5. Profitability Agent (synthetic product portfolio)

Run with:  python ml/src/agents/demo_all_agents.py
"""

import os
import sys
import json
from datetime import date, timedelta

# Ensure imports work
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from inventory_agent import calculate_inventory_risk
from cashflow_agent import calculate_cashflow_risk
from expense_agent import analyze_expense_trend
from credit_agent import analyze_customer_credit, compute_payment_reliability
from profitability_agent import calculate_profitability, summarize_business_profitability


def section_header(title, width=80):
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("*" * 80)
    print("*" + " " * 78 + "*")
    print("*" + "  MICROBIZAI -- ALL FIVE AGENTS COMBINED DEMO".center(78) + "*")
    print("*" + "  Synthetic Business Snapshot".center(78) + "*")
    print("*" + " " * 78 + "*")
    print("*" * 80)

    # ══════════════════════════════════════════════════════════════════════
    # SYNTHETIC SCENARIO DEFINITION
    # ══════════════════════════════════════════════════════════════════════
    #
    # Business: "Rosa's Retail Store" -- a mid-size retail shop.
    # Planning period: 1 week (7 days)
    # Today: 2025-07-16
    #
    # All financial data below is SYNTHETIC, constructed to create a
    # realistic mix of healthy, borderline, and problematic situations
    # for demonstration purposes.

    TODAY = date(2025, 7, 16)

    # ── 1. INVENTORY AGENT ───────────────────────────────────────────────
    section_header("AGENT 1: INVENTORY RISK ASSESSMENT")

    # Three product lines with different stock situations
    inventory_scenarios = [
        {
            "product_id": "SKU_ELECTRONICS_001",
            "current_stock": 150,
            "forecast_demand": 200,     # High demand, stock won't cover
            "reorder_level": 100,
            "safety_stock": 40,
            "lead_time_days": 5,
            "desc": "Popular electronics -- high demand, low stock",
        },
        {
            "product_id": "SKU_APPAREL_042",
            "current_stock": 500,
            "forecast_demand": 120,     # Well-stocked
            "reorder_level": 80,
            "safety_stock": 25,
            "lead_time_days": 3,
            "desc": "Seasonal apparel -- well stocked",
        },
        {
            "product_id": "SKU_GROCERY_108",
            "current_stock": 30,
            "forecast_demand": 300,     # Critically low for perishables
            "reorder_level": 150,
            "safety_stock": 50,
            "lead_time_days": 2,
            "desc": "Perishable groceries -- critically low stock",
        },
    ]

    inventory_results = []
    for scenario in inventory_scenarios:
        result = calculate_inventory_risk(
            product_id=scenario["product_id"],
            current_stock=scenario["current_stock"],
            forecast_demand=scenario["forecast_demand"],
            reorder_level=scenario["reorder_level"],
            safety_stock=scenario["safety_stock"],
            lead_time_days=scenario["lead_time_days"],
        )
        inventory_results.append(result)
        tag = f"[{result['stockout_risk']}]"
        print(f"\n  {tag:<8} {scenario['desc']}")
        print(f"           Product: {result['product_id']}")
        print(f"           Demand: {result['forecast_demand']:,.0f} | Stock: {result['current_stock']:,.0f} | Gap: {result['stock_gap']:,.0f}")
        cov = result['stock_coverage_days']
        print(f"           Coverage: {f'{cov:.1f} days' if cov is not None else 'infinite'} | Risk: {result['stockout_risk']}")
        print(f"           Order Recommended: {result['recommended_order_quantity']:,.0f} units")

    # ── 2. CASH FLOW AGENT ───────────────────────────────────────────────
    section_header("AGENT 2: CASH FLOW RISK ASSESSMENT")

    # SYNTHETIC ASSUMPTIONS:
    # Revenue estimate = sum of forecast demands * average unit price (~EUR 15/unit)
    avg_unit_price = 15.0
    total_forecast_demand = sum(s["forecast_demand"] for s in inventory_scenarios)
    expected_revenue = total_forecast_demand * avg_unit_price

    cashflow_result = calculate_cashflow_risk(
        current_cash=25000,
        expected_sales_revenue=expected_revenue,  # ~EUR 9,300
        upcoming_expenses=6500,      # Rent, wages, utilities
        planned_purchase_cost=4200,  # Inventory restocking
        min_cash_reserve=5000,
    )

    tag = f"[{cashflow_result['cash_shortage_risk']}]"
    print(f"\n  {tag} Weekly Cash Flow Projection")
    print(f"     Current Cash:         EUR {cashflow_result['current_cash']:>10,.2f}")
    print(f"     Expected Revenue:     EUR {cashflow_result['expected_sales_revenue']:>10,.2f}")
    print(f"     Upcoming Expenses:    EUR {cashflow_result['upcoming_expenses']:>10,.2f}")
    print(f"     Purchase Costs:       EUR {cashflow_result['planned_purchase_cost']:>10,.2f}")
    print(f"     -------------------------------------")
    print(f"     Net Cash Flow:        EUR {cashflow_result['net_cash_flow']:>10,.2f}")
    print(f"     Projected Balance:    EUR {cashflow_result['projected_cash_balance']:>10,.2f}")
    print(f"     Cash Shortage Risk:   {cashflow_result['cash_shortage_risk']}")
    print(f"     Liquidity OK:         {'YES [OK]' if cashflow_result['liquidity_ok'] else 'NO [ALERT]'}")

    # ── 3. EXPENSE AGENT ─────────────────────────────────────────────────
    section_header("AGENT 3: EXPENSE TREND ANALYSIS")

    # SYNTHETIC expense categories with period-over-period comparison
    expense_categories = [
        ("Rent",            3000, 3000),    # Stable
        ("Employee Wages",  8500, 7200),    # +18% increase
        ("Utilities",       1200, 900),     # +33% spike
        ("Marketing",       2500, 1800),    # +39% spike
        ("Inventory COGS",  4200, 4000),    # +5% modest
        ("New SaaS Tools",  800,  0),       # Brand new expense
    ]

    expense_results = []
    for cat, current, prior in expense_categories:
        result = analyze_expense_trend(cat, current, prior)
        expense_results.append(result)
        tag = f"[{result['risk']}]"
        pct_str = f"{result['increase_pct']:+.1f}%" if result['increase_pct'] is not None else "N/A (new)"
        print(f"  {tag:<8} {result['category']:<20} EUR {current:>7,} vs EUR {prior:>7,}  ({pct_str})  [{result['trend']}]")

    # ── 4. CREDIT AGENT ──────────────────────────────────────────────────
    section_header("AGENT 4: CUSTOMER CREDIT RISK ASSESSMENT")

    # SYNTHETIC customer invoices
    credit_scenarios = [
        {
            "customer_id": "CUST_RELIABLE",
            "invoice_amount": 5000,
            "amount_paid": 5000,
            "due_date": date(2025, 7, 1),
            "desc": "Reliable customer -- fully paid",
        },
        {
            "customer_id": "CUST_LATE_PAY",
            "invoice_amount": 8000,
            "amount_paid": 3000,
            "due_date": date(2025, 6, 25),
            "desc": "Late payer -- 21 days overdue, partial payment",
        },
        {
            "customer_id": "CUST_DELINQUENT",
            "invoice_amount": 12000,
            "amount_paid": 0,
            "due_date": date(2025, 6, 1),
            "desc": "Delinquent -- 45 days overdue, no payment",
        },
        {
            "customer_id": "CUST_NEW",
            "invoice_amount": 3000,
            "amount_paid": 0,
            "due_date": date(2025, 7, 20),
            "desc": "New customer -- invoice not yet due",
        },
    ]

    credit_results = []
    for scenario in credit_scenarios:
        result = analyze_customer_credit(
            customer_id=scenario["customer_id"],
            invoice_amount=scenario["invoice_amount"],
            amount_paid=scenario["amount_paid"],
            due_date=scenario["due_date"],
            today=TODAY,
        )
        credit_results.append(result)
        tag = f"[{result['customer_risk']}]"
        print(f"\n  {tag:<8} {scenario['desc']}")
        print(f"           Customer: {result['customer_id']}")
        print(f"           Outstanding: EUR {result['outstanding_amount']:,.2f} | Overdue: {result['days_overdue']} days")
        print(f"           Risk: {result['customer_risk']} | Action: {result['recommended_action']}")

    # Payment reliability for the late payer
    print("\n  [STATS] Payment Reliability History (CUST_LATE_PAY):")
    late_history = [
        {"due_date": date(2025, 3, 15), "payment_date": date(2025, 3, 25)},  # 10 days late
        {"due_date": date(2025, 4, 15), "payment_date": date(2025, 4, 28)},  # 13 days late
        {"due_date": date(2025, 5, 15), "payment_date": date(2025, 5, 22)},  # 7 days late
    ]
    reliability = compute_payment_reliability("CUST_LATE_PAY", late_history)
    print(f"          Avg Payment Delay: {reliability['average_payment_delay_days']:.1f} days "
          f"(over {reliability['num_invoices_analyzed']} invoices)")

    # ── 5. PROFITABILITY AGENT ───────────────────────────────────────────
    section_header("AGENT 5: PROFITABILITY ANALYSIS")

    # SYNTHETIC product portfolio with mixed margins
    product_portfolio = [
        ("Electronics Premium",  299.99, 180.00, 45),
        ("Electronics Budget",    49.99,  42.00, 200),
        ("Apparel T-Shirts",      24.99,  8.00,  350),
        ("Clearance Items",        9.99,  12.00, 100),   # Loss-making
        ("Accessories",           14.99,   5.00, 500),
    ]

    profitability_results = []
    for name, sell, cost, qty in product_portfolio:
        result = calculate_profitability(name, sell, cost, qty)
        profitability_results.append(result)
        tag = f"[{result['classification']}]"
        print(f"  {tag:<22} {name:<22} Sell: EUR {sell:>7.2f}  Cost: EUR {cost:>7.2f}  "
              f"Margin: {result['profit_margin']:>5.1f}%  GP: EUR {result['gross_profit']:>9,.2f}")

    # Business-level summary
    summary = summarize_business_profitability(profitability_results)
    print(f"\n  [SUMMARY] Business Portfolio Summary:")
    print(f"            Total Gross Profit:     EUR {summary['total_gross_profit']:>10,.2f}")
    print(f"            Average Profit Margin:  {summary['average_profit_margin']:>10.1f}%")
    print(f"            Products Analyzed:      {summary['num_products']}")
    for cls, count in sorted(summary["classification_counts"].items()):
        print(f"              - {cls}: {count}")

    # ══════════════════════════════════════════════════════════════════════
    # COMBINED BUSINESS SNAPSHOT (Decision Engine Preview)
    # ══════════════════════════════════════════════════════════════════════
    section_header("COMBINED BUSINESS HEALTH SNAPSHOT (Decision Engine Input)")

    # Aggregate risk signals across all agents
    inv_risks = [r["stockout_risk"] for r in inventory_results]
    high_inv = sum(1 for r in inv_risks if r == "HIGH")

    high_expenses = sum(1 for r in expense_results if r["risk"] == "HIGH")
    high_credit = sum(1 for r in credit_results if r["customer_risk"] == "HIGH")

    total_outstanding = sum(r["outstanding_amount"] for r in credit_results)
    total_order_cost = sum(r["recommended_order_quantity"] for r in inventory_results) * avg_unit_price

    print(f"""
  +---------------------------------------------------------+
  |  BUSINESS HEALTH DASHBOARD -- Rosa's Retail Store        |
  |  Date: {TODAY.strftime('%Y-%m-%d')}                                        |
  +---------------------------------------------------------+
  |  [INVENTORY]                                            |
  |    * {high_inv} product(s) at HIGH stockout risk              |
  |    * Total restock cost estimate: EUR {total_order_cost:>10,.2f}       |
  |                                                         |
  |  [CASH FLOW]                                            |
  |    * Projected balance: EUR {cashflow_result['projected_cash_balance']:>10,.2f}              |
  |    * Risk level: {cashflow_result['cash_shortage_risk']:<8}                              |
  |    * Liquidity: {'OK' if cashflow_result['liquidity_ok'] else 'AT RISK':<10}                            |
  |                                                         |
  |  [EXPENSES]                                             |
  |    * {high_expenses} category(ies) with HIGH cost increase         |
  |    * Requires review: Utilities, Marketing               |
  |                                                         |
  |  [CREDIT]                                               |
  |    * {high_credit} customer(s) at HIGH credit risk                |
  |    * Total outstanding receivables: EUR {total_outstanding:>10,.2f}   |
  |                                                         |
  |  [PROFITABILITY]                                        |
  |    * Portfolio gross profit: EUR {summary['total_gross_profit']:>10,.2f}          |
  |    * Avg margin: {summary['average_profit_margin']:.1f}%                                  |
  |    * Loss-making products: {summary['classification_counts'].get('loss_making', 0):<3}                          |
  +---------------------------------------------------------+
    """)

    print("=" * 80)
    print("DEMO COMPLETE -- All 5 agents operational. Ready for Decision Engine (Part 7).")
    print("=" * 80)


if __name__ == "__main__":
    main()
