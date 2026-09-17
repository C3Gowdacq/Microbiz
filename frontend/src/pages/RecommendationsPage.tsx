import React, { useEffect, useState } from 'react';
import {
  getRecommendations,
  approveRecommendation,
  modifyRecommendation,
  rejectRecommendation,
  getAnalytics,
  RecommendationRecord,
  AnalyticsSummary,
} from '../api';

type TabStatus = 'ALL' | 'pending' | 'approved' | 'modified' | 'rejected';

export const RecommendationsPage: React.FC = () => {
  const [recommendations, setRecommendations] = useState<RecommendationRecord[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [currentTab, setCurrentTab] = useState<TabStatus>('ALL');
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
      const [recs, stats] = await Promise.all([
        getRecommendations(currentTab === 'ALL' ? undefined : currentTab),
        getAnalytics(),
      ]);
      setRecommendations(recs);
      setAnalytics(stats);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load recommendations inbox');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [currentTab]);

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

      {/* Recommendations Feed */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 48 }}>
          <span className="spinner"></span> Loading recommendations...
        </div>
      ) : recommendations.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🎉</div>
          <h3>No recommendations in this tab!</h3>
          <p>Targeted agent scans or full business health checks will queue actions here.</p>
        </div>
      ) : (
        <div>
          {recommendations.map((rec) => {
            const isPending = rec.status === 'pending';
            const isModifying = modifyingId === rec.id;

            return (
              <div
                key={rec.id}
                className={`rec-card ${
                  rec.priority === 'high'
                    ? 'high-priority'
                    : rec.priority === 'medium'
                    ? 'medium-priority'
                    : 'low-priority'
                }`}
              >
                {/* Card Meta Header */}
                <div className="rec-meta">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span
                      className={`badge ${
                        rec.priority === 'high'
                          ? 'badge-high'
                          : rec.priority === 'medium'
                          ? 'badge-medium'
                          : 'badge-low'
                      }`}
                    >
                      {rec.priority} Priority
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

                    <span style={{ fontFamily: 'JetBrains Mono', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                      Ref #{rec.id}
                    </span>
                  </div>

                  <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    {new Date(rec.created_at).toLocaleString()}
                  </span>
                </div>

                {/* Primary Action Title */}
                <div className="rec-action-title" style={{ marginBottom: 8 }}>
                  ⚡ {rec.primary_action.replace(/_/g, ' ')}
                </div>

                {/* Business Reason */}
                <p className="rec-reason-text">{rec.reason}</p>

                {/* LLM Explanation Section */}
                {(rec.llm_summary || rec.llm_reasoning) && (
                  <div className="rec-llm-section">
                    <div className="rec-llm-title">🤖 LLM Strategic Analysis & Reasoning</div>
                    {rec.llm_summary && (
                      <p className="rec-llm-body" style={{ fontWeight: 600, marginBottom: 6 }}>
                        {rec.llm_summary}
                      </p>
                    )}
                    {rec.llm_reasoning && <p className="rec-llm-body">{rec.llm_reasoning}</p>}

                    {rec.suggested_customer_message && (
                      <div className="rec-customer-msg">
                        <strong>Draft Communication:</strong> "{rec.suggested_customer_message}"
                      </div>
                    )}
                  </div>
                )}

                {/* Modified message display if already modified */}
                {rec.status === 'modified' && rec.modified_message && (
                  <div style={{ background: 'rgba(59, 130, 246, 0.15)', border: '1px solid #3b82f6', borderRadius: 8, padding: 12, marginBottom: 16 }}>
                    <strong style={{ color: '#93c5fd', fontSize: '0.85rem' }}>Shopkeeper Modified Draft:</strong>
                    <div style={{ color: '#eff6ff', marginTop: 4 }}>"{rec.modified_message}"</div>
                  </div>
                )}

                {/* Secondary Actions List */}
                {rec.secondary_recommendations && rec.secondary_recommendations.length > 0 && (
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 6, fontWeight: 700 }}>
                      Secondary Recommended Actions:
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {rec.secondary_recommendations.map((sec, idx) => (
                        <div
                          key={idx}
                          style={{
                            background: 'var(--bg-main)',
                            border: '1px solid var(--border-color)',
                            padding: '8px 12px',
                            borderRadius: 6,
                            fontSize: '0.85rem',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                          }}
                        >
                          <span style={{ textTransform: 'capitalize', color: '#94a3b8' }}>
                            • {sec.action.replace(/_/g, ' ')}: {sec.reason}
                          </span>
                          <span className="badge badge-medium" style={{ fontSize: '0.7rem' }}>
                            {sec.priority}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Interactive HITL Controls for Pending items */}
                {isPending && (
                  <div>
                    {!isModifying ? (
                      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 16 }}>
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
                      <div style={{ marginTop: 16, background: 'var(--bg-main)', padding: 16, borderRadius: 8, border: '1px solid var(--border-color)' }}>
                        <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#93c5fd', marginBottom: 8 }}>
                          Edit Action Note / Customer Communication Draft:
                        </label>
                        <textarea
                          className="form-control"
                          rows={3}
                          value={modifiedText}
                          onChange={(e) => setModifiedText(e.target.value)}
                          style={{ marginBottom: 12 }}
                        />
                        <div style={{ display: 'flex', gap: 10 }}>
                          <button
                            className="btn btn-primary btn-sm"
                            onClick={() => handleConfirmModify(rec.id)}
                            disabled={actionLoading === rec.id}
                          >
                            {actionLoading === rec.id ? <span className="spinner"></span> : 'Save & Approve Modified'}
                          </button>
                          <button className="btn btn-secondary btn-sm" onClick={() => setModifyingId(null)}>
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
