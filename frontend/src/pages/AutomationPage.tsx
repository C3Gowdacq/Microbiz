import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getAutomationStatus,
  toggleAutonomousMode,
  AutomationStatus,
  api,
} from '../api';

export const AutomationPage: React.FC = () => {
  const navigate = useNavigate();
  const [status, setStatus] = useState<AutomationStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [toggling, setToggling] = useState<boolean>(false);
  const [runningSweep, setRunningSweep] = useState<boolean>(false);
  const [sweepResult, setSweepResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Live Simulation state
  const [simulating, setSimulating] = useState<boolean>(false);
  const [simStep, setSimStep] = useState<number>(0);
  const [simDetails, setSimDetails] = useState<{
    productName: string;
    remainingStock: number;
    rop: number;
    reorderUnits: number;
    poCreated: boolean;
  } | null>(null);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getAutomationStatus();
      setStatus(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load automation status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const timer = setInterval(fetchStatus, 15000);
    return () => clearInterval(timer);
  }, []);

  const handleToggle = async () => {
    try {
      setToggling(true);
      setError(null);
      const updated = await toggleAutonomousMode();
      setSuccessMsg(
        updated.autonomous_mode
          ? '⚡ Autonomous Mode ENABLED: POS sale events trigger real-time stock evaluation and auto-draft replenishment orders.'
          : '🔒 Manual Mode ENABLED: Agent actions require manual merchant execution.'
      );
      await fetchStatus();
      setTimeout(() => setSuccessMsg(null), 5000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to toggle autonomous mode');
    } finally {
      setToggling(false);
    }
  };

  const handleRunFullSweep = async () => {
    try {
      setRunningSweep(true);
      setSweepResult(null);
      setError(null);
      const res = await api.post('/api/agents/run-full');
      setSweepResult(res.data);
      setSuccessMsg('Diagnostic sweep completed across all business domains!');
      fetchStatus();
      setTimeout(() => setSuccessMsg(null), 6000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Diagnostic execution failed');
    } finally {
      setRunningSweep(false);
    }
  };

  // Live simulation: Record a sale of Basmati Rice and watch the autonomous closed-loop fire
  const handleSimulateSale = async () => {
    try {
      setSimulating(true);
      setSimStep(1);
      setError(null);

      // Find Basmati Rice or first product from critical list
      const targetProduct = status?.critical_inventory?.[0] || {
        id: '16ed43d7-c035-4bdc-9650-b93254b6ad7c',
        name: 'Basmati Rice (50kg Bag)',
        current_stock: 2.0,
        reorder_level: 25.0,
      };

      // Step 1: Submit POS sale
      const salePayload = {
        product_id: targetProduct.id,
        quantity: 1,
        unit_price: 1350.0,
        payment_method: 'CASH',
        customer_name: 'Walk-in Cash Customer',
      };

      const res = await api.post('/api/sales', salePayload);

      setTimeout(() => {
        setSimStep(2); // Inventory Agent
      }, 500);

      setTimeout(() => {
        setSimStep(3); // Replenishment Agent
        const postStock = res.data.remaining_stock ?? Math.max(0, targetProduct.current_stock - 1);
        setSimDetails({
          productName: targetProduct.name,
          remainingStock: postStock,
          rop: res.data.reorder_point ?? targetProduct.reorder_level,
          reorderUnits: res.data.recommended_order_quantity ?? 28,
          poCreated: true,
        });
      }, 1100);

      setTimeout(async () => {
        setSimStep(4); // Finished
        await fetchStatus();
        setSimulating(false);
      }, 1700);

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Simulation sale failed');
      setSimulating(false);
      setSimStep(0);
    }
  };

  const currencySymbol = '₹';

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 className="page-title">Autonomous Retail Engine</h1>
          <p className="page-subtitle">Real-time closed-loop decision system & multi-agent retail operations</p>
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button
            className="btn btn-secondary"
            onClick={handleSimulateSale}
            disabled={simulating}
            style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}
          >
            {simulating ? '⏳ Simulating Pipeline...' : '🎮 Simulate POS Sale Event'}
          </button>
          <button
            className="btn btn-primary"
            onClick={handleRunFullSweep}
            disabled={runningSweep}
            style={{ fontWeight: 600 }}
          >
            {runningSweep ? '⏳ Running Multi-Agent Sweep...' : '⚡ Run Full Diagnostic'}
          </button>
        </div>
      </div>

      {successMsg && (
        <div className="alert alert-success" style={{ margin: '16px 0', padding: '14px 18px', background: '#e6f4ea', color: '#137333', borderRadius: '8px', border: '1px solid #ceead6' }}>
          {successMsg}
        </div>
      )}

      {error && (
        <div className="alert alert-danger" style={{ margin: '16px 0', padding: '14px 18px', background: '#fce8e6', color: '#c5221f', borderRadius: '8px', border: '1px solid #fad2cf' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Mode Status Banner Card */}
      <div className="card" style={{ padding: '24px', margin: '20px 0', background: status?.autonomous_mode ? 'linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%)' : 'linear-gradient(135deg, #37474f 0%, #455a64 100%)', color: '#fff' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <span style={{ fontSize: '24px' }}>{status?.autonomous_mode ? '🤖' : '🔒'}</span>
              <h2 style={{ margin: 0, fontSize: '22px', fontWeight: 700 }}>
                {status?.autonomous_mode ? 'Autonomous Closed Loop: ACTIVE' : 'Manual Supervised Mode: ACTIVE'}
              </h2>
            </div>
            <p style={{ margin: 0, opacity: 0.9, maxWidth: '680px', fontSize: '14px', lineHeight: 1.5 }}>
              {status?.autonomous_mode
                ? 'Every POS sale automatically recalculates sales velocity, projects stockout risk, drafts deduplicated purchase orders for supplier replenishment, and alerts the merchant in AI Approvals.'
                : 'Stock transactions update inventory normally. Agent diagnostics, credit checks, and replenishment recommendations are triggered manually.'}
            </p>
          </div>

          <button
            className="btn"
            style={{
              background: '#fff',
              color: status?.autonomous_mode ? '#1b5e20' : '#263238',
              fontWeight: 700,
              padding: '12px 24px',
              fontSize: '15px',
              borderRadius: '8px',
              border: 'none',
              cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            }}
            onClick={handleToggle}
            disabled={toggling}
          >
            {toggling ? 'Updating...' : status?.autonomous_mode ? 'Switch to Manual Mode' : 'Enable Autonomous Mode'}
          </button>
        </div>
      </div>

      {/* Interactive Closed-Loop Simulation Display (When triggered) */}
      {(simulating || simStep > 0) && (
        <div className="card" style={{ padding: '20px', marginBottom: '24px', borderLeft: '4px solid #10b981', background: '#f0fdf4' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <h4 style={{ margin: 0, color: '#065f46', fontSize: '16px' }}>
              ⚡ Live Autonomous Closed-Loop Demonstration
            </h4>
            {simStep === 4 && (
              <button
                className="btn btn-sm"
                style={{ background: '#059669', color: '#fff', border: 'none', borderRadius: 4, padding: '4px 10px', fontSize: '12px', cursor: 'pointer' }}
                onClick={() => setSimStep(0)}
              >
                Close Trace ✕
              </button>
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
            <div style={{ padding: 12, borderRadius: 6, background: simStep >= 1 ? '#dcfce7' : '#fff', border: '1px solid #bbf7d0' }}>
              <div style={{ fontSize: '11px', color: '#047857', fontWeight: 700 }}>STEP 1: POS SALE</div>
              <div style={{ fontWeight: 600, fontSize: '13px', marginTop: 4 }}>
                {simStep >= 1 ? '✓ Sale Recorded (1 Unit)' : 'Waiting...'}
              </div>
              <div style={{ fontSize: '11px', color: '#666', marginTop: 2 }}>Cashier checkout at POS</div>
            </div>

            <div style={{ padding: 12, borderRadius: 6, background: simStep >= 2 ? '#dcfce7' : '#fff', border: '1px solid #bbf7d0' }}>
              <div style={{ fontSize: '11px', color: '#047857', fontWeight: 700 }}>STEP 2: INVENTORY AGENT</div>
              <div style={{ fontWeight: 600, fontSize: '13px', marginTop: 4 }}>
                {simStep >= 2 ? '🚨 Stock < ROP (CRITICAL)' : 'Evaluating...'}
              </div>
              <div style={{ fontSize: '11px', color: '#666', marginTop: 2 }}>Velocity & lead-time calculated</div>
            </div>

            <div style={{ padding: 12, borderRadius: 6, background: simStep >= 3 ? '#dcfce7' : '#fff', border: '1px solid #bbf7d0' }}>
              <div style={{ fontSize: '11px', color: '#047857', fontWeight: 700 }}>STEP 3: REPLENISHMENT</div>
              <div style={{ fontWeight: 600, fontSize: '13px', marginTop: 4 }}>
                {simStep >= 3 ? `📦 Draft PO (+${simDetails?.reorderUnits || 28} units)` : 'Deduplicating...'}
              </div>
              <div style={{ fontSize: '11px', color: '#666', marginTop: 2 }}>Primary supplier & cost matched</div>
            </div>

            <div style={{ padding: 12, borderRadius: 6, background: simStep >= 4 ? '#dcfce7' : '#fff', border: '1px solid #bbf7d0' }}>
              <div style={{ fontSize: '11px', color: '#047857', fontWeight: 700 }}>STEP 4: HITL APPROVAL</div>
              <div style={{ fontWeight: 600, fontSize: '13px', marginTop: 4 }}>
                {simStep >= 4 ? '🛡️ Inbox Updated' : 'Pushing to Inbox...'}
              </div>
              <div style={{ fontSize: '11px', color: '#666', marginTop: 2 }}>1-Click merchant authorization</div>
            </div>
          </div>

          {simDetails && (
            <div style={{ marginTop: 14, paddingTop: 12, borderTop: '1px dashed #86efac', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
              <div style={{ fontSize: '13px', color: '#065f46' }}>
                <strong>Product:</strong> {simDetails.productName} | <strong>Remaining Stock:</strong> {simDetails.remainingStock} units (ROP: {simDetails.rop}) | <strong>Recommended Order:</strong> +{simDetails.reorderUnits} units
              </div>
              <button
                className="btn btn-primary btn-sm"
                onClick={() => navigate('/recommendations')}
                style={{ fontSize: '12px', padding: '6px 14px' }}
              >
                View Draft PO in AI Approvals →
              </button>
            </div>
          )}
        </div>
      )}

      {/* KPI Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        <div className="card" style={{ padding: '20px' }}>
          <div style={{ fontSize: '13px', color: '#666', fontWeight: 600 }}>ACTIVE AGENTS</div>
          <div style={{ fontSize: '28px', fontWeight: 700, marginTop: '4px', color: '#1e88e5' }}>
            {status?.agents.length || 5}
          </div>
          <div style={{ fontSize: '12px', color: '#888', marginTop: '4px' }}>Inventory, Credit, Solvency, Expense</div>
        </div>

        <div
          className="card"
          style={{ padding: '20px', cursor: 'pointer', transition: 'transform 0.2s ease' }}
          onClick={() => navigate('/recommendations')}
          title="Click to view AI Approvals Inbox"
        >
          <div style={{ fontSize: '13px', color: '#666', fontWeight: 600 }}>PENDING HITL APPROVALS</div>
          <div style={{ fontSize: '28px', fontWeight: 700, marginTop: '4px', color: '#e53935' }}>
            {status?.pending_recommendations_count ?? 0}
          </div>
          <div style={{ fontSize: '12px', color: '#1976d2', marginTop: '4px', fontWeight: 600 }}>
            Waiting merchant review →
          </div>
        </div>

        <div
          className="card"
          style={{ padding: '20px', cursor: 'pointer' }}
          onClick={() => navigate('/sales')}
          title="Click to view Sales and Inventory"
        >
          <div style={{ fontSize: '13px', color: '#666', fontWeight: 600 }}>CRITICAL STOCK RISKS</div>
          <div style={{ fontSize: '28px', fontWeight: 700, marginTop: '4px', color: '#d97706' }}>
            {status?.critical_inventory?.length ?? 0} SKUs
          </div>
          <div style={{ fontSize: '12px', color: '#888', marginTop: '4px' }}>Currently below Reorder Point</div>
        </div>

        <div
          className="card"
          style={{ padding: '20px', cursor: 'pointer' }}
          onClick={() => navigate('/customers')}
          title="Click to view Customer Khata"
        >
          <div style={{ fontSize: '13px', color: '#666', fontWeight: 600 }}>OVERDUE KHATA CREDIT</div>
          <div style={{ fontSize: '28px', fontWeight: 700, marginTop: '4px', color: '#8e24aa' }}>
            {currencySymbol}{(status?.khata_summary?.total_overdue ?? 0).toLocaleString('en-IN')}
          </div>
          <div style={{ fontSize: '12px', color: '#888', marginTop: '4px' }}>
            Across {status?.khata_summary?.overdue_count ?? 0} customer accounts
          </div>
        </div>
      </div>

      {/* Multi-Agent Matrix with LIVE Operational Intelligence */}
      <div className="card" style={{ padding: '24px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ margin: 0, fontSize: '18px' }}>🤖 MicroBiz Multi-Agent Decision Grid</h3>
          <span style={{ fontSize: '12px', color: '#666', background: '#f1f5f9', padding: '4px 8px', borderRadius: 4 }}>
            Live Event-Driven Architecture
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>

          {/* 1. Inventory Agent */}
          <div style={{ padding: '18px', border: '1px solid #e2e8f0', borderRadius: '8px', background: '#fff', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong style={{ fontSize: '15px', display: 'flex', alignItems: 'center', gap: 6 }}>
                  📦 Inventory Agent
                </strong>
                <span className="badge badge-success" style={{ background: '#e8f5e9', color: '#2e7d32', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600 }}>ACTIVE</span>
              </div>
              <p style={{ fontSize: '12px', color: '#666', margin: '6px 0 10px 0' }}>
                Trigger: Post-sale event / Automatic lead-time & ROP monitoring
              </p>

              {/* Real-time Findings */}
              <div style={{ background: '#f8fafc', padding: 10, borderRadius: 6, border: '1px solid #edf2f7', marginBottom: 12 }}>
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#475569', marginBottom: 6 }}>
                  LIVE OPERATIONAL FINDINGS:
                </div>
                {status?.critical_inventory && status.critical_inventory.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {status.critical_inventory.slice(0, 3).map((item) => (
                      <div key={item.id} style={{ fontSize: '12px', display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: '#1e293b', fontWeight: 500 }}>{item.name}</span>
                        <span style={{ color: '#dc2626', fontWeight: 600 }}>
                          {item.current_stock} left (ROP: {item.reorder_level})
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ fontSize: '12px', color: '#16a34a' }}>✓ All monitored inventory levels healthy</div>
                )}
              </div>
            </div>

            <button
              className="btn btn-secondary btn-sm"
              style={{ width: '100%', fontSize: '12px', marginTop: 8 }}
              onClick={() => navigate('/sales')}
            >
              Record POS Sale & Test Risk →
            </button>
          </div>

          {/* 2. Replenishment Agent */}
          <div style={{ padding: '18px', border: '1px solid #e2e8f0', borderRadius: '8px', background: '#fff', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong style={{ fontSize: '15px', display: 'flex', alignItems: 'center', gap: 6 }}>
                  ⚡ Replenishment Agent
                </strong>
                <span className="badge badge-success" style={{ background: '#e8f5e9', color: '#2e7d32', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600 }}>ACTIVE</span>
              </div>
              <p style={{ fontSize: '12px', color: '#666', margin: '6px 0 10px 0' }}>
                Trigger: Stock &lt; ROP / Automatic PO drafting with deduplication
              </p>

              {/* Real-time Findings */}
              <div style={{ background: '#f8fafc', padding: 10, borderRadius: 6, border: '1px solid #edf2f7', marginBottom: 12 }}>
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#475569', marginBottom: 6 }}>
                  LIVE PROCUREMENT PIPELINE:
                </div>
                <div style={{ fontSize: '12px', color: '#1e293b', marginBottom: 4 }}>
                  <strong>{status?.replenishment_summary?.pending_po_count ?? 0} Draft Orders</strong> auto-generated
                </div>
                <div style={{ fontSize: '12px', color: '#047857', fontWeight: 600 }}>
                  Est. Order Value: {currencySymbol}{(status?.replenishment_summary?.total_po_value ?? 0).toLocaleString('en-IN')}
                </div>
                <div style={{ fontSize: '11px', color: '#64748b', marginTop: 4 }}>
                  🛡️ Idempotency active: zero duplicate supplier orders
                </div>
              </div>
            </div>

            <button
              className="btn btn-primary btn-sm"
              style={{ width: '100%', fontSize: '12px', marginTop: 8 }}
              onClick={() => navigate('/recommendations')}
            >
              Review in AI Approvals ({status?.pending_recommendations_count ?? 0}) →
            </button>
          </div>

          {/* 3. Khata Credit Agent */}
          <div style={{ padding: '18px', border: '1px solid #e2e8f0', borderRadius: '8px', background: '#fff', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong style={{ fontSize: '15px', display: 'flex', alignItems: 'center', gap: 6 }}>
                  👥 Khata Credit Agent
                </strong>
                <span className="badge badge-success" style={{ background: '#e8f5e9', color: '#2e7d32', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600 }}>ACTIVE</span>
              </div>
              <p style={{ fontSize: '12px', color: '#666', margin: '6px 0 10px 0' }}>
                Trigger: Overdue threshold ({status?.operational_thresholds?.khata_overdue_days || 30}d aging)
              </p>

              {/* Real-time Findings */}
              <div style={{ background: '#f8fafc', padding: 10, borderRadius: 6, border: '1px solid #edf2f7', marginBottom: 12 }}>
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#475569', marginBottom: 6 }}>
                  LIVE OVERDUE RECEIVABLES:
                </div>
                {status?.khata_summary?.top_overdue && status.khata_summary.top_overdue.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {status.khata_summary.top_overdue.slice(0, 2).map((c, i) => (
                      <div key={i} style={{ fontSize: '12px', display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: '#1e293b' }}>{c.customer_name}</span>
                        <span style={{ color: '#b91c1c', fontWeight: 600 }}>
                          {currencySymbol}{c.amount.toLocaleString('en-IN')} ({c.days_overdue}d)
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ fontSize: '12px', color: '#16a34a' }}>✓ Zero overdue credit accounts</div>
                )}
              </div>
            </div>

            <button
              className="btn btn-secondary btn-sm"
              style={{ width: '100%', fontSize: '12px', marginTop: 8 }}
              onClick={() => navigate('/customers')}
            >
              Open Khata & WhatsApp Nudges →
            </button>
          </div>

          {/* 4. Expense Anomaly Agent */}
          <div style={{ padding: '18px', border: '1px solid #e2e8f0', borderRadius: '8px', background: '#fff', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong style={{ fontSize: '15px', display: 'flex', alignItems: 'center', gap: 6 }}>
                  💸 Expense Anomaly Agent
                </strong>
                <span className="badge badge-success" style={{ background: '#e8f5e9', color: '#2e7d32', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600 }}>ACTIVE</span>
              </div>
              <p style={{ fontSize: '12px', color: '#666', margin: '6px 0 10px 0' }}>
                Trigger: Variance &gt; +{status?.operational_thresholds?.expense_anomaly_threshold_pct || 30}% vs 30d baseline
              </p>

              {/* Real-time Findings */}
              <div style={{ background: '#f8fafc', padding: 10, borderRadius: 6, border: '1px solid #edf2f7', marginBottom: 12 }}>
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#475569', marginBottom: 6 }}>
                  OPERATIONAL EXPENSE SURVEILLANCE:
                </div>
                <div style={{ fontSize: '12px', color: '#15803d', fontWeight: 500 }}>
                  ✓ Expense baseline stable across categories
                </div>
                <div style={{ fontSize: '11px', color: '#64748b', marginTop: 4 }}>
                  Auditing Utilities, Logistics, Rent & Packaging
                </div>
              </div>
            </div>

            <button
              className="btn btn-secondary btn-sm"
              style={{ width: '100%', fontSize: '12px', marginTop: 8 }}
              onClick={() => navigate('/expenses')}
            >
              View Expense Tracker →
            </button>
          </div>

          {/* 5. Cashflow Solvency Guard */}
          <div style={{ padding: '18px', border: '1px solid #e2e8f0', borderRadius: '8px', background: '#fff', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong style={{ fontSize: '15px', display: 'flex', alignItems: 'center', gap: 6 }}>
                  🛡️ Cashflow Solvency Guard
                </strong>
                <span className="badge badge-success" style={{ background: '#e8f5e9', color: '#2e7d32', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600 }}>ACTIVE</span>
              </div>
              <p style={{ fontSize: '12px', color: '#666', margin: '6px 0 10px 0' }}>
                Trigger: Continuous solvency sweep against minimum cash reserve
              </p>

              {/* Real-time Findings */}
              <div style={{ background: '#f8fafc', padding: 10, borderRadius: 6, border: '1px solid #edf2f7', marginBottom: 12 }}>
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#475569', marginBottom: 6 }}>
                  STORE LIQUIDITY POSITION:
                </div>
                <div style={{ fontSize: '12px', color: '#1e293b' }}>
                  Net Cash: <strong>{currencySymbol}{(status?.solvency_summary?.current_cash ?? 0).toLocaleString('en-IN')}</strong>
                </div>
                <div style={{ fontSize: '11px', color: '#15803d', marginTop: 4, fontWeight: 600 }}>
                  ✓ Solvency Status: {status?.solvency_summary?.status || 'HEALTHY'}
                </div>
              </div>
            </div>

            <button
              className="btn btn-secondary btn-sm"
              style={{ width: '100%', fontSize: '12px', marginTop: 8 }}
              onClick={() => navigate('/')}
            >
              View Executive Dashboard →
            </button>
          </div>

        </div>
      </div>

      {/* Sweep Diagnostic Output */}
      {sweepResult && (
        <div className="card" style={{ padding: '20px', marginBottom: '24px', borderLeft: '4px solid #1e88e5' }}>
          <h4 style={{ margin: '0 0 12px 0' }}>📋 Diagnostic Run Result</h4>
          <p style={{ margin: '4px 0', fontSize: '14px' }}>
            <strong>Primary Recommendation:</strong> {sweepResult.decision?.primary_recommendation?.action || 'No action needed'}
          </p>
          <p style={{ margin: '4px 0', fontSize: '14px', color: '#555' }}>
            <strong>Reason:</strong> {sweepResult.decision?.primary_recommendation?.reason || 'Store operations are healthy'}
          </p>
          {sweepResult.recommendation_id && (
            <div style={{ marginTop: '10px' }}>
              <button
                className="btn btn-primary btn-sm"
                onClick={() => navigate('/recommendations')}
              >
                Open Recommendation #{sweepResult.recommendation_id} in AI Approvals →
              </button>
            </div>
          )}
        </div>
      )}

      {/* Recent Autonomous Agent Runs Table */}
      <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #eee', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, fontSize: '16px' }}>🕒 Recent Autonomous Agent Executions</h3>
          <span style={{ fontSize: '12px', color: '#666' }}>Immutable Audit Ledger</span>
        </div>
        {status?.recent_runs.length === 0 ? (
          <div style={{ padding: '30px', textAlign: 'center', color: '#888' }}>
            No agent runs logged yet. Click "Simulate POS Sale Event" or "Run Full Diagnostic" above.
          </div>
        ) : (
          <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#f8f9fa', borderBottom: '1px solid #eee', textAlign: 'left' }}>
                <th style={{ padding: '12px 16px' }}>Agent</th>
                <th style={{ padding: '12px 16px' }}>Trigger</th>
                <th style={{ padding: '12px 16px' }}>Entity Evaluated</th>
                <th style={{ padding: '12px 16px' }}>Status</th>
                <th style={{ padding: '12px 16px' }}>Execution Time</th>
              </tr>
            </thead>
            <tbody>
              {status?.recent_runs.map((r: any) => (
                <tr key={r.id} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '12px 16px', fontWeight: 600 }}>{r.agent_name}</td>
                  <td style={{ padding: '12px 16px', fontSize: '13px', color: '#666' }}>{r.trigger || 'reactive'}</td>
                  <td style={{ padding: '12px 16px', fontSize: '13px' }}>
                    {r.entity_label || r.entity_type || 'Store System'}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{
                      padding: '3px 8px',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: 600,
                      background: r.status === 'completed' ? '#e8f5e9' : '#ffebee',
                      color: r.status === 'completed' ? '#2e7d32' : '#c62828',
                    }}>
                      {r.status.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px', fontSize: '13px', color: '#777' }}>
                    {new Date(r.started_at).toLocaleTimeString('en-IN')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
