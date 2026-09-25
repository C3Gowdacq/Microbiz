import React, { useEffect, useState } from 'react';
import {
  getSettings,
  updateSettings,
  BusinessSettings,
  BusinessSettingsUpdate,
} from '../api';

export const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<BusinessSettings | null>(null);
  const [formData, setFormData] = useState<BusinessSettingsUpdate>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getSettings();
      setSettings(data);
      setFormData({
        min_cash_reserve: data.min_cash_reserve,
        currency: data.currency,
        safety_stock_days: data.safety_stock_days,
        review_period_days: data.review_period_days,
        khata_overdue_days: data.khata_overdue_days,
        expense_anomaly_threshold_pct: data.expense_anomaly_threshold_pct,
        high_risk_multiplier: data.high_risk_multiplier,
        medium_risk_multiplier: data.medium_risk_multiplier,
        autonomous_mode: data.autonomous_mode,
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleChange = (field: keyof BusinessSettingsUpdate, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError(null);
      const updated = await updateSettings(formData);
      setSettings(updated);
      setSuccessMsg('Business operational settings updated successfully!');
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Store & Automation Settings</h1>
        <p className="page-subtitle">Configure financial thresholds, replenishment parameters, and agent policies</p>
      </div>

      {successMsg && (
        <div className="alert alert-success" style={{ margin: '16px 0', padding: '14px 18px', background: '#e6f4ea', color: '#137333', borderRadius: '8px', border: '1px solid #ceead6' }}>
          ✓ {successMsg}
        </div>
      )}

      {error && (
        <div className="alert alert-danger" style={{ margin: '16px 0', padding: '14px 18px', background: '#fce8e6', color: '#c5221f', borderRadius: '8px', border: '1px solid #fad2cf' }}>
          ⚠️ {error}
        </div>
      )}

      {loading ? (
        <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>Loading configuration...</div>
      ) : (
        <form onSubmit={handleSave}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '24px', margin: '20px 0' }}>
            {/* Financial Solvency Guard */}
            <div className="card" style={{ padding: '24px' }}>
              <h3 style={{ marginTop: 0, fontSize: '17px', borderBottom: '1px solid #eee', paddingBottom: '10px' }}>
                💰 Financial & Liquidity Policies
              </h3>

              <div style={{ margin: '16px 0' }}>
                <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600, fontSize: '14px' }}>
                  Minimum Cash Reserve (₹)
                </label>
                <input
                  type="number"
                  className="form-control"
                  min="0"
                  step="500"
                  value={formData.min_cash_reserve ?? 25000}
                  onChange={(e) => handleChange('min_cash_reserve', Number(e.target.value))}
                  required
                />
                <small style={{ color: '#666', display: 'block', marginTop: '4px' }}>
                  Cash buffer to maintain before triggering liquidity risk alerts.
                </small>
              </div>

              <div style={{ margin: '16px 0' }}>
                <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600, fontSize: '14px' }}>
                  Store Base Currency
                </label>
                <input
                  type="text"
                  className="form-control"
                  value={formData.currency ?? 'INR'}
                  onChange={(e) => handleChange('currency', e.target.value)}
                  required
                />
              </div>
            </div>

            {/* Inventory & Procurement Policies */}
            <div className="card" style={{ padding: '24px' }}>
              <h3 style={{ marginTop: 0, fontSize: '17px', borderBottom: '1px solid #eee', paddingBottom: '10px' }}>
                📦 Inventory & Replenishment Parameters
              </h3>

              <div style={{ margin: '16px 0' }}>
                <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600, fontSize: '14px' }}>
                  Safety Stock Buffer (Days of Demand)
                </label>
                <input
                  type="number"
                  className="form-control"
                  min="1"
                  max="30"
                  value={formData.safety_stock_days ?? 3}
                  onChange={(e) => handleChange('safety_stock_days', Number(e.target.value))}
                  required
                />
                <small style={{ color: '#666', display: 'block', marginTop: '4px' }}>
                  Extra demand buffer maintained to absorb demand surges and supplier delays.
                </small>
              </div>

              <div style={{ margin: '16px 0' }}>
                <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600, fontSize: '14px' }}>
                  Replenishment Review Period (Days)
                </label>
                <input
                  type="number"
                  className="form-control"
                  min="1"
                  max="60"
                  value={formData.review_period_days ?? 7}
                  onChange={(e) => handleChange('review_period_days', Number(e.target.value))}
                  required
                />
                <small style={{ color: '#666', display: 'block', marginTop: '4px' }}>
                  Cadence for calculating optimal target stock in purchase order drafts.
                </small>
              </div>
            </div>

            {/* Khata & Credit Policies */}
            <div className="card" style={{ padding: '24px' }}>
              <h3 style={{ marginTop: 0, fontSize: '17px', borderBottom: '1px solid #eee', paddingBottom: '10px' }}>
                👥 Khata (Credit) Governance
              </h3>

              <div style={{ margin: '16px 0' }}>
                <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600, fontSize: '14px' }}>
                  Khata Overdue Threshold (Days)
                </label>
                <input
                  type="number"
                  className="form-control"
                  min="1"
                  max="120"
                  value={formData.khata_overdue_days ?? 30}
                  onChange={(e) => handleChange('khata_overdue_days', Number(e.target.value))}
                  required
                />
                <small style={{ color: '#666', display: 'block', marginTop: '4px' }}>
                  Invoices past this threshold are flagged for urgent follow-up.
                </small>
              </div>

              <div style={{ margin: '16px 0' }}>
                <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600, fontSize: '14px' }}>
                  Expense Anomaly Spike Threshold (%)
                </label>
                <input
                  type="number"
                  className="form-control"
                  min="5"
                  max="200"
                  value={formData.expense_anomaly_threshold_pct ?? 30}
                  onChange={(e) => handleChange('expense_anomaly_threshold_pct', Number(e.target.value))}
                  required
                />
                <small style={{ color: '#666', display: 'block', marginTop: '4px' }}>
                  Percentage increase over prior 30-day baseline that triggers expense audit.
                </small>
              </div>
            </div>

            {/* Autonomous Execution Toggle */}
            <div className="card" style={{ padding: '24px' }}>
              <h3 style={{ marginTop: 0, fontSize: '17px', borderBottom: '1px solid #eee', paddingBottom: '10px' }}>
                ⚡ Autonomous Engine Policy
              </h3>

              <div style={{ margin: '20px 0', display: 'flex', alignItems: 'center', gap: '12px' }}>
                <input
                  type="checkbox"
                  id="autonomous_mode"
                  style={{ width: '20px', height: '20px', cursor: 'pointer' }}
                  checked={formData.autonomous_mode ?? false}
                  onChange={(e) => handleChange('autonomous_mode', e.target.checked)}
                />
                <label htmlFor="autonomous_mode" style={{ fontWeight: 700, fontSize: '15px', cursor: 'pointer' }}>
                  Enable Autonomous Event Processing
                </label>
              </div>

              <p style={{ fontSize: '13px', color: '#666', lineHeight: 1.5 }}>
                When enabled, every sale atomically calculates inventory risk and triggers the replenishment agent
                if stockout coverage drops below supplier lead time. Purchase order recommendations are queued for
                human approval.
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '20px' }}>
            <button
              type="button"
              className="btn btn-outline"
              onClick={fetchSettings}
            >
              Reset to Current
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              style={{ minWidth: '160px' }}
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save Configuration'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};
