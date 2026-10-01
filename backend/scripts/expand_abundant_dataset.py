"""
backend/scripts/expand_abundant_dataset.py

Expands the MicroBizAI database into a massive, highly abundant dataset:
- 12 Wholesale Suppliers (APMC, FMCG, Dairy, Edible Oils, Personal Care, Confectionery, Spices, Beverages)
- 80 Realistic Products across 8 retail categories (Staples, Flours, Edible Oils, Ghee, Dairy, Spices, FMCG/Biscuits, Home Care)
- 25 Khata Customers across all credit risk profiles (Chronic Delinquent, Overdue, Grace Period, Good Standing, VIP)
- 25 Invoices with payments and aging
- 300+ Sales Transactions spanning 45 rolling days across multiple categories
- 16 Operational Expense lines across utilities, rent, logistics, staff, upkeep
- 8 Purchase Orders across DRAFT, ORDERED, RECEIVED, PARTIAL
- 20 AI Approval Recommendations covering stockout, credit holds, margin fixes, expense spikes, dead stock clearance
"""

import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
import random

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.database import SessionLocal, Base
from backend.app.models import (
    Product, Customer, Sale, Expense, Invoice, Payment,
    Supplier, PurchaseOrder, PurchaseOrderItem, InventoryEvent,
    AgentRun, AuditLog, Recommendation, HumanAction, BusinessSettings
)


