"""
routers/dashboard.py -- Dashboard summary endpoint derived from real stored data.

Endpoint:
  GET  /api/dashboard/summary
"""

from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Sale, Expense, Invoice, Product, Recommendation, BusinessSettings
from backend.app.schemas import DashboardSummaryResponse

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Aggregate real stored data to produce a live dashboard summary.

    - today_sales_revenue:      sum of sale.total_amount where sale.date = today
    - total_cash_position:      sum(all sales revenue) - sum(all expenses current_period_amount) - min_cash_reserve
    - low_stock_products_count: products where current_stock < reorder_level
    - overdue_invoices_count:   unpaid/partially_paid invoices past their due_date
    - pending_recommendations_count: recommendations with status='pending'
    """
    today = date.today()

    # Fetch settings (singleton row)
    settings = db.query(BusinessSettings).filter(BusinessSettings.id == 1).first()
    min_cash_reserve = settings.min_cash_reserve if settings else 25000.0
    currency = settings.currency if settings else "INR"

    # Today's sales revenue
    today_revenue_row = (
        db.query(func.coalesce(func.sum(Sale.total_amount), 0.0))
        .filter(Sale.date == today)
        .scalar()
    )
    today_sales_revenue = float(today_revenue_row)

    # Total cash position = total lifetime sales - total lifetime expenses - min_cash_reserve
    total_sales = float(
        db.query(func.coalesce(func.sum(Sale.total_amount), 0.0)).scalar()
    )
    total_expenses = float(
        db.query(func.coalesce(func.sum(Expense.current_period_amount), 0.0)).scalar()
    )
    total_cash_position = round(total_sales - total_expenses - min_cash_reserve, 2)

    # Products where current_stock < reorder_level (and reorder_level > 0)
    low_stock_count = (
        db.query(Product)
        .filter(Product.current_stock < Product.reorder_level, Product.reorder_level > 0)
        .count()
    )

    # Overdue invoices: unpaid or partially_paid with due_date < today
    overdue_count = (
        db.query(Invoice)
        .filter(
            Invoice.status.in_(["unpaid", "partially_paid"]),
            Invoice.due_date < today,
        )
        .count()
    )

    # Pending AI recommendations
    pending_recs_count = (
        db.query(Recommendation)
        .filter(Recommendation.status == "pending")
        .count()
    )

    return DashboardSummaryResponse(
        today_sales_revenue=today_sales_revenue,
        total_cash_position=total_cash_position,
        low_stock_products_count=low_stock_count,
        overdue_invoices_count=overdue_count,
        pending_recommendations_count=pending_recs_count,
        currency=currency,
    )
