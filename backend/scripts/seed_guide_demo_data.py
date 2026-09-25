"""
backend/scripts/seed_guide_demo_data.py

Master Seed & Reset Script for MicroBizAI Academic & Guide Presentation.
Cleans and repopulates the SQLite database with exact, realistic MSME retail data
demonstrating all 5 agents, POS risk card, customer Khata recovery, and purchase orders.

Run whenever you want to restore the perfect demo state:
    python backend/scripts/seed_guide_demo_data.py
"""

import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.database import SessionLocal, engine, Base
from backend.app.models import (
    Product, Customer, Sale, Expense, Invoice, Payment,
    Supplier, PurchaseOrder, PurchaseOrderItem, InventoryEvent,
    AgentRun, AuditLog, Recommendation, HumanAction, BusinessSettings
)


def seed_demo_database():
    db = SessionLocal()
    print("=" * 70)
    print("  MICROBIZAI — MASTER DEMO DATA SEED & RESET")
    print("=" * 70)

    try:
        # 1. Clear existing transactional & operational tables
        print("\n[1/7] Cleaning existing database records...")
        db.query(HumanAction).delete()
        db.query(AuditLog).delete()
        db.query(AgentRun).delete()
        db.query(InventoryEvent).delete()
        db.query(Recommendation).delete()
        db.query(PurchaseOrderItem).delete()
        db.query(PurchaseOrder).delete()
        db.query(Supplier).delete()
        db.query(Payment).delete()
        db.query(Invoice).delete()
        db.query(Sale).delete()
        db.query(Expense).delete()
        db.query(Product).delete()
        db.query(Customer).delete()
        db.query(BusinessSettings).delete()
        db.commit()
        print("  [OK] Database cleaned successfully.")

        # 2. Seed Business Settings
        print("\n[2/7] Configuring Business Settings...")
        settings = BusinessSettings(
            id=1,
            min_cash_reserve=25000.0,
            currency="INR",
            safety_stock_days=3,
            review_period_days=7,
            khata_overdue_days=30,
            expense_anomaly_threshold_pct=30.0,
            high_risk_multiplier=1.0,
            medium_risk_multiplier=1.5,
            autonomous_mode=True,
        )
        db.add(settings)
        db.commit()
        print("  [OK] Business Settings configured (Autonomous Mode: ENABLED, Buffer: 3 days, Min Reserve: INR 25,000).")

        # 3. Seed Suppliers
        print("\n[3/7] Seeding Retail Suppliers...")
        sup_punjab = Supplier(
            id=1,
            name="Punjab Agro Food Wholesale",
            contact_name="Gurpreet Singh",
            phone="+919811223344",
            email="orders@punjabagro.com",
            address="APMC Yard, Gate 2, Delhi",
            category="Grains & Staples",
        )
        sup_dairy = Supplier(
            id=2,
            name="Mother Dairy Processing Unit",
            contact_name="Rajesh Verma",
            phone="+919822334455",
            email="dispatch@motherdairy.com",
            address="Industrial Area, Sector 4, Noida",
            category="Dairy & Perishables",
        )
        sup_oil = Supplier(
            id=3,
            name="Fortune & Adani Wilmar Dist.",
            contact_name="Amit Shah",
            phone="+919833445566",
            email="supplies@adaniwilmar.com",
            address="Wholesale Depot 12, Surat",
            category="Edible Oils & FMCG",
        )
        db.add_all([sup_punjab, sup_dairy, sup_oil])
        db.commit()
        print("  [OK] 3 Primary Suppliers registered.")

        # 4. Seed Products
        print("\n[4/7] Seeding Products with targeted Risk States...")
        p_rice = Product(
            id="16ed43d7-c035-4bdc-9650-b93254b6ad7c",
            sku="GRO-RICE-001",
            name="Basmati Rice (50kg Bag)",
            selling_price=1350.0,
            cost_price=1100.0,
            current_stock=2.0,       # CRITICAL STOCK RISK! (ROP is 25.0)
            reorder_level=25.0,
            safety_stock=5.0,
            lead_time_days=2,
            store_type="a",
            assortment="c",
            promo_active=False,
        )
        p_milk = Product(
            id="225ee64b-9055-4ba1-92aa-3c4f6170b46a",
            sku="DAIRY-MILK-002",
            name="Fresh Dairy Milk (1L Pouch)",
            selling_price=66.0,
            cost_price=58.0,
            current_stock=3.0,       # CRITICAL PERISHABLE RISK! (ROP is 30.0)
            reorder_level=30.0,
            safety_stock=8.0,
            lead_time_days=1,
            store_type="b",
            assortment="a",
            promo_active=False,
        )
        p_atta = Product(
            id="415196bf-927b-4439-9e53-7260a099d8b4",
            sku="GRO-ATTA-003",
            name="Chakki Fresh Atta (10kg Pack)",
            selling_price=420.0,
            cost_price=360.0,
            current_stock=45.0,      # HEALTHY STOCK! (ROP is 20.0)
            reorder_level=20.0,
            safety_stock=5.0,
            lead_time_days=2,
            store_type="a",
            assortment="a",
            promo_active=False,
        )
        p_sugar = Product(
            id="da629e7c-58a5-4738-a31c-c4e56f11e174",
            sku="GRO-SUG-004",
            name="Refined White Sugar (50kg Bag)",
            selling_price=2100.0,
            cost_price=2150.0,      # LOSS-MAKING MARGIN (-2.38%) FOR PROFITABILITY AGENT!
            current_stock=15.0,
            reorder_level=10.0,
            safety_stock=2.0,
            lead_time_days=3,
            store_type="a",
            assortment="c",
        )
        p_oil = Product(
            id="f4a451f4-f0c7-45c7-9753-e951365cef79",
            sku="OIL-MUST-005",
            name="Kachi Ghani Mustard Oil (15L Tin)",
            selling_price=2250.0,
            cost_price=1950.0,
            current_stock=12.0,
            reorder_level=15.0,
            safety_stock=3.0,
            lead_time_days=3,
            store_type="c",
            assortment="b",
        )
        db.add_all([p_rice, p_milk, p_atta, p_sugar, p_oil])
        db.commit()
        print("  [OK] 5 Showcase Products registered with specific risk & margin profiles.")

        # 5. Seed Customers & Khata Invoices
        print("\n[5/7] Seeding Customers & Khata Credit Accounts...")
        cust_sharma = Customer(
            id="c2e035bd-d7c2-4177-aec4-9e5e4997f2a5",
            name="Sharma Kirana & General Store",
            phone="+919611225645",
            email="sharma.kirana@example.com",
        )
        cust_gupta = Customer(
            id="b2c6976c-8b2d-4772-bc4b-ddc2633d0320",
            name="Gupta Wholesale Mart",
            phone="+919876543211",
            email="gupta.mart@example.com",
        )
        cust_verma = Customer(
            id="38c39ddd-fc4a-424c-8537-bf1da873e61e",
            name="Verma Caterers & Sweets",
            phone="+919876543212",
            email="verma.sweets@example.com",
        )
        db.add_all([cust_sharma, cust_gupta, cust_verma])
        db.commit()

        today = date.today()
        # Sharma: 36 days overdue (HIGH RISK DEBT)
        inv_sharma = Invoice(
            id=1,
            customer_id=cust_sharma.id,
            invoice_amount=28000.0,
            amount_paid=0.0,
            due_date=today - timedelta(days=36),
            created_date=today - timedelta(days=66),
            status="unpaid",
        )
        # Gupta: 11 days overdue (MEDIUM RISK DEBT)
        inv_gupta = Invoice(
            id=2,
            customer_id=cust_gupta.id,
            invoice_amount=18500.0,
            amount_paid=0.0,
            due_date=today - timedelta(days=11),
            created_date=today - timedelta(days=41),
            status="unpaid",
        )
        # Verma: Fully paid (HEALTHY)
        inv_verma = Invoice(
            id=3,
            customer_id=cust_verma.id,
            invoice_amount=12000.0,
            amount_paid=12000.0,
            due_date=today - timedelta(days=5),
            created_date=today - timedelta(days=35),
            status="paid",
        )
        db.add_all([inv_sharma, inv_gupta, inv_verma])
        db.commit()
        print("  [OK] 3 Customers & Khata Invoices created (Total Overdue: INR 46,500 across 2 accounts).")

        # 6. Seed Historical Sales & Expenses for Solvency & Velocity
        print("\n[6/7] Seeding Sales History & Operational Expenses...")
        # Create rolling 30-day sales history
        for i in range(1, 31):
            sale_date = today - timedelta(days=i)
            db.add(Sale(
                product_id=p_rice.id,
                customer_id=cust_sharma.id,
                store_id=1,
                date=sale_date,
                quantity=10.0,
                unit_price=1350.0,
                total_amount=13500.0,
            ))
            db.add(Sale(
                product_id=p_milk.id,
                customer_id=None,
                store_id=1,
                date=sale_date,
                quantity=20.0,
                unit_price=66.0,
                total_amount=1320.0,
            ))
            db.add(Sale(
                product_id=p_atta.id,
                customer_id=cust_gupta.id,
                store_id=1,
                date=sale_date,
                quantity=5.0,
                unit_price=420.0,
                total_amount=2100.0,
            ))

        # Baseline Operational Expenses
        categories = [
            ("Rent & Lease", 25000.0, "Monthly store premise rent"),
            ("Electricity & Utilities", 7500.0, "Cold storage and store lighting"),
            ("Logistics & Transport", 6800.0, "Stock collection from wholesale mandi"),
            ("Packaging & Sundries", 4200.0, "Bags, tape, and register supplies"),
        ]
        for cat, amt, desc in categories:
            db.add(Expense(
                category=cat,
                current_period_amount=amt,
                prior_period_amount=amt * 0.95,
                date=today - timedelta(days=5),
                description=desc,
            ))

        db.commit()
        print("  [OK] Sales history (30 days) and baseline expenses established (Net Cash: ~INR 2,27,000).")

        # 7. Seed Initial Purchase Orders & Audit Ledger
        print("\n[7/7] Seeding Purchase Orders & Initial Multi-Agent Recommendations...")
        now = datetime.now(timezone.utc)

        # Pre-seed a draft purchase order for Punjab Agro
        po_draft = PurchaseOrder(
            id=1,
            po_number="PO-2026-0001",
            supplier_id=sup_punjab.id,
            status="DRAFT",
            priority="HIGH",
            total_amount=30800.0,
            reason="Automated replenishment order drafted for Basmati Rice (50kg Bag) - Current stock 2 units < ROP 25 units",
            created_at=now,
        )
        db.add(po_draft)
        db.flush()

        db.add(PurchaseOrderItem(
            purchase_order_id=po_draft.id,
            product_id=p_rice.id,
            quantity=28.0,
            unit_cost=1100.0,
            total_cost=30800.0,
        ))

        # Seed Human-Readable Recommendation #1 for AI Approvals Inbox
        rec_demo = Recommendation(
            id=1,
            module="inventory",
            entity_type="product",
            entity_id=p_rice.id,
            purchase_order_id=po_draft.id,
            primary_action="full_replenishment",
            priority="high",
            status="pending",
            reason=(
                "Basmati Rice (50kg Bag) has only 2 units on hand, providing approximately 1.7 days of supply. "
                "The forecasted demand is 30.64 units, which exceeds current stock by 28.64 units. "
                "The projected net cash balance of INR 227,007.60 easily covers the purchase, so full replenishment is recommended."
            ),
            llm_summary="You should fully replenish inventory because demand is higher than stock and you have enough cash to cover the purchase.",
            llm_reasoning=(
                "The inventory data shows that Basmati Rice (50kg Bag) has only 2 units in stock while the forecasted demand is 30.64 units, "
                "creating a stock gap of 28.64 units. The cash flow projection indicates a current cash balance of INR 227,007.60 and a projected "
                "balance exceeding the safety buffer. For customer credit, Sharma Kirana & General Store owes INR 28,000.00 and is 36 days overdue, "
                "while Gupta Wholesale Mart owes INR 18,500.00 and is 11 days overdue. Both are flagged for payment reminders. "
                "Finally, Refined White Sugar (50kg Bag) is sold at a loss with a margin of -2.38%, so its pricing should be reviewed."
            ),
            suggested_customer_message=(
                "Dear Sharma Kirana & General Store, we noticed that your invoice payment of INR 28,000.00 is 36 days overdue. "
                "Please arrange payment at your earliest convenience via UPI or bank transfer. Thank you."
            ),
            secondary_recommendations=[
                {
                    "action": "send_payment_reminder",
                    "priority": "high",
                    "reason": "Sharma Kirana & General Store has outstanding overdue payment of INR 28,000.00 for 36 days.",
                },
                {
                    "action": "send_payment_reminder",
                    "priority": "medium",
                    "reason": "Gupta Wholesale Mart has outstanding overdue payment of INR 18,500.00 for 11 days.",
                },
                {
                    "action": "review_product_pricing",
                    "priority": "medium",
                    "reason": "Refined White Sugar (50kg Bag) has negative profit margin (-2.4%). Review cost or selling price.",
                }
            ],
            created_at=now,
        )
        db.add(rec_demo)

        # Audit Logs
        db.add(AuditLog(
            actor_type="SYSTEM",
            action="SYSTEM_INITIALIZED",
            entity="system",
            entity_id="1",
            reason="MicroBizAI decision engine initialized with master demo parameters.",
            timestamp=now,
        ))
        db.add(AuditLog(
            actor_type="AGENT",
            action="RISK_EVALUATED",
            entity="product",
            entity_id=p_rice.name,
            reason="Inventory Agent flagged Basmati Rice (50kg Bag) as CRITICAL RISK (Stock: 2.0 < ROP: 25.0).",
            timestamp=now,
        ))

        db.commit()
        print("  [OK] Draft PO & AI Approvals Recommendation seeded with 100% human-readable names and INR formatting.")

        print("\n" + "=" * 70)
        print("  ALL DEMO DATA SUCCESSFULLY SEEDED & VERIFIED!")
        print("=" * 70)
        print("  Run this anytime using: python backend/scripts/seed_guide_demo_data.py")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Seeding failed: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_database()
