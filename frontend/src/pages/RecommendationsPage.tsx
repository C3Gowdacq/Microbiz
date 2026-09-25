import React, { useEffect, useState } from 'react';
import {
  getRecommendations,
  approveRecommendation,
  modifyRecommendation,
  rejectRecommendation,
  getAnalytics,
  getProducts,
  getCustomers,
  RecommendationRecord,
  AnalyticsSummary,
} from '../api';

type TabStatus = 'ALL' | 'pending' | 'approved' | 'modified' | 'rejected';

export const RecommendationsPage: React.FC = () => {
  const [recommendations, setRecommendations] = useState<RecommendationRecord[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [nameMap, setNameMap] = useState<Record<string, string>>({});
  const [currentTab, setCurrentTab] = useState<TabStatus>('ALL');
  const [priorityFilter, setPriorityFilter] = useState<'ALL' | 'high' | 'medium' | 'low'>('ALL');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Modify message modal/drawer per card
  const [modifyingId, setModifyingId] = useState<number | null>(null);
  const [modifiedText, setModifiedText] = useState<string>('');
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [recs, stats, prods, custs] = await Promise.all([
        getRecommendations(currentTab === 'ALL' ? undefined : currentTab),
        getAnalytics(),
        getProducts().catch(() => []),
        getCustomers().catch(() => []),
      ]);
      const map: Record<string, string> = {};
      if (Array.isArray(prods)) {
        prods.forEach((p: any) => { map[p.id] = p.name; });
      }
      if (Array.isArray(custs)) {
        custs.forEach((c: any) => { map[c.id] = c.name; });
      }
      setNameMap(map);
      setRecommendations(recs);
      setAnalytics(stats);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load recommendations inbox');
    } finally {
      setLoading(false);
    }
  };

  const resolveNames = (text: string | null | undefined): string => {
    if (!text) return '';
    let res = text.replace(/EUR/g, '₹');
    Object.entries(nameMap).forEach(([id, name]) => {
      if (id && name) {
        res = res.split(id).join(name);
      }
    });
    return res;
  };

  useEffect(() => {
    loadData();
  }, [currentTab]);

  const filteredRecs = recommendations.filter((r) => {
    if (priorityFilter === 'ALL') return true;
    return r.priority.toLowerCase() === priorityFilter.toLowerCase();
  });

  const handleApprove = async (id: number) => {
    try {
      setActionLoading(id);
      setError(null);
      await approveRecommendation(id);
      await loadData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to approve recommendation');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (id: number) => {
    try {
      setActionLoading(id);
      setError(null);
      await rejectRecommendation(id);
      await loadData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to reject recommendation');
    } finally {
      setActionLoading(null);
    }
  };

  const handleStartModify = (rec: RecommendationRecord) => {
    setModifyingId(rec.id);
    setModifiedText(rec.suggested_customer_message || rec.reason || '');
  };

  const handleConfirmModify = async (id: number) => {
    try {
      setActionLoading(id);
      setError(null);
      await modifyRecommendation(id, modifiedText);
      setModifyingId(null);
      await loadData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to save modification');
    } finally {
      setActionLoading(null);
    }
  };

  const renderStructuredReason = (reason: string) => {
    const invRegex = /Inventory alert\s*\(([^)]+)\):\s*'([^']+)'\s*stock is\s*([\d.]+)\s*\(coverage:\s*([\d.]+)\s*days,\s*ROP:\s*([\d.]+)\)\.\s*Recommended reorder quantity:\s*([\d.]+)\s*units\s*\(estimated cost:\s*([^)]+)\)/i;
    const match = reason.match(invRegex);

    if (match) {
      const [, alertLevel, prodName, stock, coverage, rop, reorderQty, estCost] = match;
      const isCritical = alertLevel.toUpperCase() === 'CRITICAL';

      return (
        <div style={{ marginTop: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '1.3rem' }}>📦</span>
            <span style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f172a' }}>{prodName}</span>
            <span className={`badge ${isCritical ? 'badge-critical' : 'badge-high'}`} style={{ fontSize: '0.75rem' }}>
              {alertLevel.toUpperCase()} DEFICIT
            </span>
          </div>

          <div className="rec-metrics-grid">
            <div className="rec-metric-card" style={{ borderLeft: `4px solid ${isCritical ? '#e11d48' : '#f97316'}` }}>
              <span className="rec-metric-label">On-Hand Stock</span>
              <span className="rec-metric-val" style={{ color: isCritical ? '#e11d48' : '#c2410c' }}>
                {Number(stock).toFixed(1)} units
              </span>
              <span className="rec-metric-sub">Reorder Point: {rop} units</span>
            </div>

            <div className="rec-metric-card">
              <span className="rec-metric-label">Supply Coverage</span>
              <span className="rec-metric-val" style={{ color: Number(coverage) < 2 ? '#e11d48' : '#0f172a' }}>
                {coverage} days
              </span>
              <span className="rec-metric-sub">Until stock depletion</span>
            </div>

            <div className="rec-metric-card" style={{ borderLeft: '4px solid #2563eb' }}>
              <span className="rec-metric-label">Recommended Order</span>
              <span className="rec-metric-val" style={{ color: '#2563eb' }}>
                +{Math.round(Number(reorderQty))} units
              </span>
              <span className="rec-metric-sub">Exact: {Number(reorderQty).toFixed(1)} units</span>
            </div>

            <div className="rec-metric-card" style={{ borderLeft: '4px solid #059669' }}>
              <span className="rec-metric-label">Estimated Procurement Cost</span>
              <span className="rec-metric-val" style={{ color: '#059669' }}>
                {estCost}
              </span>
              <span className="rec-metric-sub">Wholesale trade estimate</span>
            </div>
          </div>

          <div className="rec-reason-box">
            <strong>Operational Intelligence:</strong> Live stock for <strong>{prodName}</strong> has breached safety levels ({Number(stock).toFixed(1)} vs ROP of {rop}), leaving approximately <strong>{coverage} days</strong> of customer demand before stockout. Replenishment recommends placing an order for <strong>{Math.round(Number(reorderQty))} units</strong> ({estCost}).
          </div>
        </div>
      );
    }

    return (
      <div className="rec-reason-box">
        <strong>Action Context:</strong> {reason}
      </div>
    );
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Human-in-the-Loop AI Approvals Inbox</h1>
          <p className="page-subtitle">
            Review, calibrate, approve, or dismiss autonomous actions triggered across all store modules
          </p>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary btn-sm" onClick={loadData} disabled={loading}>
            🔄 Refresh Inbox
          </button>
        </div>
      </div>

      {error && <div className="error-banner">⚠️ {error}</div>}

      {/* Analytics KPI Bar */}
      {analytics && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 14, marginBottom: 24 }}>
          <div className="kpi-card" style={{ padding: '14px 18px' }}>
            <div className="kpi-label">Total Actions</div>
            <div className="kpi-value" style={{ fontSize: '1.6rem', margin: '4px 0' }}>
              {analytics.total_count}
            </div>
          </div>
          <div className="kpi-card" style={{ padding: '14px 18px' }}>
            <div className="kpi-label">Pending Review</div>
            <div className="kpi-value" style={{ fontSize: '1.6rem', margin: '4px 0', color: '#818cf8' }}>
              {analytics.pending_count}
            </div>
          </div>
          <div className="kpi-card" style={{ padding: '14px 18px' }}>
            <div className="kpi-label">Approved</div>
            <div className="kpi-value" style={{ fontSize: '1.6rem', margin: '4px 0', color: '#10b981' }}>
              {analytics.approved_count}
            </div>
          </div>
          <div className="kpi-card" style={{ padding: '14px 18px' }}>
            <div className="kpi-label">Modified</div>
            <div className="kpi-value" style={{ fontSize: '1.6rem', margin: '4px 0', color: '#38bdf8' }}>
              {analytics.modified_count}
            </div>
          </div>
          <div className="kpi-card" style={{ padding: '14px 18px' }}>
            <div className="kpi-label">Dismissed / Rejected</div>
            <div className="kpi-value" style={{ fontSize: '1.6rem', margin: '4px 0', color: '#ef4444' }}>
              {analytics.rejected_count}
            </div>
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="tabs-nav">
        <button
          className={`tab-btn ${currentTab === 'ALL' ? 'active' : ''}`}
          onClick={() => setCurrentTab('ALL')}
        >
          All Records ({analytics?.total_count ?? 0})
        </button>
        <button
          className={`tab-btn ${currentTab === 'pending' ? 'active' : ''}`}
          onClick={() => setCurrentTab('pending')}
        >
          🚨 Pending Review ({analytics?.pending_count ?? 0})
        </button>
        <button
          className={`tab-btn ${currentTab === 'approved' ? 'active' : ''}`}
          onClick={() => setCurrentTab('approved')}
        >
          ✓ Approved ({analytics?.approved_count ?? 0})
        </button>
        <button
          className={`tab-btn ${currentTab === 'modified' ? 'active' : ''}`}
          onClick={() => setCurrentTab('modified')}
        >
          ✏️ Modified ({analytics?.modified_count ?? 0})
        </button>
        <button
          className={`tab-btn ${currentTab === 'rejected' ? 'active' : ''}`}
          onClick={() => setCurrentTab('rejected')}
        >
          ✕ Dismissed ({analytics?.rejected_count ?? 0})
        </button>
      </div>

      {/* Priority Secondary Filter Pills */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20, alignItems: 'center', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)' }}>Priority:</span>
        {(['ALL', 'high', 'medium', 'low'] as const).map((p) => (
          <button
            key={p}
            className={`btn btn-sm ${priorityFilter === p ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setPriorityFilter(p)}
            style={{ textTransform: 'capitalize', padding: '4px 12px', fontSize: '0.8rem' }}
          >
            {p === 'ALL' ? 'All Priorities' : `${p} Priority`}
          </button>
        ))}
        <span style={{ marginLeft: 'auto', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Showing {filteredRecs.length} recommendations
        </span>
      </div>

      {/* Recommendations Feed */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 48 }}>
          <span className="spinner"></span> Loading recommendations...
        </div>
      ) : filteredRecs.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🎉</div>
          <h3>No recommendations in this view!</h3>
          <p>Targeted agent scans or full business health checks will queue actions here.</p>
        </div>
      ) : (
        <div>
          {filteredRecs.map((rec) => {
            const isPending = rec.status === 'pending';
            const isModifying = modifyingId === rec.id;
            const isRestock = rec.primary_action.toLowerCase().includes('replenishment') || rec.primary_action.toLowerCase().includes('stock') || rec.entity_type === 'product';
            const priorityLower = rec.priority.toLowerCase();
            const validSecondary = (rec.secondary_recommendations || []).filter(
              (sec) => sec.reason && sec.reason.trim().length > 0
            );

            return (
              <div
                key={rec.id}
                className={`rec-card ${
                  priorityLower === 'critical'
                    ? 'critical-priority'
                    : priorityLower === 'high'
                    ? 'high-priority'
                    : priorityLower === 'medium'
                    ? 'medium-priority'
                    : 'low-priority'
                }`}
              >
                {/* Card Meta Header */}
                <div className="rec-meta">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                    <span
                      className={`badge ${
                        priorityLower === 'critical'
                          ? 'badge-critical'
                          : priorityLower === 'high'
                          ? 'badge-high'
                          : priorityLower === 'medium'
                          ? 'badge-medium'
                          : 'badge-low'
                      }`}
                    >
                      {rec.priority.toUpperCase()} PRIORITY
                    </span>

                    <span
                      className={`badge ${
                        rec.status === 'approved'
                          ? 'badge-approved'
                          : rec.status === 'rejected'
                          ? 'badge-rejected'
                          : rec.status === 'modified'
                          ? 'badge-modified'
                          : 'badge-pending'
                      }`}
                    >
                      {rec.status.toUpperCase()}
                    </span>

                    {rec.module && (
                      <span className="badge" style={{ background: '#f5f3ff', color: '#6d28d9', border: '1px solid #ddd6fe' }}>
                        🏷️ {rec.module.toUpperCase()}
                      </span>
                    )}

                    <span style={{ fontFamily: 'JetBrains Mono', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                      Ref #{rec.id}
                    </span>
                  </div>

                  <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: 500 }}>
                    {new Date(rec.created_at).toLocaleString()}
                  </span>
                </div>

                {/* Primary Action Title */}
                <div className="rec-action-title">
                  <span>⚡</span>
                  <span style={{ textTransform: 'capitalize' }}>
                    {rec.primary_action.replace(/_/g, ' ')}
                  </span>
                </div>

                {/* Restock PO linkage notice */}
                {isRestock && (
                  <div className="rec-po-banner">
                    <span style={{ fontSize: '1.3rem' }}>📦</span>
                    <div>
                      <strong style={{ display: 'block', color: '#065f46', marginBottom: '2px' }}>
                        Autonomous Purchase Order Pipeline Ready
                      </strong>
                      <span style={{ color: '#047857' }}>
                        Approving this recommendation creates and authorizes an immediate Purchase Order for supplier delivery.
                      </span>
                    </div>
                  </div>
                )}

                {/* Structured Business Reason Display */}
                {renderStructuredReason(resolveNames(rec.reason))}

                {/* LLM Explanation Section */}
                {(rec.llm_summary || rec.llm_reasoning) && (
                  <div className="rec-llm-section">
                    <div className="rec-llm-title">🤖 LLM Strategic Analysis & Reasoning</div>
                    {rec.llm_summary && (
                      <p className="rec-llm-body" style={{ fontWeight: 600, marginBottom: 6 }}>
                        {resolveNames(rec.llm_summary)}
                      </p>
                    )}
                    {rec.llm_reasoning && <p className="rec-llm-body">{resolveNames(rec.llm_reasoning)}</p>}

                    {rec.suggested_customer_message && (
                      <div className="rec-customer-msg">
                        <strong>Draft Communication:</strong> "{resolveNames(rec.suggested_customer_message)}"
                      </div>
                    )}
                  </div>
                )}

                {/* Modified message display if already modified */}
                {rec.status === 'modified' && rec.modified_message && (
                  <div style={{ background: '#eff6ff', border: '1px solid #93c5fd', borderRadius: 8, padding: 12, marginBottom: 16 }}>
                    <strong style={{ color: '#1e40af', fontSize: '0.85rem' }}>Shopkeeper Modified Draft:</strong>
                    <div style={{ color: '#1e293b', marginTop: 4 }}>"{resolveNames(rec.modified_message)}"</div>
                  </div>
                )}

                {/* Secondary Actions List (Only when there are actual actions with non-empty reasons) */}
                {validSecondary.length > 0 && (
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 6, fontWeight: 700 }}>
                      Secondary Recommended Actions:
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {validSecondary.map((sec, idx) => (
                        <div
                          key={idx}
                          style={{
                            background: '#f8fafc',
                            border: '1px solid #e2e8f0',
                            padding: '8px 12px',
                            borderRadius: 6,
                            fontSize: '0.85rem',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                          }}
                        >
                          <span style={{ textTransform: 'capitalize', color: '#475569' }}>
                            • {sec.action.replace(/_/g, ' ')}: {resolveNames(sec.reason)}
                          </span>
                          {sec.priority && (
                            <span className="badge badge-medium" style={{ fontSize: '0.7rem' }}>
                              {sec.priority}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Interactive HITL Controls for Pending items */}
                {isPending && (
                  <div>
                    {!isModifying ? (
                      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 18 }}>
                        <button
                          className="btn btn-success"
                          onClick={() => handleApprove(rec.id)}
                          disabled={actionLoading === rec.id}
                        >
                          {actionLoading === rec.id ? <span className="spinner"></span> : '✓ Approve Action'}
                        </button>

                        <button
                          className="btn btn-secondary"
                          onClick={() => handleStartModify(rec)}
                          disabled={actionLoading === rec.id}
                        >
                          ✏️ Modify Draft
                        </button>

                        <button
                          className="btn btn-danger"
                          onClick={() => handleReject(rec.id)}
                          disabled={actionLoading === rec.id}
                        >
                          ✕ Dismiss
                        </button>
                      </div>
                    ) : (
                      <div style={{ marginTop: 16, background: '#f8fafc', padding: 16, borderRadius: 8, border: '1px solid #e2e8f0' }}>
                        <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#1e40af', marginBottom: 8 }}>
                          Edit Action Note / Customer Communication Draft:
                        </label>
                        <textarea
                          className="form-control"
                          rows={3}
                          value={modifiedText}
                          onChange={(e) => setModifiedText(e.target.value)}
                          style={{ marginBottom: 12 }}
                        />
                        <div style={{ display: 'flex', gap: 8 }}>
                          <button
                            className="btn btn-primary btn-sm"
                            onClick={() => handleConfirmModify(rec.id)}
                            disabled={actionLoading === rec.id}
                          >
                            {actionLoading === rec.id ? <span className="spinner"></span> : 'Save Modifications'}
                          </button>
                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => setModifyingId(null)}
                            disabled={actionLoading === rec.id}
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
