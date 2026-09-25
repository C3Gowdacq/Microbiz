/**
 * api.ts -- Axios API client for MicroBizAI FastAPI backend.
 * Provides typed methods for all CRUD entities, targeted agent checks,
 * dashboard summaries, and HITL recommendations.
 */

import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ── 1. Types & Models ────────────────────────────────────────────────────────

export interface Product {
  id: string;
  sku: string;
  name: string;
  selling_price: number;
  cost_price: number;
  current_stock: number;
  reorder_level: number;
  safety_stock: number;
  lead_time_days: number;
  // ML Store Profile
  store_type?: string | null;
  assortment?: string | null;
  competition_distance?: number | null;
  competition_open_date?: string | null;
  promo_active: boolean;
  promo2: boolean;
  school_holiday: boolean;
  ml_ready: boolean;
}

export interface ProductCreate {
  sku: string;
  name: string;
  selling_price?: number;
  cost_price?: number;
  current_stock?: number;
  reorder_level?: number;
  safety_stock?: number;
  lead_time_days?: number;
  // ML Store Profile
  store_type?: string | null;
  assortment?: string | null;
  competition_distance?: number | null;
  competition_open_date?: string | null;
  promo_active?: boolean;
  promo2?: boolean;
  school_holiday?: boolean;
}

export interface Customer {
  id: string;
  name: string;
  email?: string | null;
  phone?: string | null;
}

export interface CustomerCreate {
  name: string;
  email?: string | null;
  phone?: string | null;
}

export interface InvoiceSummaryItem {
  invoice_id: number;
  invoice_amount: number;
  amount_paid: number;
  due_date?: string | null;
  created_date?: string | null;
  status: 'unpaid' | 'partially_paid' | 'paid';
}

export interface CustomerSummary {
  customer_id: string;
  customer_name: string;
  outstanding_balance: number;
  days_overdue?: number | null;
  invoice_history: InvoiceSummaryItem[];
}

export interface InventoryRisk {
  product_id: string;
  product_name: string;
  sku: string;
  current_stock: number;
  avg_daily_demand: number;
  forecast_demand: number;
  horizon_days: number;
  lead_time_days: number;
  lead_time_demand: number;
  safety_stock: number;
  reorder_point: number;
  coverage_days?: number | null;
  stock_gap: number;
  risk_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'HEALTHY';
  reorder_needed: boolean;
  recommended_order_qty: number;
  model_used: string;
  scaling_factor: number;
}

export interface Sale {
  id: number;
  product_id: string;
  customer_id?: string | null;
  store_id: number;
  date?: string | null;
  quantity: number;
  unit_price: number;
  total_amount: number;
  inventory_risk?: InventoryRisk | null;
}

export interface SaleCreate {
  product_id: string;
  customer_id?: string | null;
  quantity: number;
  unit_price: number;
  date?: string | null;
}

export interface Invoice {
  id: number;
  customer_id: string;
  invoice_amount: number;
  amount_paid: number;
  due_date?: string | null;
  created_date?: string | null;
  status: 'unpaid' | 'partially_paid' | 'paid';
}

export interface InvoiceCreate {
  customer_id: string;
  invoice_amount: number;
  due_date?: string | null;
  created_date?: string | null;
}

export interface PaymentCreate {
  payment_date: string;
  amount: number;
}

export interface PaymentResponse {
  id: number;
  invoice_id: number;
  payment_date: string;
  amount: number;
  invoice_status: 'unpaid' | 'partially_paid' | 'paid';
  invoice_amount_paid: number;
}

export interface Expense {
  id: number;
  category: string;
  description?: string | null;
  current_period_amount: number;
  prior_period_amount: number;
  date?: string | null;
}

export interface ExpenseCreate {
  category: string;
  description?: string | null;
  current_period_amount: number;
  prior_period_amount?: number;
  date?: string | null;
}

export interface DashboardSummary {
  today_sales_revenue: number;
  total_cash_position: number;
  low_stock_products_count: number;
  overdue_invoices_count: number;
  pending_recommendations_count: number;
  currency: string;
}

export interface BusinessSettings {
  id: number;
  min_cash_reserve: number;
  currency: string;
}

// ── 2. Recommendation & HITL Types ──────────────────────────────────────────

export interface SecondaryRecommendation {
  action: string;
  priority: string;
  reason: string;
}

