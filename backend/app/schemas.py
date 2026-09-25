"""
schemas.py -- Pydantic request and response schemas for MicroBizAI API.

Defines schemas for ORM models, agent API payloads, CRUD endpoints, and HITL recommendations.
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field

DateType = date  # alias used in some schemas to avoid field-name shadowing


# ── 1. Product Schemas ────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    """Used in POST /api/products — id is auto-generated as UUID."""
    sku:            str
    name:           str
    selling_price:  float = 0.0
    cost_price:     float = 0.0
    current_stock:  float = 0.0
    reorder_level:  float = 0.0
    safety_stock:   float = 0.0
    lead_time_days: int   = 1
    # ML Store Profile fields (optional at creation)
    store_type:            Optional[str]  = None   # 'a','b','c','d'
    assortment:            Optional[str]  = None   # 'a','b','c'
    competition_distance:  Optional[float] = None  # meters
    competition_open_date: Optional[date]  = None
    promo_active:          bool = False
    promo2:                bool = False
    school_holiday:        bool = False


class ProductUpdate(BaseModel):
    """Used in PUT /api/products/{id} — all fields optional."""
    sku:            Optional[str]   = None
    name:           Optional[str]   = None
    selling_price:  Optional[float] = None
    cost_price:     Optional[float] = None
    reorder_level:  Optional[float] = None
    safety_stock:   Optional[float] = None
    lead_time_days: Optional[int]   = None
    # ML Store Profile fields
    store_type:            Optional[str]   = None
    assortment:            Optional[str]   = None
    competition_distance:  Optional[float] = None
    competition_open_date: Optional[date]  = None
    promo_active:          Optional[bool]  = None
    promo2:                Optional[bool]  = None
    school_holiday:        Optional[bool]  = None


class ProductStockUpdate(BaseModel):
    """Used in PUT /api/products/{id}/stock — sets current_stock directly."""
    current_stock: float = Field(description="New stock level after delivery/adjustment")


class ProductResponse(BaseModel):
    id:             str
    sku:            str
    name:           str
    selling_price:  float
    cost_price:     float
    current_stock:  float
    reorder_level:  float
    safety_stock:   float
    lead_time_days: int
    # ML Store Profile fields
    store_type:            Optional[str]  = None
    assortment:            Optional[str]  = None
    competition_distance:  Optional[float] = None
    competition_open_date: Optional[date]  = None
    promo_active:          bool = False
    promo2:                bool = False
    school_holiday:        bool = False
    ml_ready:              bool = False  # computed: True if store_type + assortment are set

    class Config:
        from_attributes = True


# ── 2. Customer Schemas ───────────────────────────────────────────────────────

class CustomerCreate(BaseModel):
    name:  str
    email: Optional[str] = None
    phone: Optional[str] = None


class CustomerUpdate(BaseModel):
    name:  Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class CustomerResponse(BaseModel):
    id:    str
    name:  str
    email: Optional[str] = None
    phone: Optional[str] = None

    class Config:
        from_attributes = True


class InvoiceSummaryItem(BaseModel):
    invoice_id:     int
    invoice_amount: float
    amount_paid:    float
    due_date:       Optional[DateType]
    created_date:   Optional[DateType]
    status:         str

    class Config:
        from_attributes = True


class CustomerSummaryResponse(BaseModel):
    customer_id:         str
    customer_name:       str
    outstanding_balance: float
    days_overdue:        Optional[int]    # days past due on oldest unpaid invoice
    invoice_history:     List[InvoiceSummaryItem]


# ── 3. Sale Schemas ───────────────────────────────────────────────────────────

class SaleCreate(BaseModel):
    model_config = {"populate_by_name": True}

    product_id:  str
    customer_id: Optional[str]      = None
    quantity:    float
    unit_price:  float
    sale_date:   Optional[DateType] = Field(default=None, alias="date")


class SaleResponse(BaseModel):
    id:           int
    product_id:   str
    customer_id:  Optional[str] = None
    store_id:     int = 1
    date:         Optional[DateType] = None
    quantity:     float
    unit_price:   float
    total_amount: float
    inventory_risk: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# ── 4. Invoice Schemas ────────────────────────────────────────────────────────

class InvoiceCreate(BaseModel):
    customer_id:    str
    invoice_amount: float
    due_date:       Optional[DateType] = None
    created_date:   Optional[DateType] = None


class InvoiceResponse(BaseModel):
    id:             int
    customer_id:    str
    invoice_amount: float
    amount_paid:    float
    due_date:       Optional[DateType]
    created_date:   Optional[DateType]
    status:         str

    class Config:
        from_attributes = True


# ── 5. Payment Schemas ────────────────────────────────────────────────────────

class PaymentCreate(BaseModel):
    payment_date: DateType
    amount:       float = Field(gt=0, description="Must be a positive amount")


class PaymentResponse(BaseModel):
    id:             int
    invoice_id:     int
    payment_date:   DateType
    amount:         float
    # derived fields for convenience
    invoice_status: str
    invoice_amount_paid: float

    class Config:
        from_attributes = True


# ── 6. Expense Schemas ────────────────────────────────────────────────────────

class ExpenseCreate(BaseModel):
    model_config = {"populate_by_name": True}

    category:              str
    description:           Optional[str]      = None
    current_period_amount: float              = 0.0
    prior_period_amount:   float              = 0.0
    expense_date:          Optional[DateType] = Field(default=None, alias="date")


class ExpenseResponse(BaseModel):
    id:                    int
    category:              str
    description:           Optional[str]
    current_period_amount: float
    prior_period_amount:   float
    date:                  Optional[DateType]

    class Config:
        from_attributes = True


# ── 7. Business Settings Schemas ──────────────────────────────────────────────

class BusinessSettingsResponse(BaseModel):
    id:               int
    min_cash_reserve: float
    currency:         str
    # Phase 1: operational thresholds
    safety_stock_days:             int   = 3
    review_period_days:            int   = 7
    khata_overdue_days:            int   = 30
    expense_anomaly_threshold_pct: float = 30.0
    high_risk_multiplier:          float = 1.0
    medium_risk_multiplier:        float = 1.5
    autonomous_mode:               bool  = False

    class Config:
        from_attributes = True


class BusinessSettingsUpdate(BaseModel):
    min_cash_reserve:              Optional[float] = None
    currency:                      Optional[str]   = None
    # Phase 1: operational thresholds
    safety_stock_days:             Optional[int]   = None
    review_period_days:            Optional[int]   = None
    khata_overdue_days:            Optional[int]   = None
    expense_anomaly_threshold_pct: Optional[float] = None
    high_risk_multiplier:          Optional[float] = None
    medium_risk_multiplier:        Optional[float] = None
    autonomous_mode:               Optional[bool]  = None


# ── 8. Dashboard Summary Schema ───────────────────────────────────────────────

class DashboardSummaryResponse(BaseModel):
    today_sales_revenue:        float
    total_cash_position:        float
    low_stock_products_count:   int
    overdue_invoices_count:     int
    pending_recommendations_count: int
    currency:                   str


# ── 9. Agent Endpoint Request Schemas ─────────────────────────────────────────

class SalesForecastRequest(BaseModel):
    store_features:       Optional[Dict[str, Any]] = Field(default=None)
    forecast_horizon_days: int = Field(default=7)


class InventoryRiskRequest(BaseModel):
    product_id:     str
    current_stock:  float
    forecast_demand: float
    reorder_level:  float
    safety_stock:   float
    lead_time_days: int


class CashflowCheckRequest(BaseModel):
    current_cash:          float
    expected_sales_revenue: float
    upcoming_expenses:     float
    planned_purchase_cost: float
    min_cash_reserve:      float


class ExpenseAnalyzeRequest(BaseModel):
    category:              str
    current_period_amount: float
    prior_period_amount:   float


class CreditAnalyzeRequest(BaseModel):
    customer_id:    str
    invoice_amount: float
    amount_paid:    float
    due_date:       date
    today:          Optional[date] = None


class ProfitabilityAnalyzeRequest(BaseModel):
    product_id:    str
    selling_price: float
    cost_price:    float
    quantity_sold: float


class RunFullPipelineRequest(BaseModel):
    inventory_inputs:     List[InventoryRiskRequest]
    cashflow_input:       CashflowCheckRequest
    expense_inputs:       List[ExpenseAnalyzeRequest]
    credit_inputs:        List[CreditAnalyzeRequest]
    profitability_inputs: List[ProfitabilityAnalyzeRequest]
    forecast_horizon_days: int          = 7
    today:                Optional[date] = None


# ── 10. HITL Recommendation Schemas ──────────────────────────────────────────

class ModifyRecommendationRequest(BaseModel):
    modified_message: str = Field(description="Shopkeeper modified customer message or note")


class HumanActionResponse(BaseModel):
    id:                int
    recommendation_id: int
    action:            str
    original_message:  Optional[str] = None
    modified_message:  Optional[str] = None
    timestamp:         datetime

    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    id:                        int
    created_at:                datetime
    primary_action:            str
    priority:                  str
    reason:                    str
    secondary_recommendations: Optional[List[Dict[str, Any]]] = None
    llm_summary:               Optional[str] = None
    llm_reasoning:             Optional[str] = None
    suggested_customer_message: Optional[str] = None
    status:                    str
    modified_message:          Optional[str] = None
    # Phase 1: entity context for traceability
    module:            Optional[str] = None
    entity_type:       Optional[str] = None
    entity_id:         Optional[str] = None
    purchase_order_id: Optional[int] = None

    class Config:
        from_attributes = True


class RecommendationAnalyticsResponse(BaseModel):
    total_count:                  int
    pending_count:                int
    approved_count:               int
    modified_count:               int
    rejected_count:               int
    avg_time_to_decision_seconds: float


# ── 11. Sales Forecasting Schemas ─────────────────────────────────────────────

class ForecastRequest(BaseModel):
    """Used in POST /api/products/{id}/forecast — run forecast with specified horizon."""
    horizon_days: int = Field(default=7, ge=1, le=90, description="Forecast horizon in days (e.g. 7, 14, 30)")


class ForecastResponse(BaseModel):
    id:                   int
    product_id:           str
    product_name:         Optional[str] = None
    product_sku:          Optional[str] = None
    forecast_date:        DateType
    horizon_days:         int
    predicted_sales:      float
    model_used:           str
    status:               str
    created_at:           datetime
    current_stock:        float
    stock_gap_preview:    float
    stockout_risk_preview: str

    class Config:
        from_attributes = True


class ForecastHistoryItem(BaseModel):
    id:              int
    product_id:      str
    forecast_date:   DateType
    horizon_days:    int
    predicted_sales: float
    model_used:      str
    status:          str
    created_at:      datetime
    actual_sales:    Optional[float] = None
    error:           Optional[float] = None
    error_pct:       Optional[float] = None
    is_completed:    bool            = False
    accuracy_note:   Optional[str]   = None

    class Config:
        from_attributes = True


class ForecastActRequest(BaseModel):
    """Used in POST /api/forecasts/{id}/act — shopkeeper human decision on forecast."""
    action: str = Field(
        description="'trigger_inventory_check' | 'adjust_stock' | 'dismiss'"
    )
    stock_adjustment: Optional[float] = Field(
        default=None,
        description="Optional new stock value if action='adjust_stock'"
    )


class ForecastActResponse(BaseModel):
    forecast_id:        int
    action:             str
    status:             str
    recommendation_id:  Optional[int] = None
    recommendation:     Optional[Dict[str, Any]] = None
    current_stock:      Optional[float] = None
    message:            str


# ── 12. Supplier Schemas (Phase 1) ────────────────────────────────────────────

class SupplierCreate(BaseModel):
    name:         str
    contact_name: Optional[str] = None
    phone:        Optional[str] = None
    email:        Optional[str] = None
    address:      Optional[str] = None
    category:     Optional[str] = None
    is_active:    bool = True


class SupplierUpdate(BaseModel):
    name:         Optional[str]  = None
    contact_name: Optional[str]  = None
    phone:        Optional[str]  = None
    email:        Optional[str]  = None
    address:      Optional[str]  = None
    category:     Optional[str]  = None
    is_active:    Optional[bool] = None


class SupplierResponse(BaseModel):
    id:           int
    name:         str
    contact_name: Optional[str] = None
    phone:        Optional[str] = None
    email:        Optional[str] = None
    address:      Optional[str] = None
    category:     Optional[str] = None
    is_active:    bool
    created_at:   datetime

    class Config:
        from_attributes = True


# ── 13. Purchase Order Schemas (Phase 1) ──────────────────────────────────────

class PurchaseOrderItemCreate(BaseModel):
    product_id: str
    quantity:   float
    unit_cost:  float = 0.0


class PurchaseOrderItemResponse(BaseModel):
    id:                int
    purchase_order_id: int
    product_id:        str
    quantity:          float
    unit_cost:         float
    total_cost:        float
    product_name:      Optional[str] = None
    product_sku:       Optional[str] = None

    class Config:
        from_attributes = True


class PurchaseOrderCreate(BaseModel):
    supplier_id: Optional[int] = None
    priority:    str           = "medium"
    reason:      Optional[str] = None
    notes:       Optional[str] = None
    items:       List[PurchaseOrderItemCreate]


class PurchaseOrderStatusUpdate(BaseModel):
    """Used in PATCH /api/purchase-orders/{id} for status transitions."""
    status: str = Field(description="New status: PENDING_APPROVAL | APPROVED | REJECTED | ORDERED | RECEIVED | CANCELLED")
    notes:  Optional[str] = None


class PurchaseOrderResponse(BaseModel):
    id:            int
    po_number:     str
    supplier_id:   Optional[int] = None
    supplier_name: Optional[str] = None
    status:        str
    total_amount:  float
    priority:      str
    reason:        Optional[str] = None
    notes:         Optional[str] = None
    created_at:    datetime
    approved_at:   Optional[datetime] = None
    ordered_at:    Optional[datetime] = None
    received_at:   Optional[datetime] = None
    items:         List[PurchaseOrderItemResponse] = []

    class Config:
        from_attributes = True


# ── 14. Inventory Event Schemas (Phase 1) ─────────────────────────────────────

class InventoryEventResponse(BaseModel):
    id:              int
    product_id:      str
    event_type:      str
    quantity_before: float
    quantity_change: float
    quantity_after:  float
    reference_type:  Optional[str] = None
    reference_id:    Optional[str] = None
    notes:           Optional[str] = None
    created_at:      datetime

    class Config:
        from_attributes = True


# ── 15. Agent Run Schemas (Phase 1) ───────────────────────────────────────────

class AgentRunResponse(BaseModel):
    id:           int
    agent_name:   str
    started_at:   datetime
    completed_at: Optional[datetime] = None
    status:       str
    trigger:      Optional[str] = None
    entity_type:  Optional[str] = None
    entity_id:    Optional[str] = None
    output_data:  Optional[Dict[str, Any]] = None
    error:        Optional[str] = None

    class Config:
        from_attributes = True


# ── 16. Audit Log Schemas (Phase 1) ───────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id:         int
    timestamp:  datetime
    actor_type: str
    actor_id:   Optional[str] = None
    action:     str
    entity:     Optional[str] = None
    entity_id:  Optional[str] = None
    old_value:  Optional[Dict[str, Any]] = None
    new_value:  Optional[Dict[str, Any]] = None
    reason:     Optional[str] = None

    class Config:
        from_attributes = True


# ── 17. Automation Status Schema (Phase 1) ────────────────────────────────────

class AutomationStatusResponse(BaseModel):
    autonomous_mode:       bool
    pending_approvals:     int
    agent_runs_today:      int
    recommendations_today: int
