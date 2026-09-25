"""
routers/suppliers.py -- CRUD endpoints for Suppliers/Vendors.

Endpoints:
  GET    /api/suppliers        list all suppliers
  POST   /api/suppliers        create a new supplier
  GET    /api/suppliers/{id}   get a single supplier
  PUT    /api/suppliers/{id}   update supplier details
  DELETE /api/suppliers/{id}   deactivate (soft-delete) supplier
"""

from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Supplier
from backend.app.schemas import SupplierCreate, SupplierUpdate, SupplierResponse

router = APIRouter(prefix="/api/suppliers", tags=["Suppliers"])


def seed_default_suppliers_if_empty(db: Session):
    """Seed initial suppliers if none exist."""
    if db.query(Supplier).count() == 0:
        defaults = [
            Supplier(
                name="General Wholesale Distributors",
                contact_name="Ramesh Kumar",
                phone="+91 98765 43210",
                email="wholesale@generalretail.in",
                address="APMC Yard, Sector 18, Vashi",
                category="Grains & Staples",
                is_active=True,
            ),
            Supplier(
                name="Fresh Produce Mandi Hub",
                contact_name="Suresh Patel",
                phone="+91 98123 45678",
                email="orders@mandihub.in",
                address="Gate 4, Wholesale Fruit & Veg Market",
                category="Fresh Produce",
                is_active=True,
            ),
            Supplier(
                name="Apex FMCG Logistics",
                contact_name="Anita Sharma",
                phone="+91 98234 56789",
                email="supply@apexfmcg.com",
                address="Industrial Area Phase 2",
                category="FMCG & Packaged Goods",
                is_active=True,
            ),
        ]
        db.add_all(defaults)
        db.commit()


@router.get("", response_model=List[SupplierResponse])
def list_suppliers(
    active_only: bool = Query(False, description="Filter only active suppliers"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
):
    """List all suppliers."""
    seed_default_suppliers_if_empty(db)
    query = db.query(Supplier)
    if active_only:
        query = query.filter(Supplier.is_active == True)
    if category:
        query = query.filter(Supplier.category == category)
    return query.order_by(Supplier.name.asc()).all()


@router.post("", response_model=SupplierResponse, status_code=201)
def create_supplier(req: SupplierCreate, db: Session = Depends(get_db)):
    """Create a new supplier."""
    supplier = Supplier(
        name=req.name,
        contact_name=req.contact_name,
        phone=req.phone,
        email=req.email,
        address=req.address,
        category=req.category,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """Get single supplier by ID."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail=f"Supplier #{supplier_id} not found")
    return supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(supplier_id: int, req: SupplierUpdate, db: Session = Depends(get_db)):
    """Update supplier details."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail=f"Supplier #{supplier_id} not found")

    if req.name is not None:
        supplier.name = req.name
    if req.contact_name is not None:
        supplier.contact_name = req.contact_name
    if req.phone is not None:
        supplier.phone = req.phone
    if req.email is not None:
        supplier.email = req.email
    if req.address is not None:
        supplier.address = req.address
    if req.category is not None:
        supplier.category = req.category
    if req.is_active is not None:
        supplier.is_active = req.is_active

    db.commit()
    db.refresh(supplier)
    return supplier


@router.delete("/{supplier_id}", status_code=200)
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """Deactivate (soft-delete) a supplier."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail=f"Supplier #{supplier_id} not found")

    supplier.is_active = False
    db.commit()
    return {"message": f"Supplier #{supplier_id} deactivated successfully"}
