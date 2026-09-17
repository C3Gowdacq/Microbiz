"""
backend/app/seed_data.py

Seeds the microbizai.db SQLite database with realistic Indian grocery/retail data:
  - Products with realistic stock levels, prices, and ML profile configurations
  - Customers with realistic contact details
  - Invoices (both paid and overdue for testing credit risk)
  - Sales records across the last 30 days for trend and demand analysis
  - Operational expenses (Rent, Electricity, Logistics)
"""

import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.database import SessionLocal, engine, Base
from backend.app.models import (
    Product, Customer, Sale, Expense, Invoice, Payment, BusinessSettings
)


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Product).count() > 0:
            print("Database already contains products. Skipping seed.")
            return

        print("Seeding database with realistic retail data...")

        # ── 1. Business Settings ──────────────────────────────────────────────
        settings = db.query(BusinessSettings).filter(BusinessSettings.id == 1).first()
        if not settings:
            settings = BusinessSettings(
                id=1,
                min_cash_reserve=25000.0,
                currency="INR",
            )
            db.add(settings)

        # ── 2. Products ───────────────────────────────────────────────────────
        products = [
            Product(
                sku="RICE-BASMATI-50KG",
                name="Basmati Rice (50kg Bag)",
                selling_price=3400.0,
                cost_price=2700.0,
                current_stock=6.0,          # LOW STOCK (reorder=25)
                reorder_level=25.0,
                safety_stock=10.0,
                lead_time_days=3,
                store_type="a",
                assortment="a",
                competition_distance=550.0,
                promo_active=True,
                promo2=False,
                school_holiday=False,
            ),
            Product(
                sku="DAL-TOOR-PREM-30KG",
                name="Toor Dal Premium (30kg Sack)",
                selling_price=4200.0,
                cost_price=3500.0,
                current_stock=18.0,         # Healthy stock
                reorder_level=12.0,
                safety_stock=5.0,
                lead_time_days=4,
                store_type="a",
                assortment="a",
                competition_distance=550.0,
                promo_active=False,
                promo2=False,
                school_holiday=False,
            ),
            Product(
                sku="OIL-MUSTARD-15L",
                name="Kachi Ghani Mustard Oil (15L Tin)",
                selling_price=2150.0,
                cost_price=1800.0,
                current_stock=4.0,          # CRITICAL STOCK (reorder=15)
                reorder_level=15.0,
                safety_stock=5.0,
                lead_time_days=2,
                store_type="b",
                assortment="b",
                competition_distance=1200.0,
                promo_active=True,
                promo2=False,
                school_holiday=False,
            ),
            Product(
                sku="FLOUR-ATTA-10KG",
                name="Chakki Fresh Atta (10kg Pack)",
                selling_price=420.0,
                cost_price=360.0,
                current_stock=45.0,         # Plentiful stock
                reorder_level=20.0,
                safety_stock=8.0,
                lead_time_days=2,
                store_type="a",
                assortment="a",
                competition_distance=550.0,
                promo_active=False,
                promo2=False,
                school_holiday=False,
            ),
            Product(
                sku="SUGAR-REFINED-50KG",
                name="Refined White Sugar (50kg Bag)",
                selling_price=2100.0,
                cost_price=2150.0,          # LOSS MAKING (cost > selling) for testing!
                current_stock=12.0,
                reorder_level=10.0,
                safety_stock=4.0,
                lead_time_days=3,
                store_type="a",
                assortment="a",
                competition_distance=550.0,
                promo_active=False,
                promo2=False,
                school_holiday=False,
            ),
        ]
        db.add_all(products)
        db.commit()

        for p in products:
            db.refresh(p)

        # ── 3. Customers ──────────────────────────────────────────────────────
        customers = [
            Customer(
                name="Sharma Kirana & General Store",
                phone="+91 98765 43210",
                email="sharma.kirana@example.com",
            ),
            Customer(
                name="Verma Caterers & Sweets",
                phone="+91 98111 22334",
                email="verma.caterers@example.com",
            ),
            Customer(
                name="Gupta Wholesale Mart",
                phone="+91 98222 33445",
                email="gupta.mart@example.com",
            ),
        ]
        db.add_all(customers)
        db.commit()

        for c in customers:
            db.refresh(c)

        # ── 4. Invoices (One overdue for Credit Risk testing) ─────────────────
        today = date.today()
        invoices = [
            Invoice(
                customer_id=customers[0].id,
                invoice_amount=32000.0,
                amount_paid=4000.0,          # ₹28,000 pending!
                due_date=today - timedelta(days=18),  # 18 days OVERDUE
                created_date=today - timedelta(days=48),
                status="partially_paid",
            ),
            Invoice(
                customer_id=customers[1].id,
                invoice_amount=15000.0,
                amount_paid=15000.0,         # FULLY PAID
                due_date=today - timedelta(days=5),
                created_date=today - timedelta(days=30),
                status="paid",
            ),
            Invoice(
                customer_id=customers[2].id,
                invoice_amount=18500.0,
                amount_paid=0.0,             # Pending, but not yet overdue
                due_date=today + timedelta(days=7),
                created_date=today - timedelta(days=10),
                status="unpaid",
            ),
        ]
        db.add_all(invoices)
        db.commit()

        # ── 5. Historical Sales Records (Last 25 Days) ────────────────────────
        sales_records = []
        # Sales for Rice (frequent seller)
        for i in [22, 18, 14, 10, 6, 2]:
            sales_records.append(
                Sale(
                    product_id=products[0].id,
                    customer_id=customers[0].id,
                    date=today - timedelta(days=i),
                    quantity=4.0,
                    unit_price=3400.0,
                    total_amount=13600.0,
                )
            )
        # Sales for Mustard Oil
        for i in [20, 15, 8, 3]:
            sales_records.append(
                Sale(
                    product_id=products[2].id,
                    customer_id=customers[1].id,
                    date=today - timedelta(days=i),
                    quantity=3.0,
                    unit_price=2150.0,
                    total_amount=6450.0,
                )
            )
        # Sales for Atta
        for i in [24, 19, 13, 7, 1]:
            sales_records.append(
                Sale(
                    product_id=products[3].id,
                    customer_id=customers[2].id,
                    date=today - timedelta(days=i),
                    quantity=12.0,
                    unit_price=420.0,
                    total_amount=5040.0,
                )
            )

        db.add_all(sales_records)
        db.commit()

        # ── 6. Operational Expenses ───────────────────────────────────────────
        expenses = [
            Expense(
                category="Shop Rent",
                description="Commercial shop monthly rental",
                current_period_amount=18000.0,
                prior_period_amount=18000.0,
                date=today - timedelta(days=10),
            ),
            Expense(
                category="Electricity",
                description="Commercial power bill (refrigeration & lights)",
                current_period_amount=7800.0,
                prior_period_amount=4800.0,   # +62% spike for expense risk detection!
                date=today - timedelta(days=5),
            ),
            Expense(
                category="Transport & Logistics",
                description="Local tempo delivery & unloading labor",
                current_period_amount=5500.0,
                prior_period_amount=5200.0,
                date=today - timedelta(days=3),
            ),
        ]
        db.add_all(expenses)
        db.commit()

        print("Seeding completed successfully!")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
