# 🎓 MicroBizAI — Master Project Guide Presentation Runbook & Button-by-Button Script

> **How to Use This Runbook:**  
> Follow this exact sequence when presenting to your project guide. Every single page, button, slider, and input field is documented with:
> 1. **What the feature is & why it matters**
> 2. **Exact button to click and what it does**
> 3. **Copy-pasteable sample inputs**
> 4. **Expected on-screen reaction**
> 5. **Guide Defense Script** (What to say mathematically and technically to justify project depth)

---

## 🚀 Pre-Presentation Setup & Massive Dataset Status

Your database has been populated with a **massive, production-grade retail catalog**:
- **80 Abundant Products** across 8 Retail Departments:
  1. *Grains, Rice & Pulses* (Basmati Rice 50kg, Kolam Rice 25kg, Sona Masoori, Ponni Boiled, Biryani Rice, Toor Dal, Moong Dal, Chana Dal, Urad Dal, Kabuli Chana, Rajma, Green Moong)
  2. *Flours, Atta & Sooji* (Chakki Fresh Atta 10kg, Aashirvaad 5kg, Sharbati Atta, Fortune Atta, Besan, Maida, Sooji/Rava, Vermicelli, Poha, Rice Flour)
  3. *Cooking Oils & Pure Ghee* (Sunflower Oil 15L Tin, Fortune Sunlite 1L, Kachi Ghani Mustard, Groundnut Oil, Saffola Gold, Amul Cow Ghee 1L, Nandini Ghee 500ml, Mother Dairy Ghee, Dhara Mustard, Parachute Coconut Oil)
  4. *Fresh Dairy & Eggs* (Fresh Milk 1L, Amul Taaza 1L, Amul Gold 1L, Nandini Milk 500ml, Amul Butter 500g, Amul Butter 100g, Nandini Curd 500g, Malai Paneer 200g, Cheese Slices 200g, Farm Eggs Crate 30)
  5. *Sweeteners, Tea & Coffee* (Sugar 50kg, Madhur Sugar 5kg, Jaggery Powder, Assam Tea 1kg, Tata Tea 500g, Taj Mahal 250g, Bru Coffee 100g, Nescafe Classic 50g)
  6. *Spices, Salts & Condiments* (Tata Salt 1kg, Tata Rock Salt, Everest Turmeric, MDH Deggi Mirch, Catch Coriander, Garam Masala, Kitchen King, Cumin/Jeera, Rai, Hing)
  7. *Biscuits, Snacks & Instant Foods* (Parle-G Gold, Maggi Noodles 24-pack, YiPPee! Noodles, Good Day Butter, Oreo Vanilla, Dark Fantasy, Aloo Bhujia 1kg, Khatta Meetha 1kg, Kurkure, Lay's Masala)
  8. *Household, Cleaning & Personal Care* (Surf Excel 1kg, Tide Plus, Rin Bar, Vim Gel, Vim Bar, Harpic 1L, Lizol 1L, Dettol Soap, Lifebuoy Soap, Colgate 500g)
- **12 Wholesale Suppliers** (Punjab Agro, Mother Dairy, Adani Wilmar, HUL, Tata Consumer, Parle, ITC Foods, Nestle, Everest/MDH, Haldiram, Godrej CP, Dabur)
- **25 Khata Customers** across all debt profiles (Chronic Delinquency >60d, Overdue 30-50d, Courtesy Grace 5-15d, Active B2B Hotels, Settled VIPs)
- **487 Rolling Sales Transactions** spanning 45 days
- **16 Operational Expenses** (Rent, Electricity Spike +53%, Logistics, Staff Wages, Deep Freezer Maintenance +166%, Generator Diesel, Trade License, CCTV, Water, Festival Bonus)
- **8 Purchase Orders** across DRAFT, ORDERED, RECEIVED, PARTIAL
- **20 AI Approval Recommendations** covering stockout deficits, credit holds, overdue follow-ups, margin corrections, expense audits, and dead stock clearance!

To re-seed or reset this state at any time:
```powershell
python backend/scripts/seed_guide_demo_data.py
```

Start servers in separate terminals:
```powershell
# Terminal 1: FastAPI Backend
.\venv\Scripts\uvicorn.exe backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Vite Frontend
cd frontend
npm run dev
```
Open your browser at: **`http://localhost:5173`**

---

## 🌟 PART 1: The Executive Hook (Permanent Top Store Header)

Every page features the **Sticky Glassmorphic Global Header**. Show this first to demonstrate consumer-grade product polish.

| UI Element | What It Does | Guide Talking Point |
| :--- | :--- | :--- |
| **Store Badge (`📍 Gowda Provisions • Bengaluru`)** | Displays store identity and market cluster. Clicking it takes you to the Merchant Profile portal. | *"MicroBizAI is multi-tenant and merchant-aware; every operational threshold is localized to the store's geo-market."* |
| **Zomato-Style Sliding Switch (`🔒 Manual` vs `⚡ Automation`)** | Instantly switches the entire application architecture between a traditional manual Kirana ERP and a closed-loop multi-agent autonomous system. | *"Rather than a generic ERP, we designed two distinct operational paradigms: one for traditional merchant oversight, and one for autonomous multi-agent execution."* |
| **Dynamic Action Button** | Shows `🛒 New POS Bill` in Manual Mode; transforms into `🤖 AI Approvals` in Automation Mode. | *"Context-aware navigation prevents cognitive overload by presenting only mode-relevant actions."* |
| **Merchant Avatar (`C Chetan Gowda ▼`)** | Opens account drawer showing store phone (`+91 98450 12345`), registration status, switch store, and sign out. | *"Demonstrates secure role-based access and merchant profile isolation."* |

---

## ⚡ PART 2: Mode 1 — Autonomous Retail OS (`⚡ Automation Mode`)

Click the **`⚡ Automation`** toggle in the top bar. Explain that in this mode, the shopkeeper acts as an **executive supervisor (Human-in-the-Loop)** while 5 autonomous agents run operations in the background.

---

### Page 2.1: Executive Dashboard (`/`)

#### 1. Real-Time Autonomous KPI Cards
- **Today's Revenue (POS):** Aggregates daily sales from POS billing (e.g. ₹6,840.00).
- **Net Cash Position:** Net liquidity (Sales − Expenses − ₹25,000 Safety Reserve). Shows in green if healthy, red if constrained.
- **Pending AI Approvals:** Counter of recommendations waiting for review (**20 Pending**).
- **Autonomous Agents (5/5):** Displays active agent fleet: *Inventory Sentinel, Cashflow Guardian, Credit Copilot, Expense Auditor, Profit Optimizer*.

#### 2. Actionable Buttons on this Page:
- **Button: `🛒 Customer Order (POS)`**
  - **What it does:** Quick shortcut to launch the customer checkout terminal.
- **Button: `🤖 Review AI Approvals (20)`**
  - **What it does:** Jumps directly to the HITL approval inbox.
- **Button: `⚡ Trigger Live Store Sweep`**
  - **What happens when clicked:** The button shows an animated spinner (`Scanning 5 Agents...`). The backend sweeps all 80 products, 25 khata ledgers, and 16 expense lines.
  - **Expected Result:** A purple toast card appears: `✅ Store Health Sweep Complete (Recommendation #X)` highlighting the primary prioritized action.
  - **Guide Script:** *"This invokes our distributed agent pipeline. Each agent analyzes its respective business dimension, and the decision engine applies Pareto prioritization to prevent conflicting recommendations."*

---

### Page 2.2: Deep Academic Showcase 1 — LangGraph StateGraph DAG (`/agent-graph`)

> **Click `🧠 LangGraph DAG` in the sidebar or the banner card on Dashboard.**

#### 1. What This Page Solves
Proves to the guide that this is **not** a simple script with `if/else` logic, but an **asynchronous state graph (DAG)** with state reduction and mathematical conflict arbitration.

#### 2. Interactive Controls & Buttons:
- **Button: `▶ Run Live Trace Step-by-Step`**
  - **What happens:** Steps through the 8 nodes in sequence with glowing active animations:
    1. `Event Ingestion` (Captures event snapshot)
    2. Parallel execution of `[Inventory Sentinel, Sales Forecaster, Credit Risk Scorer, Expense Audit]`
    3. `State Reducer` (Aggregates parallel mutations into unified state)
    4. `Pareto Conflict Arbitrator` (Resolves stock vs cash conflicts)
    5. `HITL Governance Gateway` (Routes to approval inbox)
    6. `Execution Engine` (Dispatches action)
  - **Telemetry Shown:** Latency in milliseconds (e.g. `142ms`), peak memory (`41.8 MB`), and state payload keys.
- **Button: `⚡ Execute Full Convergence`**
  - **What happens:** Instantly resolves all graph cycles and displays the final consensus decision.

#### 3. The Pareto Conflict Arbitration Card (Crucial for Guide Defense!)
Show the box titled: **"Active Conflict: Inventory Sentinel vs Cashflow Guardian"**:
- **Conflict:** Inventory Sentinel calculated a stockout risk on *Aashirvaad Shudh Chakki Atta* and proposed an **₹84,200** purchase order. However, Cashflow Guardian detected available cash is ₹45,000 and the shopkeeper has a mandatory ₹50,000 reserve floor!
- **Resolution:** Rather than crashing or blindly depleting cash, the **Pareto Arbitrator** trims the purchase order to **₹31,500** (covering high-velocity 5kg SKUs only) and requests 15-day supplier credit terms.
- **Guide Script:** *"Here we resolve the multi-objective optimization problem: minimizing stockout risk while maximizing liquidity reserve. The arbitrator computes a non-dominated Pareto-optimal solution."*

---

### Page 2.3: Deep Academic Showcase 2 — Kirana Digital Twin Sandbox (`/simulation`)

> **Click `🎲 Digital Twin Sandbox` in the sidebar or from the Dashboard card.**

#### 1. What This Page Solves
Runs **1,000 Monte Carlo stochastic differential simulations** of 90-day store cashflow under macro-economic stress conditions.

#### 2. Interactive Controls & Buttons:
- **Slider 1: Demand Shock ($-50\%$ to $+100\%$)**
  - *Sample input:* Drag to `-30%` (simulating sudden economic slowdown).
- **Slider 2: Inflation Rate ($0\%$ to $30\%$)**
  - *Sample input:* Drag to `14%` (simulating wholesale supplier cost spikes).
- **Slider 3: Khata Default Rate ($0\%$ to $50\%$)**
  - *Sample input:* Drag to `25%` (simulating 1 in 4 credit customers defaulting).
- **One-Click Stress Presets:**
  - **Button: `⚡ Stagflation Shock`** (Sets Demand: -25%, Inflation: 18%, Default: 30%)
  - **Button: `🎉 Diwali Festive Surge`** (Sets Demand: +60%, Inflation: 6%, Default: 5%)
  - **Button: `🚚 Supply Chain Squeeze`** (Sets Demand: -10%, Inflation: 22%, Default: 15%)
  - **Button: `🔄 Baseline (Normal)`** (Resets to normal operating conditions)
- **Button: `🎲 Run 1,000 Stochastic Iterations`**
  - **What happens:** Simulates 1,000 stochastic cash flow trajectories over 90 forward days ($90 \times 1,000 = 90,000$ simulated daily cycles).

#### 3. Expected Results & Metrics to Explain:
- **Value-at-Risk (VaR 95%):** e.g. `₹28,450` — With 95% statistical confidence, maximum potential liquidity loss over 90 days will not exceed this amount.
- **Probability of Insolvency:** e.g. `2.4%` (Autonomous) vs `38.2%` (Unmanaged Baseline).
- **Autonomous Resiliency Lift:** Shows how MicroBizAI's autonomous safety buffers and replenishment caps prevent store bankruptcy compared to an unmanaged store.
- **Dynamic Stochastic Fan Chart:** Explains the 5 percentile bands: $p_5$ (Worst-case stress trajectory), $p_{25}$ (Conservative), $p_{50}$ (Median expected outcome), $p_{75}$ (Optimistic), $p_{95}$ (Best-case scenario).
- **Guide Script:** *"This implements a Geometric Brownian Motion cashflow model with drift and stochastic volatility. It answers the question: Will this Kirana store survive a sudden 20% inflation shock or customer credit defaults over the next quarter?"*

---

### Page 2.4: AI Approvals Inbox (`/recommendations`)

#### 1. What This Page Solves
Demonstrates the **Human-in-the-Loop (HITL)** governance model across **20 diverse recommendations**. The AI never spends merchant money without 1-click merchant authorization.

#### 2. Interactive Buttons & Actions:
- **Priority Filter Tabs:** `All (20)`, `High (8)`, `Medium (7)`, `Low (5)`.
- **Card Action Buttons on Each Item:**
  - **Button: `✓ Approve & Execute`**
    - **What happens:** Instantly creates the official Supplier Purchase Order, puts overdue credit customers on automated SMS reminder holds, or commits price changes. A green confirmation banner displays the approved action.
  - **Button: `✗ Dismiss / Reject`**
    - **What happens:** Dismisses the recommendation. The system logs merchant feedback into the `audit_logs` table for model re-tuning.
- **Sample Items to Showcase to Your Guide:**
  1. *Critical Stockout Restock:* "Basmati Rice (50kg Bag) — Stock: 2 units (Coverage: 1.2 days, ROP: 25.0). Recommended PO: 28 units @ ₹1,100 = ₹30,800."
  2. *Daily Perishable Milk Order:* "Fresh Dairy Milk (1L Pouch) — Stock: 3 units (Coverage: 0.8 days). Recommended morning delivery: 50 units."
  3. *Chronic Delinquency Credit Freeze:* "Sharma Mess & Catering (Balance: ₹4,850.00, Overdue by 68 days). Recommended action: Pause credit & dispatch 48-hour legal collection notice."
  4. *Courtesy Khata SMS Link:* "Bawarchi Biryani Centre (Balance: ₹7,600.00, Overdue by 42 days). Recommended action: Send polite WhatsApp payment link with UPI QR."
  5. *Electricity Spike Anomaly:* "Electricity & Utilities (₹8,450 vs prior ₹5,500 = +53.6% spike). Recommended action: Flag for meter audit & check compressor seal on display cooler."
  6. *Negative Margin Price Fix:* "Refined White Sugar 50kg (Margin: -2.38%, Loss: ₹50/bag). Recommended action: Increase selling price from ₹2,100 to ₹2,250 to restore 4.4% positive margin."
  7. *Dead Stock Clearance:* "Parle-G Gold Biscuits (120 units on hand = 60+ days capital lockup). Recommended action: Launch 10% promo bundle 'Buy 2 Get 1 Tea' to liberate ₹28,800 liquidity."

---

### Page 2.5: Customer Sales Entry POS (`/sales`)

#### 1. What This Page Solves
Demonstrates how everyday retail transactions automatically feed the autonomous closed-loop intelligence.

#### 2. Sample Inputs to Demonstrate:
- **Product Dropdown (80 items):** Select `Fresh Dairy Milk (1L Pouch)` or `Tata Salt (1kg Vacuum Evaporated)` or `Cadbury Oreo Vanilla Crème`.
- **Quantity:** Enter `5`.
- **Customer Selection (25 options):** Select `Walk-in Customer (Cash / UPI)` or pick a Khata customer like `Ramesh Kumar (Teacher)` or `Udupi Sagar Hotel`.
- **Payment Method:** Select `UPI / Cash / Khata Credit`.
- **Button: `🛒 Complete Customer Order`**
  - **What happens:**
    1. Deducts 5 units from inventory instantly.
    2. Records the sale transaction with invoice number.
    3. Writes an immutable audit entry to `inventory_events`.
    4. Evaluates whether remaining stock is below reorder threshold. If stock breaches threshold, it immediately queues a Restock PO in **AI Approvals**!

---

## 🔒 PART 3: Mode 2 — Traditional Kirana ERP (`🔒 Manual Mode`)

Now, click the top toggle to **`🔒 Manual`**.  
Explain to the guide:  
> *"When the merchant selects Manual Mode, the entire autonomous automation engine is hidden. The interface transforms into a traditional, distraction-free store management ERP where the shopkeeper exercises direct physical control."*

---

### Page 3.1: Manual Store Operations Dashboard (`/`)
- Shows classic retail metrics: Today's Gross Revenue, Cash on Hand, Total SKU Count (**80**), Low Stock Items Count, and Total Outstanding Khata Credit.
- Notice: **Zero AI triggers, zero autonomous sweep buttons, zero LangGraph or Digital Twin elements.** Everything is clean, fast, and manual.

---

### Page 3.2: Grocery & Stock Inventory (`/products`)

#### 1. Features & Category Filters:
- Filter buttons:
  - `✨ All Products (80)`
  - `🌾 Grains & Pulses (22)`
  - `🥫 Cooking Oils & Ghee (10)`
  - `🫖 Tea & Spices (18)`
  - `🥛 Fresh Dairy & Eggs (10)`
  - `🍪 Biscuits & Snacks (10)`
  - `🧼 Household & Care (10)`
- Search Bar: Type `Milk`, `Atta`, `Sugar`, `Ghee`, or `Soap` to see instant client-side filtering.
- Visual Badges: Items with low inventory display a distinct red `Low Stock` badge.

#### 2. Product Detail & Physical Stock Recount (`/products/:id`):
Click on **`Fresh Dairy Milk (1L Pouch)`** or **`Fortune Sunlite Sunflower Oil`**.

| Form / Button | Sample Input | What Happens When Clicked |
| :--- | :--- | :--- |
| **Selling Price Input** | Change `66` to `68.00` | Click **`Update Price`** → Updates price across POS and updates unit margin. |
| **New On-Hand Stock Count** | Change `3` to `25` | Click **`Save New Stock Count`** → Reconciles physical stock after receiving a wholesale delivery. |
| **Recent Sales Table** | — | Displays the historical ledger of every transaction containing this SKU. |

---

### Page 3.3: Customer Khata & Credit Ledger (`/customers`)

#### 1. What This Page Solves
Digitalizes the traditional Indian red notebook (*Bahi-Khata*) to manage customer store credit across 25 diverse debtors.

#### 2. Sample Customers to Showcase:
- **Vikram Singh (Contractor):** Outstanding `₹8,200.00` — **Overdue (64 Days)** flagged in red.
- **Sharma Mess & Catering:** Outstanding `₹4,850.00` — **Overdue (68 Days)**.
- **Udupi Sagar Hotel:** Outstanding `₹18,500.00` — Overdue Commercial Hotel.
- **Ramesh Kumar (Teacher):** Outstanding `₹450.00` — Active Good Standing.
- **Verma Caterers & Events:** Outstanding `₹0.00` — 100% Repaid VIP.

#### 3. Customer Detail & Payment Collection (`/customers/:id`):
Click on **`Vikram Singh (Contractor)`**:
- View the itemized list of unpaid grocery bills.
- **Button / Form: `Record Khata Payment`**
  - **Sample input:** Amount: `₹2,000.00`, Notes: `Cash paid at counter`.
  - **Click: `Submit Payment`**
  - **Expected Result:** Outstanding balance reduces from ₹8,200 to ₹6,200. The invoice status updates to `PARTIAL`, and the transaction is logged with timestamp.

---

### Page 3.4: Supplier Purchase Orders (`/purchase-orders`)

#### 1. What This Page Solves
Manages wholesale supplier relationships, order drafting, and goods receiving across 12 wholesale suppliers.

#### 2. Sample Inputs to Create a Manual PO:
- **Button: `+ New Purchase Order`**
- **Supplier:** Select `Punjab Agro Food Wholesale` (Supplier #1) or `Hindustan Unilever Depot` (Supplier #4).
- **Product:** Select `Aashirvaad Shudh Chakki Atta (5kg Pack)`.
- **Quantity:** Enter `20`.
- **Unit Cost:** Enter `₹215.00` (Total PO: ₹4,300.00).
- **Click: `Save & Dispatch Order`**
- **Expected Result:** PO is created with status `ORDERED`.
- **Button: `✓ Mark Goods Received` on the PO:**
  - Clicking this automatically increases on-hand stock by +20 units and creates a verified `PURCHASE_RECEIVED` event in the stock audit trail.

---

### Page 3.5: Store Expenses Tracker (`/expenses`)

#### 1. Sample Inputs to Add an Expense:
- **Category:** Select `Electricity & Utilities` or `Shop Rent` or `Logistics & Transport`.
- **Amount:** Enter `₹1,200.00`.
- **Description:** Enter `Tempo delivery charges from APMC Yard`.
- **Date:** Select today's date.
- **Click: `Log Expense`**
- **Expected Result:** Appears immediately in the monthly expenses ledger and subtracts from today's net cash position.

---

### Page 3.6: Machine Learning Demand Forecasting Hub (`/forecasting`)

#### 1. What This Page Solves
Executes the trained **Random Forest 25-feature store-profile model** to forecast sales demand over 7, 14, or 30 days.

#### 2. Sample Inputs:
- **Select Product:** Choose `Basmati Rice (50kg Bag)` or `Fresh Dairy Milk (1L Pouch)`.
- **Forecast Horizon:** Select `7 Days` or `14 Days`.
- **Click: `Run Machine Learning Forecast`**
- **Expected Result:**
  - Displays predicted demand (e.g. `30.6 units`).
  - Compares against Current Stock (e.g. `2 units`).
  - Highlights the **Stock Gap Shortage of -28.6 units** in red, proving the need for immediate wholesale replenishment before stockout occurs!

---

## 🎯 5-Minute Master Defense Script for Your Guide

> *"Good morning Sir/Ma'am. Today we are presenting **MicroBizAI**, an autonomous retail intelligence operating system for India's 13 million Kirana stores.*
>
> *Our project has been benchmarked on a production-grade catalog of **80 products across 8 departments, 12 wholesale suppliers, 25 customer Khata ledgers, and 487 sales transactions**.*
>
> *Most student projects in retail stop at simple CRUD billing. MicroBizAI addresses real-world working capital failure:*
> 1. *In **Autonomous Mode**, our **LangGraph StateGraph** coordinates 5 asynchronous agents: an Inventory Sentinel, Cashflow Guardian, Credit Copilot, Expense Auditor, and Profit Optimizer. When stockout and cash reserve constraints collide, our **Pareto Arbitrator** calculates a mathematical compromise on the Pareto frontier.*
> 2. *Our **Kirana Digital Twin** runs 1,000 Monte Carlo stochastic trajectories simulating 90-day cash solvency under macro-economic shocks (inflation spikes, demand drops, khata defaults), computing formal **Value-at-Risk (VaR 95%)**.*
> 3. *Our **Machine Learning Demand Forecaster** maps store-profile features into a trained Random Forest model to predict unit velocity before stockouts happen.*
> 4. *In **Manual Mode**, the entire autonomous engine steps aside, providing a clean, distraction-free ERP for traditional physical grocery operations, customer credit ledger (Khata), supplier POs, and expense tracking.*
>
> *Every action respects Human-in-the-Loop governance: the AI calculates, but the merchant retains 1-click sovereign control."*