def seed_massive_data():
    db = SessionLocal()
    print("=" * 75)
    print("  MICROBIZAI - MASSIVE ABUNDANT DATASET SEEDER (80+ PRODUCTS, 25 CUSTOMERS)")
    print("=" * 75)

    try:
        # 1. Clean existing records
        print("\n[1/7] Cleaning existing transactional & operational records...")
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
        print("  [OK] Cleaned all tables.")

        # 2. Settings
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

        # 3. 12 Wholesale Suppliers
        print("\n[3/7] Registering 12 Diverse Wholesale Suppliers...")
        suppliers_data = [
            (1, "Punjab Agro Food Wholesale", "Gurpreet Singh", "+919811223344", "orders@punjabagro.com", "APMC Yard Gate 2, Delhi", "Grains & Staples"),
            (2, "Mother Dairy Processing Unit", "Rajesh Verma", "+919822334455", "dispatch@motherdairy.com", "Industrial Area Sector 4, Noida", "Dairy & Perishables"),
            (3, "Fortune & Adani Wilmar Dist.", "Amit Shah", "+919833445566", "supplies@adaniwilmar.com", "Wholesale Depot 12, Surat", "Edible Oils & Ghee"),
            (4, "Hindustan Unilever Depot", "Sanjay Kulkarni", "+919844556677", "orders@hul-dist.com", "Ring Road Industrial Estate, Bengaluru", "Personal & Home Care"),
            (5, "Tata Consumer Products Depot", "Venkatesh Rao", "+919855667788", "supplies@tataconsumer.com", "Yeshwantpur Market Yard, Bengaluru", "Beverages & Salt"),
            (6, "Parle & Britannia Agency", "Mahesh Agarwal", "+919866778899", "dispatch@parledist.com", "Peenya Industrial Area, Bengaluru", "Bakery & Confectionery"),
            (7, "ITC Foods & Staples Depot", "Anand Sharma", "+919877889900", "orders@itc-dist.com", "Whitefield Logistics Hub, Bengaluru", "Atta, Snacks & Biscuits"),
            (8, "Nestle India Regional Agency", "Rohit Malhotra", "+919888990011", "dispatch@nestle-agency.in", "Bommasandra Industrial Area, Bengaluru", "Noodles, Coffee & Dairy"),
            (9, "Everest & MDH Spices Wholesale", "Kantilal Patel", "+919899001122", "orders@spicesmandi.com", "APMC Spice Yard, Vashi Navi Mumbai", "Spices & Condiments"),
            (10, "Haldiram Snacks & Sweets Dist.", "Govind Bansal", "+919810112233", "orders@haldirams-agency.com", "Okhla Phase 2, New Delhi", "Packaged Snacks & Namkeen"),
            (11, "Godrej Consumer Products Ltd", "Manoj Kadam", "+919821223344", "depot@godrejcp.com", "Thane Logistics Park, Mumbai", "Home Insecticides & Soaps"),
            (12, "Dabur India Consumer Care", "Sunil Joshi", "+919832334455", "dist@dabur-agency.com", "Ghaziabad Wholesale Hub, UP", "Health, Juices & Honey"),
        ]
        for sid, name, cname, phone, email, addr, cat in suppliers_data:
            db.add(Supplier(
                id=sid, name=name, contact_name=cname, phone=phone, email=email, address=addr, category=cat
            ))
        db.commit()
        print("  [OK] 12 Wholesale Suppliers registered.")

        # 4. 80 Realistic Products
        print("\n[4/7] Seeding 80 Realistic Products across 8 Retail Departments...")
        
        # Format: (sku, name, sp, cp, stock, rop, safety, lead, stype, assort, promo)
        raw_products = [
            # Grains, Rice & Pulses (12 SKUs)
            ("GRO-RICE-001", "Basmati Rice (50kg Bag)", 1350.0, 1100.0, 2.0, 25.0, 5.0, 2, "a", "c", False), # Critical Stockout
            ("GRO-RICE-002", "Kolam Raw Steamed Rice (25kg Bag)", 1450.0, 1250.0, 35.0, 15.0, 4.0, 2, "a", "b", False),
            ("GRO-RICE-003", "Sona Masoori Bullet Rice (25kg Bag)", 1380.0, 1190.0, 5.0, 15.0, 3.0, 2, "a", "b", False), # Low Stock
            ("GRO-RICE-004", "Ponni Boiled Rice (25kg Bag)", 1280.0, 1080.0, 22.0, 12.0, 3.0, 2, "a", "a", False),
            ("GRO-RICE-005", "Fortune Special Biryani Rice (5kg Pack)", 520.0, 430.0, 14.0, 8.0, 2.0, 2, "a", "b", True),
            ("GRO-PUL-007", "Desi Toor / Arhar Dal (1kg Pack)", 165.0, 142.0, 4.0, 18.0, 4.0, 2, "a", "a", False), # Low Stock
            ("GRO-PUL-008", "Yellow Moong Dal Split (1kg Pack)", 135.0, 115.0, 28.0, 12.0, 3.0, 2, "a", "a", False),
            ("GRO-PUL-009", "Chana Dal Premium (1kg Pack)", 95.0, 78.0, 32.0, 15.0, 3.0, 2, "a", "a", False),
            ("GRO-PUL-010", "Urad Dal Gota Whole White (1kg Pack)", 155.0, 132.0, 6.0, 14.0, 3.0, 2, "a", "a", False), # Low Stock
            ("GRO-PUL-011", "Kabuli Chana Big Chickpeas (1kg Pack)", 140.0, 118.0, 19.0, 10.0, 2.0, 2, "a", "a", False),
            ("GRO-PUL-012", "Chitra Kashmiri Rajma (1kg Pack)", 160.0, 134.0, 16.0, 8.0, 2.0, 2, "a", "a", False),
            ("GRO-PUL-013", "Green Moong Whole (1kg Pack)", 125.0, 102.0, 24.0, 10.0, 2.0, 2, "a", "a", False),

            # Atta, Flours & Sooji (10 SKUs)
            ("GRO-ATTA-003", "Chakki Fresh Atta (10kg Pack)", 420.0, 360.0, 45.0, 20.0, 5.0, 2, "a", "a", False),
            ("GRO-ATTA-004", "Aashirvaad Shudh Chakki Atta (5kg Pack)", 245.0, 215.0, 3.0, 15.0, 4.0, 2, "a", "a", False), # Low Stock
            ("GRO-ATTA-005", "Aashirvaad Select Sharbati Atta (5kg)", 295.0, 255.0, 18.0, 10.0, 2.0, 2, "a", "b", False),
            ("GRO-ATTA-006", "Fortune Chakki Fresh Atta (10kg Pack)", 395.0, 340.0, 25.0, 12.0, 3.0, 2, "a", "a", False),
            ("GRO-FLR-005", "Besan Premium Gram Flour (1kg Pack)", 105.0, 88.0, 18.0, 8.0, 2.0, 2, "a", "a", False),
            ("GRO-FLR-006", "Maida Fine Wheat Flour (1kg Pack)", 52.0, 42.0, 20.0, 8.0, 2.0, 2, "a", "a", False),
            ("GRO-FLR-007", "Bombay Sooji / Rava (1kg Pack)", 58.0, 47.0, 24.0, 10.0, 2.0, 2, "a", "a", False),
            ("GRO-FLR-008", "Roasted Vermicelli / Seviyan (500g)", 45.0, 36.0, 30.0, 12.0, 2.0, 1, "a", "a", False),
            ("GRO-FLR-009", "Thick Poha / Avalakki (1kg Pack)", 62.0, 49.0, 22.0, 10.0, 2.0, 2, "a", "a", False),
            ("GRO-FLR-010", "Rice Flour / Akki Hittu (1kg Pack)", 55.0, 44.0, 15.0, 8.0, 2.0, 2, "a", "a", False),

            # Edible Oils & Pure Ghee (10 SKUs)
            ("OIL-SNF-005", "Sunflower Oil (15L Tin)", 1950.0, 1820.0, 12.0, 8.0, 2.0, 3, "c", "c", False),
            ("OIL-SNF-010", "Fortune Sunlite Sunflower Oil (1L Pouch)", 145.0, 128.0, 65.0, 25.0, 6.0, 2, "c", "b", False),
            ("OIL-MST-011", "Fortune Kachi Ghani Mustard Oil (1L Pouch)", 158.0, 138.0, 42.0, 18.0, 4.0, 2, "c", "b", False),
            ("OIL-GND-012", "Gemini Filtered Groundnut Oil (1L Pouch)", 185.0, 162.0, 20.0, 10.0, 3.0, 2, "c", "b", False),
            ("OIL-RBR-013", "Saffola Gold Rice Bran Blended (1L Pouch)", 195.0, 172.0, 4.0, 15.0, 3.0, 2, "c", "b", False), # Low Stock
            ("OIL-GHE-014", "Amul Pure Cow Ghee (1L Tin)", 680.0, 610.0, 16.0, 8.0, 2.0, 2, "c", "c", False),
            ("OIL-GHE-015", "Nandini Pure Cow Ghee (500ml Pouch)", 340.0, 305.0, 22.0, 10.0, 2.0, 1, "c", "b", False),
            ("OIL-GHE-016", "Mother Dairy Special Ghee (1L Pet Jar)", 660.0, 595.0, 10.0, 6.0, 2.0, 2, "c", "c", False),
            ("OIL-MST-017", "Dhara Mustard Oil Bottle (1L)", 165.0, 144.0, 18.0, 8.0, 2.0, 2, "c", "a", False),
            ("OIL-COCO-018", "Parachute Pure Coconut Oil (500ml)", 175.0, 150.0, 28.0, 12.0, 2.0, 2, "c", "b", False),

            # Dairy & Fresh Perishables (10 SKUs)
            ("DAIRY-MILK-002", "Fresh Dairy Milk (1L Pouch)", 66.0, 58.0, 3.0, 30.0, 8.0, 1, "b", "a", False), # Critical Daily
            ("DAIRY-MILK-003", "Amul Taaza Homogenised Toned Milk (1L)", 72.0, 64.0, 24.0, 15.0, 4.0, 1, "b", "a", False),
            ("DAIRY-MILK-004", "Amul Gold Full Cream Milk (1L Pouch)", 78.0, 69.0, 5.0, 20.0, 5.0, 1, "b", "a", False), # Low Stock
            ("DAIRY-MILK-005", "Nandini Toned Fresh Milk (500ml)", 24.0, 21.0, 8.0, 25.0, 6.0, 1, "b", "a", False), # Low Stock
            ("DAIRY-BTR-015", "Amul Salted Table Butter (500g)", 285.0, 252.0, 14.0, 6.0, 2.0, 1, "b", "a", False),
            ("DAIRY-BTR-016", "Amul Table Butter (100g Carton)", 58.0, 50.0, 36.0, 15.0, 3.0, 1, "b", "a", False),
            ("DAIRY-CRD-016", "Nandini Fresh Curd / Dahi (500g Pouch)", 32.0, 27.0, 3.0, 15.0, 4.0, 1, "b", "a", False), # Low Stock
            ("DAIRY-PNR-017", "Fresh Malai Paneer (200g Pack)", 95.0, 80.0, 4.0, 12.0, 3.0, 1, "b", "a", False), # Low Stock
            ("DAIRY-CHS-018", "Amul Cheese Slices (200g - 10 Slices)", 145.0, 126.0, 18.0, 8.0, 2.0, 1, "b", "b", False),
            ("DAIRY-EGG-019", "Farm Fresh White Eggs (Crate of 30)", 210.0, 180.0, 6.0, 12.0, 3.0, 1, "b", "a", False), # Low Stock

            # Sweeteners & Beverages (8 SKUs)
            ("GRO-SUG-004", "Refined White Sugar (50kg Bag)", 2100.0, 2150.0, 15.0, 10.0, 2.0, 3, "a", "c", False), # Loss-Making Margin Test!
            ("GRO-SUG-005", "Madhur Pure Crystal Sugar (5kg Bag)", 260.0, 235.0, 25.0, 10.0, 3.0, 2, "a", "b", False),
            ("GRO-JAG-018", "Organic Pure Jaggery Powder (1kg Pack)", 90.0, 74.0, 16.0, 8.0, 2.0, 2, "a", "a", False),
            ("BEV-TEA-008", "Premium CTC Assam Tea (1kg Pack)", 450.0, 310.0, 25.0, 10.0, 3.0, 3, "d", "c", False), # High Margin Champion
            ("BEV-TEA-019", "Tata Tea Premium Strong Blend (500g)", 260.0, 220.0, 22.0, 10.0, 2.0, 2, "d", "b", False),
            ("BEV-TEA-020", "Taj Mahal Rich Tea Leaves (250g Box)", 195.0, 165.0, 15.0, 8.0, 2.0, 2, "d", "a", False),
            ("BEV-COF-020", "Bru Instant Coffee Powder (100g Jar)", 185.0, 155.0, 12.0, 5.0, 2.0, 2, "d", "a", False),
            ("BEV-COF-021", "Nescafe Classic Instant Coffee (50g Jar)", 165.0, 138.0, 18.0, 8.0, 2.0, 2, "d", "a", False),

            # Spices, Salts & Condiments (10 SKUs)
            ("SPC-SALT-006", "Tata Salt Vacuum Evaporated (1kg Pack)", 28.0, 22.0, 180.0, 50.0, 15.0, 1, "d", "a", False), # Overstocked
            ("SPC-SALT-007", "Tata Rock Salt Sendha Namak (1kg)", 45.0, 36.0, 25.0, 10.0, 2.0, 2, "d", "a", False),
            ("SPC-TUR-022", "Everest Pure Turmeric Powder (500g)", 140.0, 116.0, 28.0, 10.0, 2.0, 2, "d", "b", False),
            ("SPC-CHL-023", "MDH Deggi Mirch Red Chilli (500g)", 240.0, 202.0, 20.0, 8.0, 2.0, 2, "d", "b", False),
            ("SPC-COR-024", "Catch Coriander / Dhaniya Powder (500g)", 135.0, 112.0, 22.0, 8.0, 2.0, 2, "d", "a", False),
            ("SPC-GAR-025", "Everest Royal Garam Masala (100g Box)", 92.0, 76.0, 32.0, 12.0, 3.0, 2, "d", "a", False),
            ("SPC-CHI-026", "MDH Kitchen King All-Rounder (100g)", 88.0, 72.0, 25.0, 10.0, 2.0, 2, "d", "a", False),
            ("SPC-JEER-027", "Unpolished Cumin Seeds / Jeera (200g)", 130.0, 108.0, 18.0, 8.0, 2.0, 2, "d", "a", False),
            ("SPC-MUST-028", "Small Black Mustard Seeds / Rai (200g)", 42.0, 33.0, 25.0, 10.0, 2.0, 2, "d", "a", False),
            ("SPC-HING-029", "LG Compounded Asafoetida Powder (50g)", 68.0, 55.0, 30.0, 10.0, 2.0, 2, "d", "a", False),

            # Biscuits, Snacks & Instant Foods (10 SKUs)
            ("FMCG-BIS-007", "Parle-G Gold Biscuits (Carton of 48)", 280.0, 240.0, 120.0, 20.0, 5.0, 2, "a", "b", False), # Overstocked capital lockup
            ("FMCG-NDL-009", "Maggi 2-Minute Masala Noodles (Pack 24)", 330.0, 325.0, 18.0, 15.0, 4.0, 2, "a", "b", False), # Razor-thin margin (+1.5%)
            ("FMCG-NDL-010", "Sunfeast YiPPee! Masala Noodles (Pack 12)", 160.0, 138.0, 24.0, 10.0, 2.0, 2, "a", "a", False),
            ("FMCG-BIS-021", "Britannia Good Day Butter Cookies (Carton 36)", 360.0, 310.0, 28.0, 12.0, 3.0, 2, "a", "b", False),
            ("FMCG-BIS-022", "Cadbury Oreo Vanilla Crème (Pack 24)", 240.0, 204.0, 30.0, 12.0, 2.0, 2, "a", "b", False),
            ("FMCG-BIS-023", "Sunfeast Dark Fantasy Choco Fills (Pack 15)", 450.0, 380.0, 16.0, 8.0, 2.0, 2, "a", "b", False),
            ("FMCG-SNK-024", "Haldiram Aloo Bhujia Namkeen (1kg Pouch)", 240.0, 198.0, 35.0, 12.0, 3.0, 2, "a", "b", False),
            ("FMCG-SNK-025", "Haldiram Khatta Meetha Mixture (1kg)", 230.0, 190.0, 26.0, 10.0, 2.0, 2, "a", "b", False),
            ("FMCG-SNK-026", "Kurkure Masala Munch (Pack of 20 x ₹10)", 190.0, 165.0, 40.0, 15.0, 3.0, 1, "a", "a", False),
            ("FMCG-SNK-027", "Lay's India's Magic Masala (Pack 20 x ₹10)", 190.0, 165.0, 38.0, 15.0, 3.0, 1, "a", "a", False),

            # Home Care & Personal Hygiene (10 SKUs)
            ("HPC-DET-030", "Surf Excel Easy Wash Detergent (1kg Pack)", 140.0, 122.0, 32.0, 12.0, 3.0, 2, "d", "c", False),
            ("HPC-DET-031", "Tide Plus Extra Power Detergent (1kg)", 115.0, 98.0, 28.0, 10.0, 2.0, 2, "d", "b", False),
            ("HPC-DET-032", "Rin Detergent Bar (Pack of 4 x 250g)", 80.0, 68.0, 45.0, 15.0, 4.0, 2, "d", "a", False),
            ("HPC-DSH-033", "Vim Dishwash Gel Lemon (500ml Bottle)", 125.0, 105.0, 26.0, 10.0, 2.0, 2, "d", "b", False),
            ("HPC-DSH-034", "Vim Dishwash Bar (Pack of 3 x 200g)", 60.0, 50.0, 50.0, 15.0, 3.0, 2, "d", "a", False),
            ("HPC-CLN-035", "Harpic Power Plus Toilet Cleaner (1L)", 195.0, 168.0, 20.0, 8.0, 2.0, 2, "d", "b", False),
            ("HPC-CLN-036", "Lizol Disinfectant Floor Cleaner Citrus (1L)", 210.0, 180.0, 18.0, 8.0, 2.0, 2, "d", "b", False),
            ("HPC-SOP-037", "Dettol Original Germ Protection Soap (Pack 4)", 175.0, 148.0, 24.0, 10.0, 2.0, 2, "d", "b", False),
            ("HPC-SOP-038", "Lifebuoy Total Germ Protection (Pack 4)", 135.0, 114.0, 30.0, 10.0, 2.0, 2, "d", "a", False),
            ("HPC-PST-039", "Colgate Strong Teeth Toothpaste (500g Saver)", 245.0, 210.0, 22.0, 10.0, 2.0, 2, "d", "b", False),
        ]

        products_map = {}
        for (sku, name, sp, cp, stock, rop, safety, lead, stype, assort, promo) in raw_products:
            pid = str(uuid.uuid4())
            p = Product(
                id=pid,
                sku=sku,
                name=name,
                selling_price=sp,
                cost_price=cp,
                current_stock=stock,
                reorder_level=rop,
                safety_stock=safety,
                lead_time_days=lead,
                store_type=stype,
                assortment=assort,
                competition_distance=450.0,
                promo_active=promo,
            )
            db.add(p)
            products_map[sku] = p
        db.commit()
        print(f"  [OK] {len(raw_products)} Products created across all retail departments.")

        # 5. 25 Khata Customers across all debt states
        print("\n[5/7] Seeding 25 Khata Customers with realistic debt profiles...")
        today = date.today()
        customers_data = [
            ("Sharma Mess & Catering", "+919811002201", "sharma.mess@gmail.com", "Near Bus Stand Market", 15000.0, 4850.0, 68),  # Chronic Delinquency
            ("Gupta General Stores", "+919811002202", "gupta.store@yahoo.com", "Main Road Corner", 10000.0, 3400.0, 52),     # Severe Overdue
            ("Vikram Singh (Contractor)", "+919811002203", "vikram.contract@gmail.com", "PWD Colony 4th Block", 12000.0, 8200.0, 64), # Chronic Delinquent
            ("Chai Point Express Stall", "+919811002204", "chaipoint.stall@gmail.com", "Auto Stand Metro Gate", 6000.0, 4800.0, 15), # Commercial Tea Stall Khata
            ("Pooja Sweets & Bakery", "+919811002205", "poojasweets@rediffmail.com", "Temple Road Cross", 8000.0, 6500.0, 22),     # Commercial Bakery Khata
            ("Ananya Daily Needs", "+919811002206", "ananya.daily@gmail.com", "Green Glen Layout", 5000.0, 3200.0, 4),             # Courtesy Grace
            ("Sri Venkateshwara Bakery", "+919811002207", "venkatesh.bkr@gmail.com", "Industrial Gate 3", 20000.0, 14200.0, -5),   # Grace Period Active (Due in 5d)
            ("Patel Provision Store", "+919811002208", "patel.stores@gmail.com", "APMC Yard Shop 14", 15000.0, 9500.0, -10),        # Active Normal
            ("Verma Caterers & Events", "+919811002209", "verma.events@gmail.com", "Ring Road Palace Hall", 25000.0, 0.0, 0),       # 100% Repaid VIP
            ("Kavita Reddy (Regular Walk-in)", "+919811002210", "kavita.r@gmail.com", "Teacher's Colony", 3000.0, 0.0, 0),         # Fully Paid Regular
            ("Bawarchi Biryani Centre", "+919811002211", "bawarchi.bng@gmail.com", "Food Street Cross 2", 18000.0, 7600.0, 42),    # Overdue Commercial
            ("Ramesh Kumar (Teacher)", "+919811002212", "ramesh.edu@gov.in", "Govt School Quarters", 5000.0, 450.0, -12),          # Active Good Standing
            ("Sunita Patil (Daily Khata)", "+919811002213", "sunita.patil@gmail.com", "Railway Layout 2nd Cross", 4000.0, 1850.0, 18),
            ("Udupi Sagar Hotel", "+919811002214", "udupisagar@gmail.com", "Station Road Front", 30000.0, 18500.0, 35),            # Overdue Commercial Hotel
            ("Kiran Medical Store", "+919811002215", "kiran.pharma@gmail.com", "Hospital Road Gate 1", 8000.0, 2100.0, -8),
            ("Nagesh Rao (Postman)", "+919811002216", "nagesh.post@gmail.com", "Post Office Colony", 3500.0, 800.0, -14),
            ("Annapoorna Tiffin Centre", "+919811002217", "annapoorna.tc@gmail.com", "Market Circle North", 12000.0, 5400.0, 8),
            ("Deepak Electricals", "+919811002218", "deepak.elec@gmail.com", "Commercial Complex 2", 6000.0, 0.0, 0),
            ("Praveen Kumar (Driver)", "+919811002219", "praveen.cab@gmail.com", "Auto Nagar Line 3", 3000.0, 2400.0, 58),       # Severe Personal Overdue
            ("Meenakshi Tailors", "+919811002220", "meenakshi.tailors@gmail.com", "Ladies Market Road", 4500.0, 1200.0, 12),
            ("Sri Krishna Milk Parlour", "+919811002221", "krishna.milk@gmail.com", "Booth No 4 Main Gate", 10000.0, 4100.0, -4),
            ("Ganesh Fast Food Corner", "+919811002222", "ganesh.fastfood@gmail.com", "College Road Corner", 8000.0, 5900.0, 28),
            ("Lakshmi Beauty Parlour", "+919811002223", "lakshmi.beauty@gmail.com", "1st Floor Shopping Block", 5000.0, 1500.0, -6),
            ("Mohammed Zameer (Plumber)", "+919811002224", "zameer.plumb@gmail.com", "Old Town Masjid Lane", 3500.0, 2900.0, 72), # Chronic Delinquent
            ("Raghavendra Xerox & Stationers", "+919811002225", "raghu.xerox@gmail.com", "Opposite City College", 7000.0, 0.0, 0),
        ]

        customers_list = []
        for idx, (cname, phone, email, addr, lim, bal, overdue_days) in enumerate(customers_data, start=1):
            cid = str(uuid.uuid4())
            c = Customer(
                id=cid,
                name=cname,
                phone=phone,
                email=email,
            )
            db.add(c)
            customers_list.append((c, bal, overdue_days))
        db.commit()

        # Seed Invoices for each customer
        inv_id_counter = 1
        for c, bal, overdue_days in customers_list:
            if bal > 0:
                due = today - timedelta(days=overdue_days) if overdue_days > 0 else today + timedelta(days=abs(overdue_days))
                inv = Invoice(
                    id=inv_id_counter,
                    customer_id=c.id,
                    invoice_amount=bal,
                    amount_paid=0.0,
                    due_date=due,
                    created_date=due - timedelta(days=30),
                    status="unpaid",
                )
                db.add(inv)
                inv_id_counter += 1
            else:
                inv = Invoice(
                    id=inv_id_counter,
                    customer_id=c.id,
                    invoice_amount=4500.0,
                    amount_paid=4500.0,
                    due_date=today - timedelta(days=5),
                    created_date=today - timedelta(days=35),
                    status="paid",
                )
                db.add(inv)
                inv_id_counter += 1
        db.commit()
        print("  [OK] 25 Customers and Invoices seeded.")

        # 6. Seed 350+ Sales Transactions across 45 rolling days
        print("\n[6/7] Seeding 350+ Realistic Sales Transactions (Rolling 45 Days)...")
        all_prods = list(products_map.values())
        random.seed(42)

        for day_offset in range(1, 46):
            s_date = today - timedelta(days=day_offset)
            # 8 to 12 sales per day
            num_sales = random.randint(8, 14)
            for _ in range(num_sales):
                p = random.choice(all_prods)
                qty = random.choice([1, 2, 3, 5, 10, 20]) if p.selling_price < 200 else random.choice([1, 2, 3])
                tot = round(qty * p.selling_price, 2)
                # 40% walk-in cash, 60% customer
                chosen_cust = random.choice(customers_list)[0].id if random.random() > 0.4 else None

                db.add(Sale(
                    product_id=p.id,
                    customer_id=chosen_cust,
                    store_id=1,
                    date=s_date,
                    quantity=float(qty),
                    unit_price=p.selling_price,
                    total_amount=tot,
                ))

        # 16 Operational Expenses
        print("  Seeding 16 Operational Expenses...")
        expenses_data = [
            ("Rent & Lease", 25000.0, 25000.0, "Monthly store premise rent (STABLE 0% VARIANCE)"),
            ("Electricity & Utilities", 8450.0, 5500.0, "Cold storage and store lighting (CRITICAL SPIKE +53.6%)"),
            ("Logistics & Transport", 6800.0, 6500.0, "APMC wholesale mandi tempo transport (NORMAL +4.6%)"),
            ("Packaging & Bags", 4200.0, 4000.0, "Biodegradable bags and tape supplies (NORMAL +5.0%)"),
            ("Digital Marketing", 3500.0, 0.0, "Local WhatsApp Catalog & Google My Business Ads (NEW SPEND)"),
            ("Store Upkeep & Sanitation", 2800.0, 2600.0, "Sanitization, pest control & billing rolls (NORMAL +7.7%)"),
            ("Staff Wages (Cashier)", 18000.0, 18000.0, "Store cashier monthly salary (FIXED 0% VARIANCE)"),
            ("Staff Wages (Helper)", 12000.0, 12000.0, "Store stock loader and delivery helper salary (FIXED)"),
            ("Water Tanker Supply", 1600.0, 1500.0, "Potable drinking water refill for store (NORMAL +6.7%)"),
            ("Freezer Maintenance", 3200.0, 1200.0, "Emergency dairy deep freezer gas charging (+166.7% SPIKE)"),
            ("Generator Diesel", 2400.0, 2200.0, "Backup power fuel for summer power cuts (NORMAL +9.1%)"),
            ("Broadband & POS SIM", 999.0, 999.0, "Airtel Fiber & POS terminal data plan (FIXED)"),
            ("Municipal Trade License", 2500.0, 2500.0, "BBMP annual retail trade fee amortized (FIXED)"),
            ("CCTV & Security", 1200.0, 1200.0, "Cloud backup subscription for 8 security cameras (FIXED)"),
            ("Paper Bags & Jute Sacks", 1800.0, 1700.0, "Eco-friendly bulk grain packaging supplies (NORMAL +5.9%)"),
            ("Festival Bonus & Sweets", 5000.0, 0.0, "Annual festive goodwill bonus for staff (NOVEL SEASONAL)"),
        ]
        for cat, curr, prior, desc in expenses_data:
            db.add(Expense(
                category=cat,
                current_period_amount=curr,
                prior_period_amount=prior,
                description=desc,
                date=today - timedelta(days=5),
            ))
        db.commit()
        print("  [OK] 350+ Sales and 16 Expenses recorded.")

        # 7. Seed 8 Purchase Orders & 20 Multi-Agent Recommendations
        print("\n[7/7] Seeding 8 Purchase Orders and 20 AI Approvals Recommendations...")
        now = datetime.now(timezone.utc)

        # Pre-seed 8 POs
        p_rice = products_map["GRO-RICE-001"]
        p_milk = products_map["DAIRY-MILK-002"]
        p_atta = products_map["GRO-ATTA-004"]
        p_curd = products_map["DAIRY-CRD-016"]
        p_oil = products_map["OIL-RBR-013"]
        p_toor = products_map["GRO-PUL-007"]

        pos_data = [
            (1, "PO-2026-0001", 1, "DRAFT", "HIGH", 30800.0, "Basmati Rice 50kg wholesale replenishment"),
            (2, "PO-2026-0002", 2, "DRAFT", "HIGH", 2900.0, "Daily perishable replenishment Fresh Dairy Milk"),
            (3, "PO-2026-0003", 7, "DRAFT", "HIGH", 8600.0, "Aashirvaad Shudh Chakki Atta 5kg restock"),
            (4, "PO-2026-0004", 2, "ORDERED", "MEDIUM", 1350.0, "Nandini Fresh Curd 500g standing order"),
            (5, "PO-2026-0005", 3, "ORDERED", "MEDIUM", 5160.0, "Saffola Gold 1L replenishment order"),
            (6, "PO-2026-0006", 1, "RECEIVED", "LOW", 14200.0, "Desi Toor Dal wholesale delivery received"),
            (7, "PO-2026-0007", 5, "RECEIVED", "LOW", 9300.0, "Tata Tea Premium & Salt monthly consignment"),
            (8, "PO-2026-0008", 4, "PARTIAL", "LOW", 18500.0, "Surf Excel & Vim Gel FMCG consignment partial dispatch"),
        ]
        for poid, ponum, supid, st, prio, tot, reason in pos_data:
            po = PurchaseOrder(
                id=poid, po_number=ponum, supplier_id=supid, status=st, priority=prio, total_amount=tot, reason=reason, created_at=now
            )
            db.add(po)
        db.commit()

        # Add PO items
        db.add(PurchaseOrderItem(purchase_order_id=1, product_id=p_rice.id, quantity=28.0, unit_cost=1100.0, total_cost=30800.0))
        db.add(PurchaseOrderItem(purchase_order_id=2, product_id=p_milk.id, quantity=50.0, unit_cost=58.0, total_cost=2900.0))
        db.add(PurchaseOrderItem(purchase_order_id=3, product_id=p_atta.id, quantity=40.0, unit_cost=215.0, total_cost=8600.0))
        db.commit()

        # Seed 20 Varied AI Recommendations
        recs_data = [
            # 1. Critical Stockout (Basmati Rice)
            (1, "inventory", "product", p_rice.id, 1, "full_replenishment", "critical", "pending",
             "Inventory alert (CRITICAL): 'Basmati Rice (50kg Bag)' stock is 2.0 (coverage: 1.2 days, ROP: 25.0). Order 28 units.",
             "Critical stockout imminent. Replenish 28 units immediately via Punjab Agro Wholesale.",
             "Basmati Rice has 2 bags on shelves vs 30.6 unit 7-day demand. Complete stockout in 36 hours."),

            # 2. Perishable Milk Daily Order
            (2, "inventory", "product", p_milk.id, 2, "full_replenishment", "high", "pending",
             "Inventory alert (HIGH): 'Fresh Dairy Milk (1L Pouch)' stock is 3.0 (coverage: 0.8 days, ROP: 30.0). Order 50 units.",
             "Morning dairy depletion. Immediate replenishment needed to prevent daily lost sales.",
             "Milk has 20 pouches/day velocity. Current 3 pouches will run out before noon. Order 50 units from Mother Dairy."),

            # 3. Fast-Moving Atta Restock
            (3, "inventory", "product", p_atta.id, 3, "full_replenishment", "high", "pending",
             "Inventory alert (HIGH): 'Aashirvaad Shudh Chakki Atta (5kg Pack)' stock is 3.0 (ROP: 15.0). Order 40 units.",
             "Fast-moving staple reaching critical depletion. Replenish 40 packs @ ₹215.",
             "Weekly demand is 28 units. Current 3 packs will be exhausted within 24 hours. Wholesale discount available for 40 units."),

            # 4. Toor Dal Near-Depletion
            (4, "inventory", "product", p_toor.id, None, "full_replenishment", "high", "pending",
             "Inventory alert (HIGH): 'Desi Toor / Arhar Dal (1kg Pack)' stock is 4.0 (ROP: 18.0). Order 30 units.",
             "Core pulse staple near stockout. Draft replenishment order of 30 units.",
             "High-frequency staple with 4 units remaining. Lead time 2 days. Reorder now to avoid customer walkouts."),

            # 5. Saffola Gold Low Stock
            (5, "inventory", "product", p_oil.id, 5, "full_replenishment", "medium", "pending",
             "Inventory alert (MEDIUM): 'Saffola Gold Rice Bran (1L)' stock is 4.0 (ROP: 15.0). Order 25 units.",
             "Premium edible oil below reorder threshold. Approve standing replenishment.",
             "High-margin premium oil category. Stock is 4 pouches against safety buffer of 3."),

            # 6. Chronic Delinquent Credit Hold (Sharma Mess)
            (6, "khata", "customer", customers_list[0][0].id, None, "pause_credit", "critical", "pending",
             "Khata risk alert (CRITICAL): 'Sharma Mess & Catering' has ₹4,850.00 overdue by 68 days (limit: 30 days).",
             "Halt uncollateralized credit and issue legal 48-hour formal collection notice.",
             "Customer has exceeded statutory 30-day limit by 38 days without partial payment. High default probability."),

            # 7. Chronic Delinquent Credit Hold (Vikram Singh)
            (7, "khata", "customer", customers_list[2][0].id, None, "pause_credit", "critical", "pending",
             "Khata risk alert (CRITICAL): 'Vikram Singh (Contractor)' balance ₹8,200.00 is 64 days overdue.",
             "Freeze further store credit. Issue formal WhatsApp UPI collection link.",
             "Contractor credit aging beyond 60 days. Risk of complete bad debt write-off if unaddressed."),

            # 8. Severe Overdue Credit Hold (Gupta General Stores)
            (8, "khata", "customer", customers_list[1][0].id, None, "pause_credit", "high", "pending",
             "Khata risk alert (HIGH): 'Gupta General Stores' balance ₹3,400.00 is 52 days overdue.",
             "Automated credit hold. Dispatch polite automated payment reminder link.",
             "Outstanding invoice overdue by 22 days past limit. Require ₹1,500 down payment before next dispatch."),

            # 9. Courtesy Khata SMS Reminder (Bawarchi Biryani)
            (9, "khata", "customer", customers_list[10][0].id, None, "payment_reminder", "medium", "pending",
             "Khata risk alert (MEDIUM): 'Bawarchi Biryani Centre' balance ₹7,600.00 is 42 days overdue.",
             "Send polite WhatsApp collection reminder with UPI QR code link.",
             "B2B restaurant buyer with good historical volume. Friendly reminder prevents aging into bad debt."),

            # 10. Courtesy Khata SMS Reminder (Udupi Sagar Hotel)
            (10, "khata", "customer", customers_list[13][0].id, None, "payment_reminder", "medium", "pending",
             "Khata risk alert (MEDIUM): 'Udupi Sagar Hotel' balance ₹18,500.00 is 35 days overdue.",
             "Initiate weekly ledger reconciliation with hotel procurement manager.",
             "High-volume commercial account. Current invoice due by 5 days; early touchpoint accelerates recovery."),

            # 11. Overdue Auto-SMS (Pooja Sweets)
            (11, "khata", "customer", customers_list[4][0].id, None, "payment_reminder", "medium", "pending",
             "Khata alert (MEDIUM): 'Pooja Sweets & Bakery' balance ₹6,500.00 is 22 days overdue.",
             "Send automated SMS balance reminder before month-end statement closure.",
             "Commercial sweet shop invoice approaching 30-day default window."),

            # 12. Electricity Bill Spike Anomaly
            (12, "expense", "expense_category", "Electricity & Utilities", None, "investigate_anomaly", "high", "pending",
             "Expense anomaly alert (HIGH): 'Electricity & Utilities' ₹8,450.00 is +53.6% above prior period (₹5,500.00).",
             "Flag for immediate tariff meter audit and cold storage refrigeration leak check.",
             "Expense spike exceeds 30% anomaly threshold. Check compressor seal on Nandini dairy display cooler."),

            # 13. Deep Freezer Maintenance Spike
            (13, "expense", "expense_category", "Freezer Maintenance", None, "review_expense", "high", "pending",
             "Expense anomaly alert (HIGH): 'Freezer Maintenance' ₹3,200.00 is +166.7% above baseline (₹1,200.00).",
             "Review emergency technician repair invoice and obtain itemized parts warranty.",
             "One-off gas charging expense exceeds baseline by ₹2,000. Ensure warranty certificate is archived."),

            # 14. Novel Spending Category Audit (Digital Marketing)
            (14, "expense", "expense_category", "Digital Marketing", None, "audit_spending", "medium", "pending",
             "Expense alert (MEDIUM): 'Digital Marketing' ₹3,500.00 recorded with zero prior period baseline.",
             "Verify WhatsApp Catalog and Google My Business promotional ROI.",
             "Novel expense category flagged by Expense Auditor. Verify local flyer distribution receipts."),

            # 15. Negative Margin Price Correction (Sugar 50kg)
            (15, "pricing", "product", products_map["GRO-SUG-004"].id, None, "price_adjustment", "high", "pending",
             "Profitability alert (HIGH): 'Refined White Sugar (50kg Bag)' margin is negative (-2.38%, loss ₹50.00/bag).",
             "Increase selling price from ₹2,100.00 to ₹2,250.00 to restore positive 4.4% gross margin.",
             "Current retail price ₹2,100 is below wholesale procurement cost ₹2,150. Immediate markup correction required."),

            # 16. Razor-Thin Margin Markup (Maggi Noodles)
            (16, "pricing", "product", products_map["FMCG-NDL-009"].id, None, "price_adjustment", "medium", "pending",
             "Profitability alert (MEDIUM): 'Maggi Noodles 24-pack' margin is razor-thin (+1.51%, unit profit ₹5.00).",
             "Adjust retail price from ₹330.00 to ₹345.00 or bundle with ketchup for 8.5% margin.",
             "Selling price ₹330 on cost ₹325 barely covers credit card/POS gateway charges. Bundle promotion recommended."),

            # 17. Dead Stock Capital Lockup Clearance (Parle-G)
            (17, "inventory", "product", products_map["FMCG-BIS-007"].id, None, "promotional_discount", "medium", "pending",
             "Inventory alert (MEDIUM): 'Parle-G Gold (Carton 48)' stock is 120 units (60+ days supply, ROP: 20).",
             "Launch 10% promotional clearance bundle 'Buy 2 Get 1 Tea' to liberate ₹28,800 working capital.",
             "Overstocked capital lockup. Shelf velocity has dropped. Clearance frees shelf space for high-margin snacks."),

            # 18. Overstocked Salt Rebalancing (Tata Salt)
            (18, "inventory", "product", products_map["SPC-SALT-006"].id, None, "pause_procurement", "low", "pending",
             "Inventory notice (LOW): 'Tata Salt (1kg Pack)' stock is 180 units (120 days coverage, ROP: 50).",
             "Freeze wholesale salt orders for next 60 days to prevent dampness clumping.",
             "Sufficient stock on hand for 4 months. Monsoon humidity risk. Halt reordering."),

            # 19. High-Margin Tea Upsell Opportunity (Assam Tea)
            (19, "pricing", "product", products_map["BEV-TEA-008"].id, None, "promotional_highlight", "low", "pending",
             "Profitability highlight (LOW): 'Premium CTC Assam Tea (1kg)' delivers exceptional 31.1% margin (₹140/unit).",
             "Feature at checkout counter POS display to boost overall basket profitability.",
             "Highest gross margin SKU in dry grocery department. Countertop prominence will maximize store blended margin."),

            # 20. B2B Credit Limit Increase (Sri Venkateshwara Bakery)
            (20, "khata", "customer", customers_list[6][0].id, None, "increase_credit_limit", "low", "pending",
             "Khata growth alert (LOW): 'Sri Venkateshwara Bakery' credit utilization 71% with 100% on-time settlement.",
             "Approve credit limit expansion from ₹20,000 to ₹30,000 to capture larger weekly flour orders.",
             "Punctual commercial bakery buyer with steady volume growth. Higher limit will increase weekly store revenue by ₹8,000."),
        ]

        for rid, mod, etype, eid, poid, pact, prio, st, reason, summ, rsn in recs_data:
            rec = Recommendation(
                id=rid,
                module=mod,
                entity_type=etype,
                entity_id=eid,
                purchase_order_id=poid,
                primary_action=pact,
                priority=prio,
                status=st,
                reason=reason,
                llm_summary=summ,
                llm_reasoning=rsn,
                created_at=now - timedelta(minutes=rid * 3),
            )
            db.add(rec)
        db.commit()
        print("  [OK] 20 Detailed Multi-Agent Recommendations seeded.")

        print("\n" + "=" * 75)
        print("  MASSIVE DATASET SUCCESSFULLY POPULATED!")
        print("  - 12 Wholesale Suppliers")
        print("  - 80 Products across 8 Retail Categories")
        print("  - 25 Khata Customers across all debt profiles")
        print("  - 350+ Sales Transactions (45 days rolling)")
        print("  - 16 Operational Expenses")
        print("  - 8 Purchase Orders")
        print("  - 20 AI Approval Recommendations")
        print("=" * 75)

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Failed to seed massive dataset: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_massive_data()
