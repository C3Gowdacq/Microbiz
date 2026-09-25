import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath("."))
from backend.app.database import SessionLocal, engine, Base
from backend.app.models import Product, Sale, Customer

def add_generic_products():
    db = SessionLocal()
    try:
        today = date.today()
        customers = db.query(Customer).all()
        if not customers:
            print("No customers found!")
            return

        new_products = [
            Product(
                sku="TEA-POWDER-500G",
                name="Black Tea Powder (500g Pack)",
                selling_price=190.0,
                cost_price=155.0,
                current_stock=8.0,
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
                current_stock=50.0,
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
                current_stock=5.0,
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
                current_stock=14.0,
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
                current_stock=6.0,
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
                current_stock=9.0,
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

        added_count = 0
        for p in new_products:
            existing = db.query(Product).filter(Product.sku == p.sku).first()
            if not existing:
                db.add(p)
                db.flush()
                # add sales history
                for day_offset in [21, 16, 11, 7, 3, 1]:
                    qty = max(2.0, round(p.reorder_level / 4.0, 1))
                    sale = Sale(
                        product_id=p.id,
                        customer_id=customers[day_offset % len(customers)].id,
                        date=today - timedelta(days=day_offset),
                        quantity=qty,
                        unit_price=p.selling_price,
                        total_amount=round(qty * p.selling_price, 2),
                    )
                    db.add(sale)
                added_count += 1
                print(f"Added: {p.name} (SKU: {p.sku})")

        db.commit()
        total_products = db.query(Product).count()
        print(f"\nSuccessfully added {added_count} new generic basic products.")
        print(f"Total products now in database: {total_products}")
    finally:
        db.close()

if __name__ == "__main__":
    add_generic_products()
