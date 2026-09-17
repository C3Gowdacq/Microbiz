# MicroBizAI: Autonomous Multi-Agent Business Intelligence System

An autonomous business intelligence and supply chain decision-support platform designed for Micro, Small, and Medium Enterprises (MSMEs). MicroBizAI combines time-series machine learning forecasting with a multi-agent policy engine to automate stock replenishment, cash flow feasibility checks, overdue credit collection, and expense monitoring.

---

## 🏗 System Architecture

```
                                  +---------------------------------------+
                                  |     React + Vite Frontend (UI)        |
                                  | (Dashboard, Forecast, Stock, Dues)    |
                                  +-------------------+-------------------+
                                                      | REST / JSON (HTTP)
                                                      v
                                  +---------------------------------------+
                                  |        FastAPI Backend Gateway        |
                                  |     (/api/forecast, /api/products)    |
                                  +---------+-------------------+---------+
                                            |                   |
                     +----------------------+                   +----------------------+
                     v                                                                 v
+---------------------------------------+                             +---------------------------------------+
|   Machine Learning Forecasting Core   |                             |   Autonomous Multi-Agent Core Engine  |
| - 25 Temporal & Lag Feature Pipeline  |                             | - Inventory Agent (Stock Gap, DoC)    |
| - Random Forest Macro-Level Regressor |                             | - Cash Flow Agent (Liquidity Checks)  |
| - Macro-to-Micro Proportional Uplift  |                             | - Credit Agent (Aging & Invoicing)    |
+---------------------------------------+                             | - Expense Agent (Spike Detection)     |
                                                                      | - Human-in-the-Loop (HITL) Guardrails |
                                                                      +---------------------------------------+
                                                                                       |
                                                                                       v
                                                                      +---------------------------------------+
                                                                      |        SQLite Database Layer          |
                                                                      |  (Products, Sales, Invoices, Dues)    |
                                                                      +---------------------------------------+
```

---

## 🚀 Key Features

1. **Demand Forecasting (Store-to-SKU Allocation)**:
   - Evaluates 25 time-series features (lags, rolling sales velocities, competition distance, calendar encodings).
   - Generates multi-day store-level sales forecasts using Random Forest and scales demand to individual SKUs via proportional allocation.
2. **Inventory Gap & Safety Stock Optimization**:
   - Calculates target safety stock, Days of Inventory Coverage (DoC), and flags stockout risks before depletion.
3. **Cash Flow & Liquidity Feasibility Analysis**:
   - Validates whether purchasing needed stock leaves a safe minimum cash reserve buffer.
4. **Autonomous Credit & Overdue Debt Recovery**:
   - When procurement liquidity is insufficient, the engine identifies overdue customer credit receivables and drafts collection invoices.
5. **Human-in-the-Loop (HITL) Policy Control**:
   - Financial transactions and outgoing customer communications require explicit merchant confirmation.

---

## 📦 Project Structure

```
Major_Project/
├── backend/                  # FastAPI Application Layer
│   └── app/
│       ├── database.py       # SQLAlchemy Database Engine & Sessions
│       ├── models.py         # ORM Data Models (Products, Sales, Invoices, etc.)
│       ├── schemas.py        # Pydantic Request/Response Schemas
│       ├── seed_data.py      # Database Seeder & Mock Retail Data
│       ├── routers/          # REST Endpoints (forecast, products, sales, etc.)
│       └── services/         # Feature builders, agents data bridges, accuracy calculators
├── frontend/                 # React 18 + Vite Web Application
│   ├── src/
│   │   ├── pages/            # Dashboard, Products, Forecasting, Receivables, etc.
│   │   ├── components/       # Reusable UI components & modals
│   │   └── services/api.ts   # Axios API client
│   ├── package.json
│   └── vite.config.ts
├── ml/                       # Machine Learning Core & Agents
│   ├── data/                 # Raw & Processed datasets
│   ├── models/               # Model weights and baseline pipelines
│   └── src/                  # Feature engineering, training scripts, multi-agent definitions
├── requirements.txt          # Python dependencies
└── .env.example              # Environment variables template
```

---

## 🛠 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Git

### 1. Clone the Repository & Configure Environment
```bash
git clone <repository_url>
cd Major_Project

# Create your local .env file from the template
cp .env.example .env
```
Open `.env` and add your Groq API key:
```env
GROQ_API_KEY=your_groq_api_key_here
```

---

### 2. Backend Setup & Database Seeding

#### On Windows (PowerShell):
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Initialize database and seed sample products & sales
python -m backend.app.seed_data

# Start FastAPI server (runs on http://localhost:8000)
uvicorn backend.app.main:app --reload --port 8000
```

#### On macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m backend.app.seed_data
uvicorn backend.app.main:app --reload --port 8000
```

Interactive API documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

### 3. Frontend Setup

In a new terminal window:
```bash
cd frontend

# Install Node dependencies
npm install

# Run Vite development server
npm run dev
```
The web dashboard will launch at [http://localhost:5173](http://localhost:5173).

---

## 🧪 Testing & Verification

Run end-to-end verification and integration test suites:
```powershell
# Verify full backend CRUD and business workflows
python scratch/test_complete_project_flow.py

# Verify forecasting and multi-agent decision evaluation
python scratch/test_forecasting.py
```
