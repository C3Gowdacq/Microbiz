import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  getDashboardSummary,
  runFullPipeline,
  getRecommendations,
  approveRecommendation,
  rejectRecommendation,
  DashboardSummary,
  RecommendationRecord,
  FullPipelineResponse,
} from '../api';

export const DashboardPage: React.FC = () => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [pendingRecs, setPendingRecs] = useState<RecommendationRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [runningPipeline, setRunningPipeline] = useState<boolean>(false);
  const [pipelineResult, setPipelineResult] = useState<FullPipelineResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [sumData, recsData] = await Promise.all([
        getDashboardSummary(),
        getRecommendations('pending'),
      ]);
      setSummary(sumData);
      setPendingRecs(recsData.slice(0, 5));
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRunPipeline = async () => {
    try {
      setRunningPipeline(true);
      setError(null);
      const result = await runFullPipeline();
      setPipelineResult(result);
      await loadData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Error running full business health check');
    } finally {
      setRunningPipeline(false);
    }
  };

  const handleQuickApprove = async (id: number) => {
    try {
      await approveRecommendation(id);
      await loadData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to approve recommendation');
    }
  };

  const handleQuickReject = async (id: number) => {
    try {
      await rejectRecommendation(id);
      await loadData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to reject recommendation');
    }
  };

  const currencySymbol = summary?.currency === 'USD' ? '$' : summary?.currency === 'EUR' ? '€' : '₹';

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Executive Dashboard</h1>
          <p className="page-subtitle">Real-time enterprise metrics & autonomous intelligence overview</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary btn-sm" onClick={loadData} disabled={loading}>
            🔄 Refresh
          </button>
        </div>
      </div>

      {error && <div className="error-banner">⚠️ {error}</div>}

      {/* KPI Grid */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-label">Today's Revenue</div>
          <div className="kpi-value">
            {currencySymbol}
            {summary ? summary.today_sales_revenue.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '0.00'}
          </div>
          <div className="kpi-sub">Aggregated from today's sales</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Net Cash Position</div>
          <div className="kpi-value" style={{ color: (summary?.total_cash_position || 0) >= 0 ? '#10b981' : '#f87171' }}>
            {currencySymbol}
            {summary ? summary.total_cash_position.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '0.00'}
          </div>
          <div className="kpi-sub">Sales − Expenses − Reserve</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Low Stock Products</div>
          <div className="kpi-value" style={{ color: (summary?.low_stock_products_count || 0) > 0 ? '#f59e0b' : '#f8fafc' }}>
            {summary?.low_stock_products_count ?? 0}
          </div>
          <div className="kpi-sub">Stock below reorder level</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Overdue Invoices</div>
          <div className="kpi-value" style={{ color: (summary?.overdue_invoices_count || 0) > 0 ? '#ef4444' : '#f8fafc' }}>
            {summary?.overdue_invoices_count ?? 0}
          </div>
          <div className="kpi-sub">Unpaid past due date</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Pending AI Actions</div>
          <div className="kpi-value" style={{ color: (summary?.pending_recommendations_count || 0) > 0 ? '#818cf8' : '#f8fafc' }}>
            {summary?.pending_recommendations_count ?? 0}
          </div>
          <div className="kpi-sub">Awaiting shopkeeper review</div>
        </div>
      </div>

      {/* Autonomous Health Check Hero */}
      <div className="hero-banner">
        <div className="hero-text">
          <h3>⚡ Autonomous Business Health Check</h3>
          <p>
            Run all 5 AI agents simultaneously over live inventory, customer credit balances, expense trends, and cash flow projections from the SQLite database.
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={handleRunPipeline}
          disabled={runningPipeline}
          style={{ whiteSpace: 'nowrap' }}
        >
          {runningPipeline ? (
            <>
              <span className="spinner"></span>
              <span>Scanning All Agents...</span>
            </>
          ) : (
            <>
              <span>🚀 Run Full Business Health Check</span>
            </>
          )}
        </button>
      </div>

      {/* Pipeline Result Toast / Box */}
      {pipelineResult && (
        <div className="card" style={{ borderColor: '#6366f1', background: 'rgba(30, 27, 75, 0.4)' }}>
          <div className="card-header">
            <div className="card-title">✅ Health Check Completed (Rec #{pipelineResult.recommendation_id})</div>
            <Link to="/recommendations" className="btn btn-secondary btn-sm">
              View in Inbox →
            </Link>
          </div>
          <p style={{ marginBottom: 12, color: '#e0e7ff' }}>
            <strong>Primary Action:</strong>{' '}
            <span style={{ textTransform: 'capitalize', color: '#60a5fa', fontWeight: 700 }}>
              {pipelineResult.decision?.primary_recommendation?.action}
            </span>{' '}
            ({pipelineResult.decision?.primary_recommendation?.priority} priority)
          </p>
          <p style={{ color: '#cbd5e1', fontSize: '0.95rem' }}>{pipelineResult.decision?.summary}</p>
        </div>
      )}

      {/* Pending Recommendations Inbox Preview */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">🚨 Actionable AI Recommendations (Pending Review)</div>
          <Link to="/recommendations" className="btn btn-outline btn-sm">
            View All ({summary?.pending_recommendations_count ?? 0}) →
          </Link>
        </div>

        {pendingRecs.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">✨</div>
            <p>No pending recommendations! All systems operating smoothly or all actions reviewed.</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {pendingRecs.map((rec) => (
              <div
                key={rec.id}
                style={{
                  background: 'var(--bg-main)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 10,
                  padding: '16px 20px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: 12,
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span className="badge badge-high">{rec.priority}</span>
                    <strong style={{ textTransform: 'capitalize', color: '#60a5fa' }}>{rec.primary_action}</strong>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                      #{rec.id} • {new Date(rec.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <div style={{ color: '#cbd5e1', fontSize: '0.9rem', maxWidth: 700 }}>{rec.reason}</div>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn btn-success btn-sm" onClick={() => handleQuickApprove(rec.id)}>
                    ✓ Approve
                  </button>
                  <button className="btn btn-danger btn-sm" onClick={() => handleQuickReject(rec.id)}>
                    ✕ Dismiss
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Navigation Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16 }}>
        <Link to="/products" className="card" style={{ textDecoration: 'none', transition: 'transform 0.2s' }}>
          <div style={{ fontSize: '1.5rem', marginBottom: 8 }}>📦</div>
          <div className="card-title">Manage Inventory</div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Check stockout risks, record deliveries, and inspect product margins.
          </p>
        </Link>

        <Link to="/sales" className="card" style={{ textDecoration: 'none', transition: 'transform 0.2s' }}>
          <div style={{ fontSize: '1.5rem', marginBottom: 8 }}>🛒</div>
          <div className="card-title">Record POS Sale</div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Log item purchases with automatic stock decrementing & ledger update.
          </p>
        </Link>

        <Link to="/customers" className="card" style={{ textDecoration: 'none', transition: 'transform 0.2s' }}>
          <div style={{ fontSize: '1.5rem', marginBottom: 8 }}>👥</div>
          <div className="card-title">Customers & Credit</div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Inspect outstanding balances, generate invoices, and record customer payments.
          </p>
        </Link>
      </div>
    </div>
  );
};
