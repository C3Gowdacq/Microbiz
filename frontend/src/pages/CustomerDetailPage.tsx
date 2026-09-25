import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  getCustomer,
  getCustomerSummary,
  createInvoice,
  recordPayment,
  checkCustomerCredit,
  Customer,
  CustomerSummary,
  InvoiceSummaryItem,
  CheckCreditResponse,
} from '../api';

export const CustomerDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [customer, setCustomer] = useState<Customer | null>(null);
  const [summary, setSummary] = useState<CustomerSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Agent State
  const [checkingCredit, setCheckingCredit] = useState<boolean>(false);
  const [creditResult, setCreditResult] = useState<CheckCreditResponse | null>(null);

  // Invoice Modal State
  const [showInvoiceModal, setShowInvoiceModal] = useState<boolean>(false);
  const [creatingInvoice, setCreatingInvoice] = useState<boolean>(false);
  const [invoiceAmount, setInvoiceAmount] = useState<number>(100);
  const [invoiceDueDate, setInvoiceDueDate] = useState<string>(
    new Date(Date.now() + 14 * 86400000).toISOString().split('T')[0]
  );

  // Payment Modal State
  const [showPaymentModal, setShowPaymentModal] = useState<boolean>(false);
  const [selectedInvoice, setSelectedInvoice] = useState<InvoiceSummaryItem | null>(null);
  const [paymentAmount, setPaymentAmount] = useState<number>(0);
  const [recordingPayment, setRecordingPayment] = useState<boolean>(false);

  const loadCustomerData = async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const [cust, sum] = await Promise.all([
        getCustomer(id),
        getCustomerSummary(id),
      ]);
      setCustomer(cust);
      setSummary(sum);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load customer account');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCustomerData();
  }, [id]);

  const handleCheckCreditRisk = async () => {
    if (!id) return;
    try {
      setCheckingCredit(true);
      setError(null);
      const res = await checkCustomerCredit(id);
      setCreditResult(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Credit check failed');
    } finally {
      setCheckingCredit(false);
    }
  };

  const handleCreateInvoice = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    try {
      setCreatingInvoice(true);
      setError(null);
      await createInvoice({
        customer_id: id,
        invoice_amount: Number(invoiceAmount),
        due_date: invoiceDueDate || undefined,
      });
      setShowInvoiceModal(false);
      await loadCustomerData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to create invoice');
    } finally {
      setCreatingInvoice(false);
    }
  };

  const fillSampleInvoice = () => {
    setInvoiceAmount(14500);
    const in15Days = new Date();
    in15Days.setDate(in15Days.getDate() + 15);
    setInvoiceDueDate(in15Days.toISOString().split('T')[0]);
  };

  const handleOpenPayment = (inv: InvoiceSummaryItem) => {
    setSelectedInvoice(inv);
    setPaymentAmount(inv.invoice_amount - inv.amount_paid);
    setShowPaymentModal(true);
  };

  const handleRecordPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInvoice) return;
    try {
      setRecordingPayment(true);
      setError(null);
      await recordPayment(selectedInvoice.invoice_id, {
        payment_date: new Date().toISOString().split('T')[0],
        amount: Number(paymentAmount),
      });
      setShowPaymentModal(false);
      setSelectedInvoice(null);
      await loadCustomerData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to record payment');
    } finally {
      setRecordingPayment(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 48 }}>
        <span className="spinner"></span> Loading customer account...
      </div>
    );
  }

  if (!customer) {
    return (
      <div className="empty-state">
        <h2>Customer not found</h2>
        <button className="btn btn-secondary" onClick={() => navigate('/customers')} style={{ marginTop: 16 }}>
          ← Back to Customers
        </button>
      </div>
    );
  }

  const balance = summary?.outstanding_balance ?? 0;
  const daysOverdue = summary?.days_overdue;
  const isOverdue = daysOverdue !== undefined && daysOverdue !== null && daysOverdue > 0;

  return (
    <div>
      <div className="page-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
            <Link to="/customers" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>
              ← Customers
            </Link>
            <span style={{ color: 'var(--text-muted)' }}>/</span>
            <span style={{ fontFamily: 'JetBrains Mono', color: '#94a3b8' }}>{customer.id.slice(0, 8)}</span>
          </div>
          <h1 className="page-title">{customer.name}</h1>
          <p className="page-subtitle">{customer.email || 'No email'} • {customer.phone || 'No phone'}</p>
        </div>

        <div className="header-actions">
          <button className="btn btn-primary" onClick={handleCheckCreditRisk} disabled={checkingCredit}>
            {checkingCredit ? <span className="spinner"></span> : '🔍 Run Credit Risk Check'}
          </button>
          <button className="btn btn-secondary" onClick={() => setShowInvoiceModal(true)}>
            ➕ Issue Invoice
          </button>
        </div>
      </div>

      {error && <div className="error-banner">⚠️ {error}</div>}

      {/* Credit Agent Result Alert */}
      {creditResult && (
        <div className="card" style={{ borderColor: '#f59e0b', background: 'rgba(30, 27, 75, 0.5)' }}>
          <div className="card-header">
            <div className="card-title" style={{ color: '#fbbf24', display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>💳 Live Customer Credit Agent Analysis</span>
              {creditResult.agent_result && (
                <span
                  className={`badge ${
                    creditResult.agent_result.customer_risk === 'HIGH'
                      ? 'badge-high'
                      : creditResult.agent_result.customer_risk === 'MEDIUM'
                      ? 'badge-medium'
                      : 'badge-low'
                  }`}
                >
                  {creditResult.agent_result.customer_risk} RISK
                </span>
              )}
            </div>
            {creditResult.recommendation_created && (
              <Link to="/recommendations" className="btn btn-success btn-sm">
                Reminder Action Queued in Inbox →
              </Link>
            )}
          </div>

          {creditResult.agent_result ? (
            <div className="agent-metric-grid">
              <div className="agent-metric">
                <div className="agent-metric-val">₹{creditResult.agent_result.outstanding_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
                <div className="agent-metric-lbl">Outstanding Debt</div>
              </div>
              <div className="agent-metric">
                <div className="agent-metric-val" style={{ color: creditResult.agent_result.days_overdue > 0 ? '#ef4444' : '#10b981' }}>
                  {creditResult.agent_result.days_overdue} days
                </div>
                <div className="agent-metric-lbl">Days Overdue</div>
              </div>
              <div className="agent-metric">
                <div className="agent-metric-val" style={{ textTransform: 'capitalize', color: '#60a5fa' }}>
                  {creditResult.agent_result.recommended_action.replace('_', ' ')}
                </div>
                <div className="agent-metric-lbl">Recommended Action</div>
              </div>
            </div>
          ) : (
            <p style={{ color: '#a7f3d0' }}>{creditResult.message || 'No outstanding debt for this customer.'}</p>
          )}
        </div>
      )}

      {/* Account Overview Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 20, marginBottom: 28 }}>
        <div className="kpi-card">
          <div className="kpi-label">Outstanding Balance</div>
          <div className="kpi-value" style={{ color: balance > 0 ? '#f59e0b' : '#10b981' }}>
            ₹{balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div className="kpi-sub">{balance === 0 ? 'Account fully settled' : 'Unpaid invoices remaining'}</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Oldest Overdue Days</div>
          <div className="kpi-value" style={{ color: isOverdue ? '#ef4444' : '#10b981' }}>
            {daysOverdue ?? 0} days
          </div>
          <div className="kpi-sub">{isOverdue ? 'Overdue debt' : 'No overdue invoices'}</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Total Invoices</div>
          <div className="kpi-value">{summary?.invoice_history.length ?? 0}</div>
          <div className="kpi-sub">Lifetime transactions</div>
        </div>
      </div>

      {/* Invoice Ledger Table */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Invoices & Payment History</h2>
          <button className="btn btn-primary btn-sm" onClick={() => setShowInvoiceModal(true)}>
            ➕ Create Invoice
          </button>
        </div>

        {summary?.invoice_history.length === 0 ? (
          <div className="empty-state">
            <p>No invoices created for this customer yet.</p>
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Invoice ID</th>
                  <th>Amount</th>
                  <th>Amount Paid</th>
                  <th>Remaining</th>
                  <th>Due Date</th>
                  <th>Status</th>
                  <th>Payment Action</th>
                </tr>
              </thead>
              <tbody>
                {summary?.invoice_history.map((inv) => {
                  const remaining = inv.invoice_amount - inv.amount_paid;

                  return (
                    <tr key={inv.invoice_id}>
                      <td style={{ fontFamily: 'JetBrains Mono' }}>#{inv.invoice_id}</td>
                      <td><strong>₹{inv.invoice_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong></td>
                      <td>₹{inv.amount_paid.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                      <td>
                        <strong style={{ color: remaining > 0 ? '#f59e0b' : '#10b981' }}>
                          ₹{remaining.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </strong>
                      </td>
                      <td>
                        {inv.due_date ? (
                          <span>{inv.due_date}</span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>None set</span>
                        )}
                      </td>
                      <td>
                        <span
                          className={`badge ${
                            inv.status === 'paid'
                              ? 'badge-paid'
                              : inv.status === 'partially_paid'
                              ? 'badge-partial'
                              : 'badge-unpaid'
                          }`}
                        >
                          {inv.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td>
                        {inv.status !== 'paid' ? (
                          <button className="btn btn-success btn-sm" onClick={() => handleOpenPayment(inv)}>
                            💳 Pay Invoice
                          </button>
                        ) : (
                          <span style={{ color: '#10b981', fontSize: '0.85rem' }}>✓ Paid Full</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Invoice Modal */}
      {showInvoiceModal && (
        <div className="modal-overlay" onClick={() => setShowInvoiceModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">➕ Issue New Invoice</h2>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <button
                  type="button"
                  className="btn btn-sm btn-secondary"
                  onClick={fillSampleInvoice}
                  style={{ background: '#fef3c7', color: '#b45309', border: '1px solid #fde68a', fontWeight: 600 }}
                  title="Auto-fill sample trade invoice amount & due date"
                >
                  ✨ Auto-Fill Sample Data
                </button>
                <button className="modal-close" onClick={() => setShowInvoiceModal(false)}>
                  ×
                </button>
              </div>
            </div>

            <form onSubmit={handleCreateInvoice}>
              <div className="form-group" style={{ marginBottom: 16 }}>
                <label>Invoice Amount (₹) *</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  required
                  className="form-control"
                  value={invoiceAmount}
                  onChange={(e) => setInvoiceAmount(Number(e.target.value))}
                />
              </div>

              <div className="form-group" style={{ marginBottom: 20 }}>
                <label>Payment Due Date (Select past date to test overdue scenarios) *</label>
                <input
                  type="date"
                  required
                  className="form-control"
                  value={invoiceDueDate}
                  onChange={(e) => setInvoiceDueDate(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowInvoiceModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={creatingInvoice}>
                  {creatingInvoice ? 'Issuing...' : 'Issue Invoice'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Record Payment Modal */}
      {showPaymentModal && selectedInvoice && (
        <div className="modal-overlay" onClick={() => setShowPaymentModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">💳 Record Customer Payment</h2>
              <button className="modal-close" onClick={() => setShowPaymentModal(false)}>
                ×
              </button>
            </div>

            <div style={{ background: 'var(--bg-main)', padding: 14, borderRadius: 8, marginBottom: 18 }}>
              <div>
                <strong>Invoice #{selectedInvoice.invoice_id}</strong>
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                Total: ₹{selectedInvoice.invoice_amount.toFixed(2)} | Paid: ₹{selectedInvoice.amount_paid.toFixed(2)} | Remaining: ₹
                {(selectedInvoice.invoice_amount - selectedInvoice.amount_paid).toFixed(2)}
              </div>
            </div>

            <form onSubmit={handleRecordPayment}>
              <div className="form-group" style={{ marginBottom: 20 }}>
                <label>Payment Amount (₹) *</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  max={selectedInvoice.invoice_amount - selectedInvoice.amount_paid}
                  required
                  className="form-control"
                  value={paymentAmount}
                  onChange={(e) => setPaymentAmount(Number(e.target.value))}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowPaymentModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-success" disabled={recordingPayment}>
                  {recordingPayment ? 'Recording...' : 'Confirm Payment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
