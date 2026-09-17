"""
routers/settings.py -- Business Settings endpoints (singleton row).

Endpoints:
  GET  /api/settings        get current settings (auto-creates defaults if missing)
  PUT  /api/settings        update min_cash_reserve and/or currency
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import BusinessSettings
from backend.app.schemas import BusinessSettingsResponse, BusinessSettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["Settings"])


def _get_or_create_settings(db: Session) -> BusinessSettings:
    """Return the singleton settings row, creating it with defaults if absent."""
    settings = db.query(BusinessSettings).filter(BusinessSettings.id == 1).first()
    if not settings:
        settings = BusinessSettings(id=1, min_cash_reserve=25000.0, currency="INR")
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("", response_model=BusinessSettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    """Return current business settings."""
    return _get_or_create_settings(db)


@router.put("", response_model=BusinessSettingsResponse)
def update_settings(req: BusinessSettingsUpdate, db: Session = Depends(get_db)):
    """Update min_cash_reserve and/or currency. Ignores None fields."""
    settings = _get_or_create_settings(db)

    if req.min_cash_reserve is not None:
        settings.min_cash_reserve = req.min_cash_reserve
    if req.currency is not None:
        settings.currency = req.currency.upper()

    db.commit()
    db.refresh(settings)
    return settings
