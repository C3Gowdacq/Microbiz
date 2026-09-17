"""
routers/products.py -- CRUD endpoints for Products.

Endpoints:
  POST   /api/products              create a product (id auto-generated as UUID)
  GET    /api/products              list all products
  GET    /api/products/{id}         get a single product
  PUT    /api/products/{id}         update product fields (price, reorder levels etc.)
  PUT    /api/products/{id}/stock   set current_stock directly (e.g. after delivery)
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Product
from backend.app.schemas import ProductCreate, ProductUpdate, ProductStockUpdate, ProductResponse

router = APIRouter(prefix="/api/products", tags=["Products"])


def _product_to_response(product: Product) -> ProductResponse:
    """Convert a Product ORM object to a ProductResponse, computing ml_ready dynamically."""
    return ProductResponse(
        id=product.id,
        sku=product.sku,
        name=product.name,
        selling_price=product.selling_price,
        cost_price=product.cost_price,
        current_stock=product.current_stock,
        reorder_level=product.reorder_level,
        safety_stock=product.safety_stock,
        lead_time_days=product.lead_time_days,
        store_type=product.store_type,
        assortment=product.assortment,
        competition_distance=product.competition_distance,
        competition_open_date=product.competition_open_date,
        promo_active=product.promo_active or False,
        promo2=product.promo2 or False,
        school_holiday=product.school_holiday or False,
        ml_ready=bool(product.store_type and product.assortment),
    )


@router.post("", response_model=ProductResponse, status_code=201)
def create_product(req: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product. The id is auto-generated as a UUID."""
    product = Product(
        id=str(uuid.uuid4()),
        sku=req.sku,
        name=req.name,
        selling_price=req.selling_price,
        cost_price=req.cost_price,
        current_stock=req.current_stock,
        reorder_level=req.reorder_level,
        safety_stock=req.safety_stock,
        lead_time_days=req.lead_time_days,
        # ML Store Profile
        store_type=req.store_type,
        assortment=req.assortment,
        competition_distance=req.competition_distance,
        competition_open_date=req.competition_open_date,
        promo_active=req.promo_active,
        promo2=req.promo2,
        school_holiday=req.school_holiday,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return _product_to_response(product)


@router.get("", response_model=List[ProductResponse])
def list_products(db: Session = Depends(get_db)):
    """Return all products ordered by name."""
    products = db.query(Product).order_by(Product.name).all()
    return [_product_to_response(p) for p in products]


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: str, db: Session = Depends(get_db)):
    """Retrieve a single product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found")
    return _product_to_response(product)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: str, req: ProductUpdate, db: Session = Depends(get_db)):
    """Update product metadata (price, reorder levels, SKU, ML profile etc.). Ignores None fields."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found")

    update_data = req.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return _product_to_response(product)


@router.put("/{product_id}/stock", response_model=ProductResponse)
def update_product_stock(product_id: str, req: ProductStockUpdate, db: Session = Depends(get_db)):
    """
    Directly set current_stock on a product.
    Use this after receiving a delivery or performing a manual stock count.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found")

    if req.current_stock < 0:
        raise HTTPException(status_code=422, detail="current_stock cannot be negative")

    product.current_stock = req.current_stock
    db.commit()
    db.refresh(product)
    return _product_to_response(product)