export interface PrimaryRecommendation {
  action: string;
  priority: string;
  reason: string;
}

export interface DecisionEngineOutput {
  primary_recommendation: PrimaryRecommendation;
  secondary_recommendations: SecondaryRecommendation[];
  summary: string;
}

export interface LLMExplanationOutput {
  summary: string;
  reasoning: string;
  suggested_customer_message?: string | null;
  is_fallback?: boolean;
  model_used?: string;
}

export interface RecommendationRecord {
  id: number;
  created_at: string;
  primary_action: string;
  priority: string;
  reason: string;
  secondary_recommendations?: SecondaryRecommendation[] | null;
  llm_summary?: string | null;
  llm_reasoning?: string | null;
  suggested_customer_message?: string | null;
  status: 'pending' | 'approved' | 'modified' | 'rejected';
  modified_message?: string | null;
  entity_type?: string | null;
  entity_id?: string | null;
  module?: string | null;
}

export interface AnalyticsSummary {
  total_count: number;
  pending_count: number;
  approved_count: number;
  modified_count: number;
  rejected_count: number;
  avg_time_to_decision_seconds: number;
}

export interface FullPipelineResponse {
  recommendation_id: number;
  inputs_summary?: {
    products_checked: number;
    customers_checked: number;
    expense_categories: number;
  };
  decision: DecisionEngineOutput;
  llm_explanation: LLMExplanationOutput;
  error?: string | null;
}

// ── 3. Targeted Agent Check Responses ───────────────────────────────────────

export interface InventoryAgentResult {
  product_id: string;
  current_stock: number;
  forecast_demand: number;
  stock_gap: number;
  stock_coverage_days?: number | null;
  stockout_risk: 'HIGH' | 'MEDIUM' | 'LOW' | 'N/A';
  recommended_order_quantity: number;
}

export interface CheckInventoryResponse {
  product_id: string;
  agent_result: InventoryAgentResult;
  recommendation_id?: number | null;
  recommendation_created: boolean;
}

export interface ProfitabilityAgentResult {
  product_id: string;
  selling_price: number;
  cost_price: number;
  unit_profit: number;
  gross_profit: number;
  profit_margin: number;
  classification: 'loss_making' | 'low_margin' | 'healthy_margin' | 'highly_profitable';
}

export interface CheckProfitabilityResponse {
  product_id: string;
  agent_result: ProfitabilityAgentResult;
  recommendation_id?: number | null;
  recommendation_created: boolean;
}

export interface CreditAgentResult {
  customer_id: string;
  outstanding_amount: number;
  days_overdue: number;
  customer_risk: 'HIGH' | 'MEDIUM' | 'LOW' | 'NONE';
  recommended_action: string;
}

export interface CheckCreditResponse {
  customer_id: string;
  agent_result?: CreditAgentResult | null;
  message?: string;
  recommendation_id?: number | null;
  recommendation_created: boolean;
}

