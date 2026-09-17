"""
routers/expenses.py -- Endpoints for recording and listing Expenses.

Endpoints:
  POST  /api/expenses        record an expense
  GET   /api/expenses        list expenses (filterable by category or date range)
"""

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Expense
from backend.app.schemas import ExpenseCreate, ExpenseResponse

router = APIRouter(prefix="/api/expenses", tags=["Expenses"])


@router.post("", response_model=ExpenseResponse, status_code=201)
def create_expense(req: ExpenseCreate, db: Session = Depends(get_db)):
    """Record a new expense entry."""
    expense = Expense(
        category=req.category,
        description=req.description,
        current_period_amount=req.current_period_amount,
        prior_period_amount=req.prior_period_amount,
        date=req.expense_date or date.today(),
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.get("", response_model=List[ExpenseResponse])
def list_expenses(
    category:  Optional[str]  = Query(None, description="Filter by expense category"),
    date_from: Optional[date] = Query(None, description="Filter expenses on or after this date"),
    date_to:   Optional[date] = Query(None, description="Filter expenses on or before this date"),
    db: Session = Depends(get_db),
):
    """List all expenses, optionally filtered by category and/or date range."""
    query = db.query(Expense)
    if category:
        query = query.filter(Expense.category == category)
    if date_from:
        query = query.filter(Expense.date >= date_from)
    if date_to:
        query = query.filter(Expense.date <= date_to)
    return query.order_by(Expense.date.desc(), Expense.id.desc()).all()
