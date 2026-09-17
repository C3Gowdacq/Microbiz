"""
credit_agent.py -- Standalone Customer Credit Risk Assessment Agent.

Takes structured inputs (customer invoice data, payment history) and returns
credit risk classification and payment reliability metrics.

This module is a pure-function module with no database or API dependencies.

Public API:
  - analyze_customer_credit(...) -> dict
  - compute_payment_reliability(customer_id, historical_invoices) -> dict
"""

from datetime import date, timedelta


def analyze_customer_credit(
    customer_id,
    invoice_amount,
    amount_paid,
    due_date,
    today=None,
):
    """
    Assess credit risk for a single customer invoice.

    Args:
        customer_id:    Identifier for the customer (str or int).
        invoice_amount: Total invoice amount (float > 0).
        amount_paid:    Amount already paid against this invoice (float >= 0).
        due_date:       Payment due date (datetime.date).
        today:          Current date for overdue calculation (default: date.today()).

    Returns:
        dict with keys:
            customer_id, outstanding_amount, days_overdue,
            customer_risk ("HIGH" | "MEDIUM" | "LOW" | "NONE"),
            recommended_action ("payment_reminder" | "monitor")
    """
    if today is None:
        today = date.today()

    # ── Core calculations ────────────────────────────────────────────────

    outstanding_amount = max(0.0, invoice_amount - amount_paid)

    if outstanding_amount > 0:
        days_overdue = max(0, (today - due_date).days)
    else:
        days_overdue = 0

    # ── Risk classification ──────────────────────────────────────────────

    if outstanding_amount == 0:
        customer_risk = "NONE"
    elif days_overdue > 30:
        customer_risk = "HIGH"
    elif days_overdue > 7:
        customer_risk = "MEDIUM"
    elif days_overdue > 0:
        customer_risk = "LOW"
    else:
        # Not yet overdue but still outstanding
        customer_risk = "LOW"

    # ── Recommended action ───────────────────────────────────────────────

    if days_overdue > 0 and outstanding_amount > 0:
        recommended_action = "payment_reminder"
    else:
        recommended_action = "monitor"

    # ── Build output contract ────────────────────────────────────────────

    return {
        "customer_id": customer_id,
        "outstanding_amount": round(float(outstanding_amount), 2),
        "days_overdue": days_overdue,
        "customer_risk": customer_risk,
        "recommended_action": recommended_action,
    }


def compute_payment_reliability(customer_id, historical_invoices):
    """
    Compute average payment delay from a customer's invoice history.

    Args:
        customer_id:          Customer identifier (str or int).
        historical_invoices:  List of dicts, each with:
                                - "due_date": datetime.date
                                - "payment_date": datetime.date

    Returns:
        dict with keys:
            customer_id, average_payment_delay_days (float, clipped >= 0),
            num_invoices_analyzed (int)
    """
    if not historical_invoices:
        return {
            "customer_id": customer_id,
            "average_payment_delay_days": 0.0,
            "num_invoices_analyzed": 0,
        }

    delays = []
    for inv in historical_invoices:
        delay = (inv["payment_date"] - inv["due_date"]).days
        delays.append(max(0, delay))  # Clip early payments to 0

    avg_delay = sum(delays) / len(delays)

    return {
        "customer_id": customer_id,
        "average_payment_delay_days": round(float(avg_delay), 2),
        "num_invoices_analyzed": len(delays),
    }
