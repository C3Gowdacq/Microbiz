import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  getDashboardSummary,
  runFullPipeline,
  getRecommendations,
  approveRecommendation,
  rejectRecommendation,
  getSettings,
  getProducts,
  getInvoices,
  getCustomers,
  DashboardSummary,
  RecommendationRecord,
  FullPipelineResponse,
  Product,
  Invoice,
  Customer,
} from '../api';

export const DashboardPage: React.FC = () => {
  const [isAutonomous, setIsAutonomous] = useState<boolean>(true);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [pendingRecs, setPendingRecs] = useState<RecommendationRecord[]>([]);
  const [lowStockProducts, setLowStockProducts] = useState<Product[]>([]);
  const [unpaidInvoices, setUnpaidInvoices] = useState<Invoice[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [runningPipeline, setRunningPipeline] = useState<boolean>(false);
  const [pipelineResult, setPipelineResult] = useState<FullPipelineResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Sync mode from settings and event
  useEffect(() => {
    const fetchMode = async () => {
      try {
        const settings = await getSettings();
        setIsAutonomous(settings.autonomous_mode);
      } catch {}
    };
    fetchMode();

    const handleModeChange = (e: any) => {
      if (typeof e.detail === 'boolean') {
        setIsAutonomous(e.detail);
      } else {
        fetchMode();
      }
    };
    window.addEventListener('modeChange', handleModeChange);
    return () => window.removeEventListener('modeChange', handleModeChange);
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Always load dashboard summary
      const sumData = await getDashboardSummary();
      setSummary(sumData);

      // Mode-specific data loading
      if (isAutonomous) {
        // In Autonomous Mode: load pending AI recommendations for HITL review
        const recsData = await getRecommendations('pending');
        setPendingRecs(recsData.slice(0, 6));
      } else {
        // In Manual Mode: load inventory products, unpaid invoices, and customers for storekeeper manual operations
        const [prodData, invData, custData] = await Promise.all([
          getProducts().catch(() => []),
          getInvoices().catch(() => []),
          getCustomers().catch(() => []),
        ]);
        const lowStock = prodData.filter((p) => p.current_stock <= p.reorder_level).slice(0, 6);
        setLowStockProducts(lowStock);
        const unpaid = invData.filter((i) => i.status !== 'paid').slice(0, 6);
        setUnpaidInvoices(unpaid);
        setCustomers(custData);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [isAutonomous]);

  const handleRunPipeline = async () => {
    try {
      setRunningPipeline(true);
      setError(null);
      const result = await runFullPipeline();
      setPipelineResult(result);
      setActionSuccess('Autonomous multi-agent health check completed successfully!');
      setTimeout(() => setActionSuccess(null), 5000);
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
      setActionSuccess(`Recommendation #${id} approved! PO / Action executed.`);
      setTimeout(() => setActionSuccess(null), 4000);
      await loadData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to approve recommendation');
    }
  };

  const handleQuickReject = async (id: number) => {
    try {
      await rejectRecommendation(id);
      setActionSuccess(`Recommendation #${id} dismissed.`);
      setTimeout(() => setActionSuccess(null), 4000);
      await loadData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to reject recommendation');
    }
  };

  const currencySymbol = summary?.currency === 'USD' ? '$' : summary?.currency === 'EUR' ? '€' : '₹';

  // Customer map for invoice names
  const customerMap = new Map<string, string>();
  customers.forEach((c) => customerMap.set(c.id, c.name));

  /* ========================================================================= */
  /*                      AUTONOMOUS MODE DASHBOARD                            */
  /* ========================================================================= */
  if (isAutonomous) {
    return (
      <div>
        {/* Page Header */}
        <div className="page-header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h1 className="page-title">Executive Dashboard</h1>
              <span
                style={{
                  background: '#f0fdf4',
                  color: '#15803d',
                  border: '1px solid #bbf7d0',
                  padding: '3px 10px',
                  borderRadius: '20px',
                  fontSize: '11px',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <span className="pulse-dot" style={{ width: '7px', height: '7px', background: '#16a34a', borderRadius: '50%' }}></span>
                Autonomous Loop Active
              </span>
            </div>
            <p className="page-subtitle">
              Closed-loop retail intelligence • Multi-agent automation & Human-In-The-Loop approvals
            </p>
          </div>
          <div className="header-actions">
            <button className="btn btn-secondary btn-sm" onClick={loadData} disabled={loading}>
              🔄 Refresh
            </button>
          </div>
        </div>

        {error && <div className="error-banner">⚠️ {error}</div>}
        {actionSuccess && <div className="success-banner" style={{ background: '#f0fdf4', color: '#15803d', border: '1px solid #bbf7d0', padding: '10px 16px', borderRadius: '8px', marginBottom: '16px', fontWeight: 600 }}>✅ {actionSuccess}</div>}

        {/* Autonomous KPI Grid */}
        <div className="kpi-grid">
          <div className="kpi-card">
            <div className="kpi-label">Today's Revenue (POS)</div>
            <div className="kpi-value">
              {currencySymbol}
              {summary ? summary.today_sales_revenue.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '0.00'}
            </div>
            <div className="kpi-sub">Aggregated from POS customer orders</div>
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
            <div className="kpi-label">Pending AI Approvals</div>
            <div className="kpi-value" style={{ color: (summary?.pending_recommendations_count || 0) > 0 ? '#e11d48' : '#10b981' }}>
              {summary?.pending_recommendations_count ?? 0}
            </div>
            <div className="kpi-sub">Awaiting shopkeeper 1-click review</div>
          </div>

          <div className="kpi-card">
            <div className="kpi-label">Autonomous Agents</div>
            <div className="kpi-value" style={{ color: '#2563eb' }}>
              5 / 5
            </div>
            <div className="kpi-sub">Inventory, Cash, Credit, Exp, Profit</div>
          </div>
        </div>

        {/* Autonomous Core Quick Actions (POS & AI Approvals only) */}
        <div
          style={{
            display: 'flex',
            gap: '12px',
            margin: '20px 0',
            flexWrap: 'wrap',
            background: '#ffffff',
            padding: '16px 20px',
            borderRadius: '12px',
            border: '1px solid var(--border-color)',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '12px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
              Shopkeeper Actions:
            </span>

            <Link to="/sales" style={{ textDecoration: 'none' }}>
              <button
                className="btn btn-primary btn-sm"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  background: '#e23744',
                  borderColor: '#e23744',
                  padding: '9px 18px',
                  fontSize: '13px',
                }}
              >
                <span>🛒</span>
                <span>Customer Order (POS)</span>
              </button>
            </Link>

            <Link to="/recommendations" style={{ textDecoration: 'none' }}>
              <button
                className="btn btn-secondary btn-sm"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '9px 18px',
                  fontSize: '13px',
                }}
              >
                <span>🤖</span>
                <span>Review AI Approvals ({summary?.pending_recommendations_count ?? 0})</span>
              </button>
            </Link>
          </div>

          <button
            className="btn btn-outline btn-sm"
            onClick={handleRunPipeline}
            disabled={runningPipeline}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px' }}
          >
            {runningPipeline ? (
              <>
                <span className="spinner"></span>
                <span>Scanning 5 Agents...</span>
              </>
            ) : (
              <>
                <span>⚡</span>
                <span>Trigger Live Store Sweep</span>
              </>
            )}
          </button>
        </div>

        {/* Advanced AI Architecture & Research Showcase (Guide Pitch Highlight) */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
          gap: '16px',
          marginBottom: '24px'
        }}>
          {/* Card 1: LangGraph DAG */}
          <div style={{
            background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%)',
            borderRadius: '14px',
            padding: '20px 24px',
            color: '#f8fafc',
            border: '1px solid #312e81',
            boxShadow: '0 4px 20px rgba(15, 23, 42, 0.15)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            position: 'relative',
            overflow: 'hidden'
          }}>
            <div style={{
              position: 'absolute',
              top: '-15px',
              right: '-15px',
              width: '90px',
              height: '90px',
              background: 'radial-gradient(circle, rgba(99,102,241,0.25) 0%, transparent 70%)',
              borderRadius: '50%'
            }}></div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                <span style={{
                  fontSize: '11px',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  background: 'rgba(99, 102, 241, 0.25)',
                  color: '#a5b4fc',
                  padding: '4px 10px',
                  borderRadius: '20px',
                  border: '1px solid rgba(99, 102, 241, 0.4)'
                }}>
                  Multi-Agent Architecture
                </span>
                <span style={{ fontSize: '12px', color: '#94a3b8' }}>8 StateGraph Nodes</span>
              </div>
              <h3 style={{ fontSize: '17px', fontWeight: 700, color: '#ffffff', margin: '0 0 6px 0' }}>
                🧠 LangGraph StateGraph DAG
              </h3>
              <p style={{ fontSize: '13px', color: '#cbd5e1', lineHeight: '1.45', margin: '0 0 16px 0' }}>
                Inspect real-time agent execution telemetry, parallel state reducers, and active Pareto conflict resolution between conflicting stock & cash policies.
              </p>
            </div>
            <Link to="/agent-graph" style={{ textDecoration: 'none' }}>
              <button style={{
                width: '100%',
                background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                color: '#ffffff',
                border: 'none',
                padding: '10px 16px',
                borderRadius: '8px',
                fontWeight: 600,
                fontSize: '13px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                transition: 'all 0.2s ease',
                boxShadow: '0 2px 8px rgba(79, 70, 229, 0.3)'
              }}>
                <span>Open Interactive Graph & Telemetry</span>
                <span>→</span>
              </button>
            </Link>
          </div>

          {/* Card 2: Digital Twin Sandbox */}
          <div style={{
            background: 'linear-gradient(135deg, #092c24 0%, #064e3b 100%)',
            borderRadius: '14px',
            padding: '20px 24px',
            color: '#f8fafc',
            border: '1px solid #065f46',
            boxShadow: '0 4px 20px rgba(6, 78, 59, 0.15)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            position: 'relative',
            overflow: 'hidden'
          }}>
            <div style={{
              position: 'absolute',
              top: '-15px',
              right: '-15px',
              width: '90px',
              height: '90px',
              background: 'radial-gradient(circle, rgba(16,185,129,0.25) 0%, transparent 70%)',
              borderRadius: '50%'
            }}></div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                <span style={{
                  fontSize: '11px',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  background: 'rgba(16, 185, 129, 0.25)',
                  color: '#6ee7b7',
                  padding: '4px 10px',
                  borderRadius: '20px',
                  border: '1px solid rgba(16, 185, 129, 0.4)'
                }}>
                  Stochastic Simulation
                </span>
                <span style={{ fontSize: '12px', color: '#a7f3d0' }}>1,000 Monte Carlo Iterations</span>
              </div>
              <h3 style={{ fontSize: '17px', fontWeight: 700, color: '#ffffff', margin: '0 0 6px 0' }}>
                🎲 Kirana Digital Twin Sandbox
              </h3>
              <p style={{ fontSize: '13px', color: '#d1fae5', lineHeight: '1.45', margin: '0 0 16px 0' }}>
                Stress-test 90-day cash solvency against inflation, demand shocks, and khata defaults. Evaluates Value-at-Risk (VaR 95%) and survival probability.
              </p>
            </div>
            <Link to="/simulation" style={{ textDecoration: 'none' }}>
              <button style={{
                width: '100%',
                background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                color: '#ffffff',
                border: 'none',
                padding: '10px 16px',
                borderRadius: '8px',
                fontWeight: 600,
                fontSize: '13px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                transition: 'all 0.2s ease',
                boxShadow: '0 2px 8px rgba(16, 185, 129, 0.3)'
              }}>
                <span>Launch Monte Carlo Sandbox</span>
                <span>→</span>
              </button>
            </Link>
          </div>
        </div>

        {/* Pipeline Result Toast / Box */}
        {pipelineResult && (
          <div className="card" style={{ borderColor: '#6366f1', background: '#f5f3ff', marginBottom: '20px' }}>
            <div className="card-header">
              <div className="card-title" style={{ color: '#4338ca' }}>
                ✅ Store Health Sweep Complete (Recommendation #{pipelineResult.recommendation_id})
              </div>
              <Link to="/recommendations" className="btn btn-secondary btn-sm">
                View in Approvals Inbox →
              </Link>
            </div>
            <p style={{ marginBottom: 8, color: '#312e81' }}>
              <strong>Primary AI Action:</strong>{' '}
              <span style={{ textTransform: 'capitalize', color: '#4f46e5', fontWeight: 700 }}>
                {pipelineResult.decision?.primary_recommendation?.action}
              </span>{' '}
              ({pipelineResult.decision?.primary_recommendation?.priority} priority)
            </p>
            <p style={{ color: '#475569', fontSize: '0.92rem' }}>{pipelineResult.decision?.summary}</p>
          </div>
        )}

        {/* Pending HITL AI Approvals (The Shopkeeper's primary duty in Autonomous Mode) */}
        <div className="card" style={{ marginBottom: '24px' }}>
          <div className="card-header">
            <div>
              <div className="card-title">🚨 Actionable AI Decisions (Pending Shopkeeper Review)</div>
              <p style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
                High-priority interventions calculated by autonomous agents requiring your 1-click confirmation.
              </p>
            </div>
            <Link to="/recommendations" className="btn btn-outline btn-sm">
              View All Approvals ({summary?.pending_recommendations_count ?? 0}) →
            </Link>
          </div>

          {pendingRecs.length === 0 ? (
            <div className="empty-state" style={{ padding: '36px 20px', textAlign: 'center' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '8px' }}>✨</div>
              <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a' }}>All Autonomous Systems Green</h3>
              <p style={{ color: '#64748b', fontSize: '13px' }}>
                No pending AI approvals right now. The autonomous engine is monitoring stock, cash, and credit in the background.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {pendingRecs.map((rec) => (
                <div
                  key={rec.id}
                  style={{
                    background: '#ffffff',
                    border: '1px solid var(--border-color)',
                    borderRadius: 10,
                    padding: '16px 20px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: 12,
                    boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                  }}
                >
                  <div style={{ flex: 1, minWidth: '280px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span
                        className={`badge ${
                          rec.priority === 'high' ? 'badge-high' : rec.priority === 'medium' ? 'badge-medium' : 'badge-low'
                        }`}
                      >
                        {rec.priority}
                      </span>
                      <strong style={{ textTransform: 'capitalize', color: '#0f172a', fontSize: '14px' }}>
                        {rec.primary_action.replace(/_/g, ' ')}
                      </strong>
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                        #{rec.id} • {new Date(rec.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                    <div style={{ color: '#475569', fontSize: '0.9rem', lineHeight: '1.4' }}>
                      {rec.reason}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
                    <button
                      className="btn btn-success btn-sm"
                      onClick={() => handleQuickApprove(rec.id)}
                      title="Approve this autonomous action"
                    >
                      ✓ Approve
                    </button>
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={() => handleQuickReject(rec.id)}
                      title="Dismiss this recommendation"
                    >
                      ✕ Dismiss
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Live Multi-Agent Status Grid */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">⚡ Autonomous Multi-Agent Grid</div>
            <span style={{ fontSize: '12px', color: '#16a34a', fontWeight: 600 }}>● 5 of 5 Agents Synchronized</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
            <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <span style={{ fontSize: '18px' }}>📦</span>
                <strong style={{ fontSize: '13px', color: '#0f172a' }}>Inventory Sentinel</strong>
              </div>
              <p style={{ fontSize: '12px', color: '#64748b' }}>
                Auto-tracks sales velocity, calculates safety stock, and triggers purchase order drafts.
              </p>
            </div>

            <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <span style={{ fontSize: '18px' }}>💰</span>
                <strong style={{ fontSize: '13px', color: '#0f172a' }}>Cashflow Guardian</strong>
              </div>
              <p style={{ fontSize: '12px', color: '#64748b' }}>
                Enforces ₹50,000 cash reserve floor before approving any supplier purchase order disbursement.
              </p>
            </div>

            <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <span style={{ fontSize: '18px' }}>👥</span>
                <strong style={{ fontSize: '13px', color: '#0f172a' }}>Credit & Khata Copilot</strong>
              </div>
              <p style={{ fontSize: '12px', color: '#64748b' }}>
                Monitors overdue customer accounts and queues automated polite SMS collection payment links.
              </p>
            </div>

            <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <span style={{ fontSize: '18px' }}>💸</span>
                <strong style={{ fontSize: '13px', color: '#0f172a' }}>Expense Auditor</strong>
              </div>
              <p style={{ fontSize: '12px', color: '#64748b' }}>
                Detects anomalies in electricity, rent, and logistics overheads against prior period baselines.
              </p>
            </div>

            <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <span style={{ fontSize: '18px' }}>📈</span>
                <strong style={{ fontSize: '13px', color: '#0f172a' }}>Profit Optimizer</strong>
              </div>
              <p style={{ fontSize: '12px', color: '#64748b' }}>
                Evaluates gross margins across SKUs to prevent selling items at loss or unviable markup.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  /* ========================================================================= */
  /*                      MANUAL MODE DASHBOARD                                */
  /* ========================================================================= */
  return (
    <div>
      {/* Page Header */}
      <div className="page-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 className="page-title">Store Operations Dashboard</h1>
            <span
              style={{
                background: '#f1f5f9',
                color: '#475569',
                border: '1px solid #cbd5e1',
                padding: '3px 10px',
                borderRadius: '20px',
                fontSize: '11px',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              🔒 Manual Operations Mode
            </span>
          </div>
          <p className="page-subtitle">
            Traditional Kirana store management • Inventory, sales register, purchase orders & khata credit
          </p>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary btn-sm" onClick={loadData} disabled={loading}>
            🔄 Refresh
          </button>
        </div>
      </div>

      {error && <div className="error-banner">⚠️ {error}</div>}

      {/* Manual KPI Grid */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-label">Today's Revenue</div>
          <div className="kpi-value">
            {currencySymbol}
            {summary ? summary.today_sales_revenue.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '0.00'}
          </div>
          <div className="kpi-sub">Aggregated from today's sales register</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Net Cash Position</div>
          <div className="kpi-value" style={{ color: (summary?.total_cash_position || 0) >= 0 ? '#10b981' : '#f87171' }}>
            {currencySymbol}
            {summary ? summary.total_cash_position.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '0.00'}
          </div>
          <div className="kpi-sub">Cash available in store ledger</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Low Stock Products</div>
          <div className="kpi-value" style={{ color: (summary?.low_stock_products_count || 0) > 0 ? '#f59e0b' : '#10b981' }}>
            {summary?.low_stock_products_count ?? 0}
          </div>
          <div className="kpi-sub">Items requiring manual vendor reorders</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Overdue Khata Accounts</div>
          <div className="kpi-value" style={{ color: (summary?.overdue_invoices_count || 0) > 0 ? '#ef4444' : '#10b981' }}>
            {summary?.overdue_invoices_count ?? 0}
          </div>
          <div className="kpi-sub">Unpaid customer credit invoices</div>
        </div>
      </div>

      {/* Manual Quick Action Bar */}
      <div
        style={{
          display: 'flex',
          gap: '10px',
          margin: '20px 0',
          flexWrap: 'wrap',
          background: '#ffffff',
          padding: '14px 18px',
          borderRadius: '12px',
          border: '1px solid var(--border-color)',
          alignItems: 'center',
        }}
      >
        <span style={{ fontSize: '12px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginRight: '6px' }}>
          Manual Tools:
        </span>

        <Link to="/sales" style={{ textDecoration: 'none' }}>
          <button className="btn btn-primary btn-sm" style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#16a34a', borderColor: '#16a34a' }}>
            <span>🛒</span>
            <span>New POS Sale</span>
          </button>
        </Link>

        <Link to="/products" style={{ textDecoration: 'none' }}>
          <button className="btn btn-secondary btn-sm" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span>📦</span>
            <span>Manage Stock</span>
          </button>
        </Link>

        <Link to="/purchase-orders" style={{ textDecoration: 'none' }}>
          <button className="btn btn-secondary btn-sm" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span>📝</span>
            <span>Create Purchase Order</span>
          </button>
        </Link>

        <Link to="/customers" style={{ textDecoration: 'none' }}>
          <button className="btn btn-secondary btn-sm" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span>👥</span>
            <span>Customer Khata</span>
          </button>
        </Link>

        <Link to="/expenses" style={{ textDecoration: 'none' }}>
          <button className="btn btn-secondary btn-sm" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span>💸</span>
            <span>Record Expense</span>
          </button>
        </Link>

        <Link to="/forecasting" style={{ textDecoration: 'none' }}>
          <button className="btn btn-secondary btn-sm" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span>🔮</span>
            <span>Demand Forecasting</span>
          </button>
        </Link>
      </div>

      {/* Section 1: Critical Low Stock Items (Manual Reorder Alert) */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <div>
            <div className="card-title">⚠️ Critical Low Stock Products (Manual Reorder Needed)</div>
            <p style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
              Products whose current stock is at or below the minimum reorder threshold.
            </p>
          </div>
          <Link to="/products" className="btn btn-outline btn-sm">
            View All Stock →
          </Link>
        </div>

        {lowStockProducts.length === 0 ? (
          <div className="empty-state" style={{ padding: '28px 20px', textAlign: 'center' }}>
            <p style={{ color: '#64748b', fontSize: '13px' }}>All product stocks are at healthy operational levels.</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#f8fafc', textAlign: 'left', borderBottom: '1px solid #e2e8f0', fontSize: '12px', color: '#64748b' }}>
                  <th style={{ padding: '10px 14px' }}>Product</th>
                  <th style={{ padding: '10px 14px' }}>SKU</th>
                  <th style={{ padding: '10px 14px' }}>Current Stock</th>
                  <th style={{ padding: '10px 14px' }}>Reorder Level</th>
                  <th style={{ padding: '10px 14px' }}>Cost Price</th>
                  <th style={{ padding: '10px 14px', textAlign: 'right' }}>Manual Action</th>
                </tr>
              </thead>
              <tbody>
                {lowStockProducts.map((p) => (
                  <tr key={p.id} style={{ borderBottom: '1px solid #f1f5f9', fontSize: '13px' }}>
                    <td style={{ padding: '12px 14px', fontWeight: 600, color: '#0f172a' }}>{p.name}</td>
                    <td style={{ padding: '12px 14px', color: '#64748b' }}>{p.sku}</td>
                    <td style={{ padding: '12px 14px' }}>
                      <span style={{ color: '#e11d48', fontWeight: 700 }}>
                        {p.current_stock} units
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px', color: '#64748b' }}>{p.reorder_level} units</td>
                    <td style={{ padding: '12px 14px', color: '#0f172a' }}>₹{p.cost_price.toFixed(2)}</td>
                    <td style={{ padding: '12px 14px', textAlign: 'right' }}>
                      <Link to="/purchase-orders" className="btn btn-secondary btn-sm" style={{ fontSize: '11px', padding: '4px 10px' }}>
                        📝 Order Stock
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Section 2: Overdue Customer Khata Accounts (Manual Collection Alert) */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <div>
            <div className="card-title">👥 Unpaid Customer Khata Ledgers (Manual Collection)</div>
            <p style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
              Customers with outstanding credit balances awaiting manual cash/UPI collection.
            </p>
          </div>
          <Link to="/customers" className="btn btn-outline btn-sm">
            Open Khata Book →
          </Link>
        </div>

        {unpaidInvoices.length === 0 ? (
          <div className="empty-state" style={{ padding: '28px 20px', textAlign: 'center' }}>
            <p style={{ color: '#64748b', fontSize: '13px' }}>All customer credit invoices are currently settled.</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#f8fafc', textAlign: 'left', borderBottom: '1px solid #e2e8f0', fontSize: '12px', color: '#64748b' }}>
                  <th style={{ padding: '10px 14px' }}>Invoice #</th>
                  <th style={{ padding: '10px 14px' }}>Customer</th>
                  <th style={{ padding: '10px 14px' }}>Invoice Amount</th>
                  <th style={{ padding: '10px 14px' }}>Due Date</th>
                  <th style={{ padding: '10px 14px' }}>Status</th>
                  <th style={{ padding: '10px 14px', textAlign: 'right' }}>Manual Action</th>
                </tr>
              </thead>
              <tbody>
                {unpaidInvoices.map((inv) => (
                  <tr key={inv.id} style={{ borderBottom: '1px solid #f1f5f9', fontSize: '13px' }}>
                    <td style={{ padding: '12px 14px', fontWeight: 600, color: '#64748b' }}>#{inv.id}</td>
                    <td style={{ padding: '12px 14px', fontWeight: 600, color: '#0f172a' }}>
                      {customerMap.get(inv.customer_id) || inv.customer_id.slice(0, 8)}
                    </td>
                    <td style={{ padding: '12px 14px', color: '#e11d48', fontWeight: 700 }}>
                      ₹{inv.invoice_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td style={{ padding: '12px 14px', color: '#64748b' }}>{inv.due_date || 'N/A'}</td>
                    <td style={{ padding: '12px 14px' }}>
                      <span className="badge badge-medium" style={{ textTransform: 'uppercase', fontSize: '10px' }}>
                        {inv.status}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px', textAlign: 'right' }}>
                      <Link to="/customers" className="btn btn-secondary btn-sm" style={{ fontSize: '11px', padding: '4px 10px' }}>
                        View Ledger
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Section 3: Manual Operations Shortcuts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
        <Link to="/products" className="card" style={{ textDecoration: 'none', transition: 'transform 0.2s' }}>
          <div style={{ fontSize: '1.5rem', marginBottom: 8 }}>📦</div>
          <div className="card-title">Inventory & Catalog</div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Update product selling prices, purchase costs, and adjust shelf stock counts.
          </p>
        </Link>

        <Link to="/sales" className="card" style={{ textDecoration: 'none', transition: 'transform 0.2s' }}>
          <div style={{ fontSize: '1.5rem', marginBottom: 8 }}>🛒</div>
          <div className="card-title">Record POS Customer Sale</div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Ring up customer purchases with cash, UPI, or udhaar with instant receipt generation.
          </p>
        </Link>

        <Link to="/purchase-orders" className="card" style={{ textDecoration: 'none', transition: 'transform 0.2s' }}>
          <div style={{ fontSize: '1.5rem', marginBottom: 8 }}>📝</div>
          <div className="card-title">Supplier Purchase Orders</div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Draft and send manual restocking orders directly to FMCG distributors.
          </p>
        </Link>

        <Link to="/customers" className="card" style={{ textDecoration: 'none', transition: 'transform 0.2s' }}>
          <div style={{ fontSize: '1.5rem', marginBottom: 8 }}>👥</div>
          <div className="card-title">Customer Khata Ledger</div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Record customer udhaar credit entries and mark manual payments as received.
          </p>
        </Link>
      </div>
    </div>
  );
};
