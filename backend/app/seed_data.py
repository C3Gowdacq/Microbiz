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
                name="Wheat Flour / Atta (10kg Pack)",
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
                cost_price=2150.0,          # Cost > selling for margin alert testing
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
            Product(
                sku="TEA-POWDER-500G",
                name="Black Tea Powder (500g Pack)",
                selling_price=190.0,
                cost_price=155.0,
                current_stock=8.0,           # LOW STOCK (reorder=20)
                reorder_level=20.0,
                safety_stock=6.0,
                lead_time_days=2,
                store_type="a",
                assortment="a",
                competition_distance=550.0,
                promo_active=True,
                promo2=False,
                school_holiday=False,
            ),
            Product(
                sku="SALT-IODIZED-1KG",
                name="Iodized Table Salt (1kg Pack)",
                selling_price=28.0,
                cost_price=21.0,
                current_stock=50.0,          # Plentiful stock
                reorder_level=25.0,
                safety_stock=10.0,
                lead_time_days=2,
                store_type="a",
                assortment="a",
                competition_distance=550.0,
                promo_active=False,
                promo2=False,
                school_holiday=False,
            ),
            Product(
                sku="MILK-FRESH-1L",
                name="Fresh Dairy Milk (1L Pouch)",
                selling_price=64.0,
                cost_price=56.0,
                current_stock=5.0,           # CRITICAL STOCK (reorder=30)
                reorder_level=30.0,
                safety_stock=10.0,
                lead_time_days=1,
                store_type="a",
                assortment="b",
                competition_distance=550.0,
                promo_active=False,
                promo2=False,
                school_holiday=False,
            ),
            Product(
                sku="OIL-SUNFLOWER-1L",
                name="Refined Sunflower Cooking Oil (1L Pouch)",
                selling_price=145.0,
                cost_price=122.0,
                current_stock=14.0,          # Medium stock (reorder=25)
                reorder_level=25.0,
                safety_stock=8.0,
                lead_time_days=3,
                store_type="b",
                assortment="a",
                competition_distance=1200.0,
                promo_active=True,
                promo2=False,
                school_holiday=False,
            ),
            Product(
                sku="DETERGENT-POWDER-1KG",
                name="Laundry Detergent Powder (1kg Pack)",
                selling_price=135.0,
                cost_price=108.0,
                current_stock=22.0,
                reorder_level=15.0,
                safety_stock=5.0,
                lead_time_days=3,
                store_type="a",
                assortment="a",
                competition_distance=550.0,
                promo_active=False,
                promo2=False,
                school_holiday=False,
            ),
            Product(
                sku="SOAP-BATH-4PACK",
                name="Bathing Soap Bars (Pack of 4)",
                selling_price=120.0,
                cost_price=95.0,
                current_stock=6.0,           # LOW STOCK (reorder=15)
                reorder_level=15.0,
                safety_stock=5.0,
                lead_time_days=2,
                store_type="a",
                assortment="a",
                competition_distance=550.0,
                promo_active=False,
                promo2=False,
                school_holiday=False,
            ),
            Product(
                sku="TOOTHPASTE-200G",
                name="Herbal Dental Toothpaste (200g Tube)",
                selling_price=95.0,
                cost_price=74.0,
                current_stock=18.0,
                reorder_level=12.0,
                safety_stock=4.0,
                lead_time_days=3,
                store_type="a",
                assortment="a",
                competition_distance=550.0,
                promo_active=False,
                promo2=False,
                school_holiday=False,
            ),
            Product(
                sku="NOODLES-INSTANT-4P",
                name="Instant Wheat Noodles (Pack of 4)",
                selling_price=55.0,
                cost_price=42.0,
                current_stock=35.0,
                reorder_level=20.0,
                safety_stock=6.0,
                lead_time_days=2,
                store_type="b",
                assortment="a",
                competition_distance=1200.0,
                promo_active=True,
                promo2=False,
                school_holiday=False,
            ),
            Product(
                sku="TURMERIC-POWDER-500G",
                name="Pure Turmeric Powder (500g Pack)",
                selling_price=110.0,
                cost_price=85.0,
                current_stock=16.0,
                reorder_level=10.0,
                safety_stock=4.0,
                lead_time_days=4,
                store_type="a",
                assortment="a",
                competition_distance=550.0,
                promo_active=False,
                promo2=False,
                school_holiday=False,
            ),
            Product(
                sku="ONIONS-5KG",
                name="Fresh Red Onions (5kg Net Bag)",
                selling_price=160.0,
                cost_price=130.0,
                current_stock=9.0,           # LOW STOCK (reorder=20)
                reorder_level=20.0,
                safety_stock=6.0,
                lead_time_days=1,
                store_type="a",
                assortment="c",
                competition_distance=550.0,
                promo_active=False,
                promo2=False,
                school_holiday=False,
            ),
            Product(
                sku="POTATOES-5KG",
                name="Fresh Farm Potatoes (5kg Net Bag)",
                selling_price=140.0,
                cost_price=110.0,
                current_stock=24.0,
                reorder_level=18.0,
                safety_stock=5.0,
                lead_time_days=1,
                store_type="a",
                assortment="c",
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
        # Sales for all other generic daily products across recent days
        for prod_idx in range(4, len(products)):
            p = products[prod_idx]
            for day_offset in [21, 16, 11, 7, 3, 1]:
                qty = max(2.0, round((p.reorder_level / 4.0), 1))
                sales_records.append(
                    Sale(
                        product_id=p.id,
                        customer_id=customers[day_offset % len(customers)].id,
                        date=today - timedelta(days=day_offset),
                        quantity=qty,
                        unit_price=p.selling_price,
                        total_amount=round(qty * p.selling_price, 2),
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
