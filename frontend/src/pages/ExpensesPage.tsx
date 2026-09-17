import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  getExpenses,
  createExpense,
  checkExpenseTrend,
  Expense,
  ExpenseCreate,
  CheckExpenseTrendResponse,
} from '../api';

const DEFAULT_CATEGORIES = [
  'Rent',
  'Utilities',
  'Employee Wages',
  'Marketing',
  'Inventory COGS',
  'Software & SaaS',
  'Equipment & Maintenance',
  'General',
];

export const ExpensesPage: React.FC = () => {
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [loading, setLoading] = useState<boolean>(true);
  const [logging, setLogging] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Trend analysis state
  const [checkingCategory, setCheckingCategory] = useState<string | null>(null);
  const [trendResult, setTrendResult] = useState<CheckExpenseTrendResponse | null>(null);

  const [formData, setFormData] = useState<ExpenseCreate>({
    category: 'Rent',
    current_period_amount: 0,
    description: '',
    date: new Date().toISOString().split('T')[0],
  });

  const loadExpenses = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getExpenses(selectedCategory === 'ALL' ? undefined : selectedCategory);
      setExpenses(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load expenses');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadExpenses();
  }, [selectedCategory]);

  const handleCreateExpense = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLogging(true);
      setError(null);
      await createExpense({
        category: formData.category,
        description: formData.description,
        current_period_amount: Number(formData.current_period_amount),
        date: formData.date,
      });

      setFormData((prev) => ({
        ...prev,
        current_period_amount: 0,
        description: '',
      }));
      await loadExpenses();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to log expense');
    } finally {
      setLogging(false);
    }
  };

  const handleCheckTrend = async (category: string) => {
    try {
      setCheckingCategory(category);
      setError(null);
      const res = await checkExpenseTrend(category);
      setTrendResult(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to check expense trend');
    } finally {
      setCheckingCategory(null);
    }
  };

  const uniqueCategories = Array.from(new Set(['ALL', ...DEFAULT_CATEGORIES, ...expenses.map((e) => e.category)]));

  const totalSpent = expenses.reduce((sum, e) => sum + e.current_period_amount, 0);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Expense Management & Trend Analytics</h1>
          <p className="page-subtitle">Log business expenditures and detect sudden budget inflation spikes</p>
        </div>
      </div>

      {error && <div className="error-banner">⚠️ {error}</div>}

      {/* Trend Result Card */}
      {trendResult && (
        <div className="card" style={{ borderColor: '#ef4444', background: 'rgba(30, 27, 75, 0.4)' }}>
          <div className="card-header">
            <div className="card-title" style={{ color: '#fca5a5', display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>💸 Live Expense Trend Agent Assessment: {trendResult.category}</span>
              <span
                className={`badge ${
                  trendResult.agent_result.risk === 'HIGH'
                    ? 'badge-high'
                    : trendResult.agent_result.risk === 'MEDIUM'
                    ? 'badge-medium'
                    : 'badge-low'
                }`}
              >
                {trendResult.agent_result.risk} RISK
              </span>
            </div>
            {trendResult.recommendation_created && (
              <Link to="/recommendations" className="btn btn-danger btn-sm">
                Budget Review Action Queued in Inbox →
              </Link>
            )}
          </div>

          <div className="agent-metric-grid">
            <div className="agent-metric">
              <div className="agent-metric-val">₹{trendResult.agent_result.current_period_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
              <div className="agent-metric-lbl">Current Period Total (30d)</div>
            </div>
            <div className="agent-metric">
              <div className="agent-metric-val">₹{trendResult.agent_result.prior_period_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
              <div className="agent-metric-lbl">Prior Period Total (30d)</div>
            </div>
            <div className="agent-metric">
              <div
                className="agent-metric-val"
                style={{
                  color:
                    trendResult.agent_result.increase_pct && trendResult.agent_result.increase_pct > 30
                      ? '#ef4444'
                      : '#10b981',
                }}
              >
                {trendResult.agent_result.increase_pct !== null && trendResult.agent_result.increase_pct !== undefined
                  ? `${trendResult.agent_result.increase_pct > 0 ? '+' : ''}${trendResult.agent_result.increase_pct.toFixed(1)}%`
                  : 'N/A (New)'}
              </div>
              <div className="agent-metric-lbl">Period Delta %</div>
            </div>
            <div className="agent-metric">
              <div className="agent-metric-val" style={{ textTransform: 'capitalize', color: '#60a5fa' }}>
                {trendResult.agent_result.trend}
              </div>
              <div className="agent-metric-lbl">Detected Trend</div>
            </div>
          </div>
        </div>
      )}

      {/* Grid: Log Expense & Category Checkers */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 24, marginBottom: 28 }}>
        {/* Log Expense Card */}
        <div className="card">
          <h2 className="card-title" style={{ marginBottom: 16 }}>➕ Log Expenditure</h2>
          <form onSubmit={handleCreateExpense}>
            <div className="form-group" style={{ marginBottom: 14 }}>
              <label>Category *</label>
              <select
                className="form-control"
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                required
              >
                {DEFAULT_CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group" style={{ marginBottom: 14 }}>
              <label>Amount (₹) *</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                required
                className="form-control"
                placeholder="0.00"
                value={formData.current_period_amount || ''}
                onChange={(e) => setFormData({ ...formData, current_period_amount: Number(e.target.value) })}
              />
            </div>

            <div className="form-group" style={{ marginBottom: 14 }}>
              <label>Description / Vendor</label>
              <input
                type="text"
                className="form-control"
                placeholder="e.g. Monthly Electricity Bill or Warehouse Rent"
                value={formData.description || ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>

            <div className="form-group" style={{ marginBottom: 18 }}>
              <label>Expense Date</label>
              <input
                type="date"
                className="form-control"
                value={formData.date || ''}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
              />
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={logging}>
              {logging ? <span className="spinner"></span> : '💾 Record Expense'}
            </button>
          </form>
        </div>

        {/* Category Trend Scanners */}
        <div className="card">
          <h2 className="card-title" style={{ marginBottom: 12 }}>🔍 Fast Category Trend Audits</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: 16 }}>
            Run the autonomous expense agent to detect sudden spikes (&gt;30% increase) in any category.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {DEFAULT_CATEGORIES.slice(0, 6).map((cat) => (
              <div
                key={cat}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '8px 12px',
                  background: 'var(--bg-main)',
                  borderRadius: 8,
                }}
              >
                <span style={{ fontWeight: 500 }}>{cat}</span>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => handleCheckTrend(cat)}
                  disabled={checkingCategory === cat}
                >
                  {checkingCategory === cat ? <span className="spinner"></span> : 'Check Trend →'}
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Category Filter Tabs */}
      <div className="tabs-nav">
        {uniqueCategories.map((cat) => (
          <button
            key={cat}
            className={`tab-btn ${selectedCategory === cat ? 'active' : ''}`}
            onClick={() => setSelectedCategory(cat)}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Expense History Table */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            Expense Records ({expenses.length}) — Total: ₹{totalSpent.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </h2>
          {selectedCategory !== 'ALL' && (
            <button
              className="btn btn-primary btn-sm"
              onClick={() => handleCheckTrend(selectedCategory)}
              disabled={checkingCategory === selectedCategory}
            >
              {checkingCategory === selectedCategory ? <span className="spinner"></span> : `Audit ${selectedCategory} Trend`}
            </button>
          )}
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Date</th>
                <th>Category</th>
                <th>Description</th>
                <th>Amount</th>
                <th>Category Audit</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: 32 }}>
                    <span className="spinner"></span> Loading expense ledger...
                  </td>
                </tr>
              ) : expenses.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: 32 }}>
                    No expenses logged in this category.
                  </td>
                </tr>
              ) : (
                expenses.map((exp) => (
                  <tr key={exp.id}>
                    <td style={{ fontFamily: 'JetBrains Mono', color: 'var(--text-muted)' }}>#{exp.id}</td>
                    <td>{exp.date || '—'}</td>
                    <td>
                      <strong style={{ color: '#60a5fa' }}>{exp.category}</strong>
                    </td>
                    <td>{exp.description || '—'}</td>
                    <td>
                      <strong style={{ color: '#f87171' }}>₹{exp.current_period_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong>
                    </td>
                    <td>
                      <button
                        className="btn btn-outline btn-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCheckTrend(exp.category);
                        }}
                      >
                        Audit Trend
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