export interface ExpenseTrendAgentResult {
  category: string;
  current_period_amount: number;
  prior_period_amount: number;
  increase_pct?: number | null;
  trend: 'increasing' | 'decreasing' | 'stable' | 'new_category';
  risk: 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface CheckExpenseTrendResponse {
  category: string;
  agent_result: ExpenseTrendAgentResult;
  recommendation_id?: number | null;
  recommendation_created: boolean;
}

export interface CashflowAgentResult {
  current_cash: number;
  expected_sales_revenue: number;
  upcoming_expenses: number;
  planned_purchase_cost: number;
  net_cash_flow: number;
  projected_cash_balance: number;
  cash_shortage_risk: 'HIGH' | 'MEDIUM' | 'LOW';
  liquidity_ok: boolean;
}

export interface CheckCashflowResponse {
  inputs_used: {
    current_cash: number;
    expected_sales_revenue: number;
    upcoming_expenses: number;
    planned_purchase_cost: number;
    min_cash_reserve: number;
  };
  agent_result: CashflowAgentResult;
}

// ── 4. API Client Functions ──────────────────────────────────────────────────

// Products
export const getProducts = async (): Promise<Product[]> => {
  const res = await api.get<Product[]>('/api/products');
  return res.data;
};

export const getProduct = async (id: string): Promise<Product> => {
  const res = await api.get<Product>(`/api/products/${id}`);
  return res.data;
};

export const createProduct = async (data: ProductCreate): Promise<Product> => {
  const res = await api.post<Product>('/api/products', data);
  return res.data;
};

export const updateProduct = async (id: string, data: Partial<ProductCreate>): Promise<Product> => {
  const res = await api.put<Product>(`/api/products/${id}`, data);
  return res.data;
};

export const adjustProductStock = async (id: string, current_stock: number): Promise<Product> => {
  const res = await api.put<Product>(`/api/products/${id}/stock`, { current_stock });
  return res.data;
};

export const checkProductInventory = async (id: string): Promise<CheckInventoryResponse> => {
  const res = await api.post<CheckInventoryResponse>(`/api/products/${id}/check-inventory`);
  return res.data;
};

export const checkProductProfitability = async (id: string): Promise<CheckProfitabilityResponse> => {
  const res = await api.post<CheckProfitabilityResponse>(`/api/products/${id}/check-profitability`);
  return res.data;
};

// Customers
export const getCustomers = async (): Promise<Customer[]> => {
  const res = await api.get<Customer[]>('/api/customers');
  return res.data;
};

export const getCustomer = async (id: string): Promise<Customer> => {
  const res = await api.get<Customer>(`/api/customers/${id}`);
  return res.data;
};

export const createCustomer = async (data: CustomerCreate): Promise<Customer> => {
  const res = await api.post<Customer>('/api/customers', data);
  return res.data;
};

export const getCustomerSummary = async (id: string): Promise<CustomerSummary> => {
  const res = await api.get<CustomerSummary>(`/api/customers/${id}/summary`);
  return res.data;
};

export const checkCustomerCredit = async (id: string): Promise<CheckCreditResponse> => {
  const res = await api.post<CheckCreditResponse>(`/api/customers/${id}/check-credit`);
  return res.data;
};

// Invoices & Payments
export const getInvoices = async (customerId?: string): Promise<Invoice[]> => {
  const res = await api.get<Invoice[]>('/api/invoices', {
    params: customerId ? { customer_id: customerId } : {},
  });
  return res.data;
};

export const createInvoice = async (data: InvoiceCreate): Promise<Invoice> => {
  const res = await api.post<Invoice>('/api/invoices', data);
  return res.data;
};

export const recordPayment = async (invoiceId: number, data: PaymentCreate): Promise<PaymentResponse> => {
  const res = await api.post<PaymentResponse>(`/api/invoices/${invoiceId}/payments`, data);
  return res.data;
};

// Sales
export const getSales = async (productId?: string, customerId?: string): Promise<Sale[]> => {
  const res = await api.get<Sale[]>('/api/sales', {
    params: {
      ...(productId ? { product_id: productId } : {}),
      ...(customerId ? { customer_id: customerId } : {}),
    },
  });
  return res.data;
};

export const createSale = async (data: SaleCreate): Promise<Sale> => {
  const res = await api.post<Sale>('/api/sales', data);
  return res.data;
};

// Expenses
export const getExpenses = async (category?: string): Promise<Expense[]> => {
  const res = await api.get<Expense[]>('/api/expenses', {
    params: category ? { category } : {},
  });
  return res.data;
};

export const createExpense = async (data: ExpenseCreate): Promise<Expense> => {
  const res = await api.post<Expense>('/api/expenses', data);
  return res.data;
};

export const checkExpenseTrend = async (category: string): Promise<CheckExpenseTrendResponse> => {
  const res = await api.post<CheckExpenseTrendResponse>('/api/expenses/check-trend', { category });
  return res.data;
};

// Cashflow
export const checkCashflowReal = async (): Promise<CheckCashflowResponse> => {
  const res = await api.post<CheckCashflowResponse>('/api/cashflow/check-real');
  return res.data;
};

// Dashboard & Settings
export const getDashboardSummary = async (): Promise<DashboardSummary> => {
  const res = await api.get<DashboardSummary>('/api/dashboard/summary');
  return res.data;
};

export const getSettings = async (): Promise<BusinessSettings> => {
  const res = await api.get<BusinessSettings>('/api/settings');
  return res.data;
};

export const updateSettings = async (data: Partial<BusinessSettings>): Promise<BusinessSettings> => {
  const res = await api.put<BusinessSettings>('/api/settings', data);
  return res.data;
};

// Full Pipeline & Recommendations
export const runFullPipeline = async (): Promise<FullPipelineResponse> => {
  const res = await api.post<FullPipelineResponse>('/api/agents/run-full');
  return res.data;
};

export const getRecommendations = async (status?: string): Promise<RecommendationRecord[]> => {
  const res = await api.get<RecommendationRecord[]>('/api/recommendations', {
    params: status ? { status } : {},
  });
  return res.data;
};

export const getRecommendationById = async (id: number): Promise<RecommendationRecord> => {
  const res = await api.get<RecommendationRecord>(`/api/recommendations/${id}`);
  return res.data;
};

export const approveRecommendation = async (id: number): Promise<RecommendationRecord> => {
  const res = await api.post<RecommendationRecord>(`/api/recommendations/${id}/approve`);
  return res.data;
};

export const modifyRecommendation = async (
  id: number,
  modified_message: string
): Promise<RecommendationRecord> => {
  const res = await api.post<RecommendationRecord>(`/api/recommendations/${id}/modify`, {
    modified_message,
  });
  return res.data;
};

export const rejectRecommendation = async (id: number): Promise<RecommendationRecord> => {
  const res = await api.post<RecommendationRecord>(`/api/recommendations/${id}/reject`);
  return res.data;
};

export const getAnalytics = async (): Promise<AnalyticsSummary> => {
  const res = await api.get<AnalyticsSummary>('/api/recommendations/analytics');
  return res.data;
};

// ── 5. Sales Forecasting Types & Methods ─────────────────────────────────────

export interface ForecastResponse {
  id: number;
  product_id: string;
  product_name?: string | null;
  product_sku?: string | null;
  forecast_date: string;
  horizon_days: number;
  predicted_sales: number;
  model_used: string;
  status: 'active' | 'acted_on' | 'dismissed';
  created_at: string;
  current_stock: number;
  stock_gap_preview: number;
  stockout_risk_preview: 'HIGH' | 'MEDIUM' | 'LOW' | 'N/A';
}

export interface ForecastHistoryItem {
  id: number;
  product_id: string;
  forecast_date: string;
  horizon_days: number;
  predicted_sales: number;
  model_used: string;
  status: 'active' | 'acted_on' | 'dismissed';
  created_at: string;
  actual_sales?: number | null;
  error?: number | null;
  error_pct?: number | null;
  is_completed: boolean;
  accuracy_note?: string | null;
}

export interface ForecastActRequest {
  action: 'trigger_inventory_check' | 'adjust_stock' | 'dismiss';
  stock_adjustment?: number | null;
}

export interface ForecastActResponse {
  forecast_id: number;
  action: string;
  status: string;
  recommendation_id?: number | null;
  recommendation?: any;
  current_stock?: number | null;
  message: string;
}

export const runProductForecast = async (
  productId: string,
  horizonDays: number = 7
): Promise<ForecastResponse> => {
  const res = await api.post<ForecastResponse>(`/api/products/${productId}/forecast`, {
    horizon_days: horizonDays,
  });
  return res.data;
};

export const getProductForecasts = async (
  productId: string
): Promise<ForecastHistoryItem[]> => {
  const res = await api.get<ForecastHistoryItem[]>(`/api/products/${productId}/forecasts`);
  return res.data;
};

export const actOnForecast = async (
  forecastId: number,
  data: ForecastActRequest
): Promise<ForecastActResponse> => {
  const res = await api.post<ForecastActResponse>(`/api/forecasts/${forecastId}/act`, data);
  return res.data;
};

// ── 6. Suppliers & Purchase Orders ───────────────────────────────────────────

export interface Supplier {
  id: number;
  name: string;
  contact_name?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  category?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface SupplierCreate {
  name: string;
  contact_name?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  category?: string | null;
}

export interface PurchaseOrderItem {
  id: number;
  purchase_order_id: number;
  product_id: string;
  quantity: number;
  unit_cost: number;
  total_cost: number;
  product_name?: string | null;
  product_sku?: string | null;
}

export interface PurchaseOrderItemCreate {
  product_id: string;
  quantity: number;
  unit_cost?: number;
}

export interface PurchaseOrder {
  id: number;
  po_number: string;
  supplier_id?: number | null;
  supplier_name?: string | null;
  status: 'DRAFT' | 'PENDING_APPROVAL' | 'APPROVED' | 'ORDERED' | 'RECEIVED' | 'CANCELLED' | 'REJECTED';
  total_amount: number;
  priority: string;
  reason?: string | null;
  notes?: string | null;
  created_at: string;
  approved_at?: string | null;
  ordered_at?: string | null;
  received_at?: string | null;
  items: PurchaseOrderItem[];
}

export interface PurchaseOrderCreate {
  supplier_id?: number | null;
  priority?: string;
  reason?: string | null;
  notes?: string | null;
  items: PurchaseOrderItemCreate[];
}

export const getSuppliers = async (activeOnly: boolean = false): Promise<Supplier[]> => {
  const res = await api.get<Supplier[]>('/api/suppliers', { params: { active_only: activeOnly } });
  return res.data;
};

export const createSupplier = async (data: SupplierCreate): Promise<Supplier> => {
  const res = await api.post<Supplier>('/api/suppliers', data);
  return res.data;
};

export const getPurchaseOrders = async (status?: string, supplierId?: number): Promise<PurchaseOrder[]> => {
  const params: any = {};
  if (status) params.status = status;
  if (supplierId) params.supplier_id = supplierId;
  const res = await api.get<PurchaseOrder[]>('/api/purchase-orders', { params });
  return res.data;
};

export const createPurchaseOrder = async (data: PurchaseOrderCreate): Promise<PurchaseOrder> => {
  const res = await api.post<PurchaseOrder>('/api/purchase-orders', data);
  return res.data;
};

export const getPurchaseOrder = async (id: number): Promise<PurchaseOrder> => {
  const res = await api.get<PurchaseOrder>(`/api/purchase-orders/${id}`);
  return res.data;
};

export const updatePurchaseOrderStatus = async (id: number, status: string, notes?: string): Promise<PurchaseOrder> => {
  const res = await api.patch<PurchaseOrder>(`/api/purchase-orders/${id}/status`, { status, notes });
  return res.data;
};

export const receivePurchaseOrder = async (id: number): Promise<PurchaseOrder> => {
  const res = await api.post<PurchaseOrder>(`/api/purchase-orders/${id}/receive`);
  return res.data;
};

// ── 7. Automation & Settings ─────────────────────────────────────────────────

export interface CriticalInventoryItem {
  id: string;
  name: string;
  sku?: string;
  current_stock: number;
  reorder_level: number;
  urgency: 'CRITICAL' | 'HIGH';
}

export interface AutomationStatus {
  autonomous_mode: boolean;
  operational_thresholds: {
    safety_stock_days: number;
    review_period_days: number;
    khata_overdue_days: number;
    expense_anomaly_threshold_pct: number;
    high_risk_multiplier: number;
    medium_risk_multiplier: number;
  };
  agents: { name: string; type: string; status: string }[];
  pending_recommendations_count: number;
  audit_logs_count: number;
  recent_runs: any[];
  critical_inventory?: CriticalInventoryItem[];
  khata_summary?: {
    total_overdue: number;
    overdue_count: number;
    top_overdue: { customer_name: string; amount: number; days_overdue: number }[];
  };
  replenishment_summary?: {
    pending_po_count: number;
    total_po_value: number;
  };
  solvency_summary?: {
    current_cash: number;
    min_reserve: number;
    status: 'SOLVENT' | 'LOW_RESERVE';
  };
}

export interface BusinessSettings {
  id: number;
  min_cash_reserve: number;
  currency: string;
  safety_stock_days: number;
  review_period_days: number;
  khata_overdue_days: number;
  expense_anomaly_threshold_pct: number;
  high_risk_multiplier: number;
  medium_risk_multiplier: number;
  autonomous_mode: boolean;
}

export interface BusinessSettingsUpdate {
  min_cash_reserve?: number;
  currency?: string;
  safety_stock_days?: number;
  review_period_days?: number;
  khata_overdue_days?: number;
  expense_anomaly_threshold_pct?: number;
  high_risk_multiplier?: number;
  medium_risk_multiplier?: number;
  autonomous_mode?: boolean;
}

export const getAutomationStatus = async (): Promise<AutomationStatus> => {
  const res = await api.get<AutomationStatus>('/api/automation/status');
  return res.data;
};

export const toggleAutonomousMode = async (): Promise<BusinessSettings> => {
  const res = await api.post<BusinessSettings>('/api/settings/toggle-autonomous');
  return res.data;
};

