import React, { useEffect, useState } from 'react';
import { runMonteCarloSimulation, MonteCarloResponse, MonteCarloRequest } from '../api';

export const DigitalTwinPage: React.FC = () => {
  const [demandShock, setDemandShock] = useState<number>(0);
  const [supplierInflation, setSupplierInflation] = useState<number>(10);
  const [creditDefaultRate, setCreditDefaultRate] = useState<number>(15);
  const [horizonDays, setHorizonDays] = useState<number>(30);
  const [numRuns, setNumRuns] = useState<number>(1000);
  const [enableSafeguards, setEnableSafeguards] = useState<boolean>(true);

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<MonteCarloResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const executeSimulation = async (paramsOverride?: Partial<MonteCarloRequest>) => {
    try {
      setLoading(true);
      setError(null);
      const payload: MonteCarloRequest = {
        demand_shock_pct: paramsOverride?.demand_shock_pct ?? demandShock,
        supplier_inflation_pct: paramsOverride?.supplier_inflation_pct ?? supplierInflation,
        credit_default_rate_pct: paramsOverride?.credit_default_rate_pct ?? creditDefaultRate,
        horizon_days: paramsOverride?.horizon_days ?? horizonDays,
        num_simulations: paramsOverride?.num_simulations ?? numRuns,
        enable_ai_safeguards: paramsOverride?.enable_ai_safeguards ?? enableSafeguards,
      };
      const res = await runMonteCarloSimulation(payload);
      setResult(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Simulation execution failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    executeSimulation();
  }, []);

  const handleApplyPreset = (preset: 'diwali' | 'slump' | 'squeeze') => {
    if (preset === 'diwali') {
      setDemandShock(80);
      setSupplierInflation(15);
      setCreditDefaultRate(5);
      executeSimulation({ demand_shock_pct: 80, supplier_inflation_pct: 15, credit_default_rate_pct: 5 });
    } else if (preset === 'slump') {
      setDemandShock(-35);
      setSupplierInflation(5);
      setCreditDefaultRate(30);
      executeSimulation({ demand_shock_pct: -35, supplier_inflation_pct: 5, credit_default_rate_pct: 30 });
    } else if (preset === 'squeeze') {
      setDemandShock(-10);
      setSupplierInflation(25);
      setCreditDefaultRate(20);
      executeSimulation({ demand_shock_pct: -10, supplier_inflation_pct: 25, credit_default_rate_pct: 20 });
    }
  };

  // SVG Chart Dimensions & Scaling
  const chartWidth = 720;
  const chartHeight = 280;
  const padding = 50;

  const maxCash = result ? Math.max(...result.trajectories.map((t) => t.p95), result.starting_cash * 1.2) : 700000;
  const minCash = result ? Math.min(0, ...result.trajectories.map((t) => Math.min(t.p5, t.unmanaged_p50))) : 0;

  const scaleX = (day: number) => padding + (day / horizonDays) * (chartWidth - padding * 2);
  const scaleY = (val: number) => {
    const range = maxCash - minCash;
    if (range === 0) return chartHeight / 2;
    return chartHeight - padding - ((val - minCash) / range) * (chartHeight - padding * 2);
  };

  // Generate SVG path strings
  const getPathString = (field: 'p50' | 'p5' | 'p95' | 'unmanaged_p50') => {
    if (!result || result.trajectories.length === 0) return '';
    return result.trajectories.reduce((acc, pt, i) => {
      const x = scaleX(pt.day);
      const y = scaleY(pt[field]);
      return i === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
    }, '');
  };

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
      {/* Page Header */}
      <div className="page-header" style={{ marginBottom: '24px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 className="page-title">Kirana Digital Twin & Solvency Sandbox</h1>
            <span
              style={{
                background: '#fef3c7',
                color: '#b45309',
                border: '1px solid #fde68a',
                padding: '3px 10px',
                borderRadius: '20px',
                fontSize: '11px',
                fontWeight: 700,
              }}
            >
              Monte Carlo Stochastic Engine (N=1,000)
            </span>
          </div>
          <p className="page-subtitle">
            Simulate macroeconomic shocks, supplier wholesale inflation, and credit defaults to stress-test store liquidity
          </p>
        </div>

        <div className="header-actions">
          <button
            className="btn btn-primary"
            onClick={() => executeSimulation()}
            disabled={loading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
              borderColor: '#059669',
              fontWeight: 700,
              padding: '10px 20px',
            }}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                <span>Computing 1,000 Paths...</span>
              </>
            ) : (
              <>
                <span>🎲</span>
                <span>Run Monte Carlo Simulation</span>
              </>
            )}
          </button>
        </div>
      </div>

      {error && <div className="error-banner">⚠️ {error}</div>}

      {/* Preset Demo Scenarios */}
      <div
        style={{
          background: '#ffffff',
          borderRadius: '14px',
          border: '1px solid #e2e8f0',
          padding: '16px 20px',
          marginBottom: '24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '18px' }}>⚡</span>
          <span style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a' }}>
            1-Click Stress Test Scenarios (For Guide Evaluation):
          </span>
        </div>

        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => handleApplyPreset('diwali')}
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <span>💥</span>
            <span>Diwali Demand Surge (+80% Sales)</span>
          </button>

          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => handleApplyPreset('slump')}
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <span>🌧️</span>
            <span>Monsoon Slump (-35% Sales, 30% Default)</span>
          </button>

          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => handleApplyPreset('squeeze')}
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <span>📉</span>
            <span>Wholesale Margin Squeeze (+25% Inflation)</span>
          </button>
        </div>
      </div>

      {/* Main Grid: Sliders on Left + Stochastic Chart on Right */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(340px, 1fr) minmax(580px, 1.8fr)', gap: '24px', alignItems: 'start', marginBottom: '24px' }}>
        
        {/* Left Column: Interactive Shock Sliders */}
        <div className="card" style={{ padding: '24px' }}>
          <div className="card-title" style={{ marginBottom: '18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>🎛️</span>
            <span>Macroeconomic Shock Sliders</span>
          </div>

          {/* Slider 1: Demand Volatility */}
          <div style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <label style={{ fontSize: '12px', fontWeight: 700, color: '#334155' }}>
                Demand Shock (Sales Volatility)
              </label>
              <span style={{ fontSize: '13px', fontWeight: 800, color: demandShock >= 0 ? '#10b981' : '#ef4444' }}>
                {demandShock > 0 ? `+${demandShock}%` : `${demandShock}%`}
              </span>
            </div>
            <input
              type="range"
              min="-50"
              max="100"
              step="5"
              value={demandShock}
              onChange={(e) => setDemandShock(Number(e.target.value))}
              style={{ width: '100%', accentColor: demandShock >= 0 ? '#10b981' : '#ef4444' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#94a3b8' }}>
              <span>-50% Slump</span>
              <span>Baseline (0%)</span>
              <span>+100% Festival</span>
            </div>
          </div>

          {/* Slider 2: Supplier Wholesale Inflation */}
          <div style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <label style={{ fontSize: '12px', fontWeight: 700, color: '#334155' }}>
                Supplier Cost Inflation
              </label>
              <span style={{ fontSize: '13px', fontWeight: 800, color: '#f59e0b' }}>
                +{supplierInflation}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="30"
              step="1"
              value={supplierInflation}
              onChange={(e) => setSupplierInflation(Number(e.target.value))}
              style={{ width: '100%', accentColor: '#f59e0b' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#94a3b8' }}>
              <span>0% Stable</span>
              <span>+15% Moderate</span>
              <span>+30% Severe</span>
            </div>
          </div>

          {/* Slider 3: Khata Credit Default Rate */}
          <div style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <label style={{ fontSize: '12px', fontWeight: 700, color: '#334155' }}>
                Customer Credit Default Rate
              </label>
              <span style={{ fontSize: '13px', fontWeight: 800, color: '#ef4444' }}>
                {creditDefaultRate}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="50"
              step="5"
              value={creditDefaultRate}
              onChange={(e) => setCreditDefaultRate(Number(e.target.value))}
              style={{ width: '100%', accentColor: '#ef4444' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#94a3b8' }}>
              <span>0% Full Recovery</span>
              <span>25% Lagging</span>
              <span>50% Non-payment</span>
            </div>
          </div>

          {/* Horizon & Runs Selection */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '20px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: '#64748b', marginBottom: '4px' }}>
                Horizon (Days)
              </label>
              <select
                value={horizonDays}
                onChange={(e) => setHorizonDays(Number(e.target.value))}
                style={{ width: '100%', padding: '8px 10px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '12px' }}
              >
                <option value={15}>15 Days</option>
                <option value={30}>30 Days</option>
                <option value={60}>60 Days</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: '#64748b', marginBottom: '4px' }}>
                Monte Carlo Paths
              </label>
              <select
                value={numRuns}
                onChange={(e) => setNumRuns(Number(e.target.value))}
                style={{ width: '100%', padding: '8px 10px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '12px' }}
              >
                <option value={200}>200 Runs</option>
                <option value={500}>500 Runs</option>
                <option value={1000}>1,000 Runs</option>
              </select>
            </div>
          </div>

          {/* AI Safeguards Toggle */}
          <div
            style={{
              background: enableSafeguards ? '#f0fdf4' : '#fff1f2',
              border: `1.5px solid ${enableSafeguards ? '#bbf7d0' : '#fecdd3'}`,
              borderRadius: '10px',
              padding: '12px 14px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ fontSize: '12px', fontWeight: 700, color: enableSafeguards ? '#15803d' : '#9f1239' }}>
                MicroBiz Multi-Agent Reserve Lock
              </div>
              <div style={{ fontSize: '10px', color: '#64748b' }}>
                {enableSafeguards ? 'AI auto-trims POs when approaching ₹50,000' : 'Unmanaged shopkeeper baseline'}
              </div>
            </div>

            <input
              type="checkbox"
              checked={enableSafeguards}
              onChange={(e) => setEnableSafeguards(e.target.checked)}
              style={{ width: '18px', height: '18px', accentColor: '#16a34a', cursor: 'pointer' }}
            />
          </div>
        </div>

        {/* Right Column: Statistical Scorecards & Stochastic Trajectory Fan Chart */}
        <div className="card" style={{ padding: '24px' }}>
          {/* Top Scorecard Metrics */}
          {result && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '14px', marginBottom: '24px' }}>
              {/* Insolvency Risk AI vs Unmanaged */}
              <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700 }}>Insolvency Probability</div>
                <div style={{ fontSize: '22px', fontWeight: 800, color: result.probability_of_insolvency_pct > 15 ? '#e11d48' : '#10b981', marginTop: '2px' }}>
                  {result.probability_of_insolvency_pct}%
                </div>
                <div style={{ fontSize: '10px', color: '#e11d48', marginTop: '2px' }}>
                  vs <strong>{result.unmanaged_insolvency_pct}%</strong> (Unmanaged)
                </div>
              </div>

              {/* Value at Risk (VaR 95%) */}
              <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700 }}>Value at Risk (VaR 95%)</div>
                <div style={{ fontSize: '22px', fontWeight: 800, color: '#0f172a', marginTop: '2px' }}>
                  ₹{(result.value_at_risk_95 / 1000).toFixed(1)}k
                </div>
                <div style={{ fontSize: '10px', color: '#64748b', marginTop: '2px' }}>
                  Max 95% confidence loss
                </div>
              </div>

              {/* Expected Ending Cash */}
              <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700 }}>Projected Median Cash</div>
                <div style={{ fontSize: '22px', fontWeight: 800, color: '#10b981', marginTop: '2px' }}>
                  ₹{(result.expected_ending_cash / 1000).toFixed(0)}k
                </div>
                <div style={{ fontSize: '10px', color: '#64748b', marginTop: '2px' }}>
                  At Day {result.horizon_days}
                </div>
              </div>

              {/* Stress Verdict */}
              <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700 }}>Resilience Rating</div>
                <div style={{ fontSize: '13px', fontWeight: 800, color: result.risk_color, marginTop: '6px' }}>
                  {result.stress_verdict}
                </div>
              </div>
            </div>
          )}

          {/* SVG Stochastic Fan Chart */}
          <div style={{ background: '#090d16', borderRadius: '12px', padding: '16px', position: 'relative', overflow: 'hidden' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <span style={{ fontSize: '12px', fontWeight: 700, color: '#f8fafc' }}>
                📈 Stochastic Cash Trajectory Distribution (1,000 Sample Paths)
              </span>
              <div style={{ display: 'flex', gap: '14px', fontSize: '11px' }}>
                <span style={{ color: '#34d399' }}>● MicroBiz AI Median</span>
                <span style={{ color: '#f87171' }}>-- Unmanaged Baseline</span>
                <span style={{ color: '#f59e0b' }}>--- ₹50k Reserve Floor</span>
              </div>
            </div>

            <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
              {/* Grid Lines */}
              <line x1={padding} y1={chartHeight - padding} x2={chartWidth - padding} y2={chartHeight - padding} stroke="rgba(255,255,255,0.15)" strokeWidth="1" />
              <line x1={padding} y1={padding} x2={padding} y2={chartHeight - padding} stroke="rgba(255,255,255,0.15)" strokeWidth="1" />

              {/* Minimum Reserve Line (₹50,000) */}
              {result && (
                <line
                  x1={padding}
                  y1={scaleY(result.min_cash_reserve)}
                  x2={chartWidth - padding}
                  y2={scaleY(result.min_cash_reserve)}
                  stroke="#f59e0b"
                  strokeWidth="1.5"
                  strokeDasharray="4 4"
                />
              )}

              {/* 90% Confidence Interval Band (p5 to p95) */}
              {result && (
                <path
                  d={`
                    ${getPathString('p95')}
                    ${result.trajectories.slice().reverse().map((pt) => `L ${scaleX(pt.day)} ${scaleY(pt.p5)}`).join(' ')}
                    Z
                  `}
                  fill="rgba(16, 185, 129, 0.12)"
                />
              )}

              {/* 50% Confidence Interval Band (p25 to p75) */}
              {result && (
                <path
                  d={`
                    ${result.trajectories.map((pt, i) => `${i === 0 ? 'M' : 'L'} ${scaleX(pt.day)} ${scaleY(pt.p75)}`).join(' ')}
                    ${result.trajectories.slice().reverse().map((pt) => `L ${scaleX(pt.day)} ${scaleY(pt.p25)}`).join(' ')}
                    Z
                  `}
                  fill="rgba(16, 185, 129, 0.22)"
                />
              )}

              {/* Unmanaged Baseline Trajectory */}
              {result && (
                <path
                  d={getPathString('unmanaged_p50')}
                  fill="none"
                  stroke="#f87171"
                  strokeWidth="2"
                  strokeDasharray="5 5"
                />
              )}

              {/* MicroBiz AI Median Trajectory */}
              {result && (
                <path
                  d={getPathString('p50')}
                  fill="none"
                  stroke="#34d399"
                  strokeWidth="2.5"
                />
              )}

              {/* Axis Labels */}
              <text x={padding} y={chartHeight - 15} fill="#94a3b8" fontSize="10">Day 0</text>
              <text x={chartWidth / 2} y={chartHeight - 15} fill="#94a3b8" fontSize="10">Day {horizonDays / 2}</text>
              <text x={chartWidth - padding - 20} y={chartHeight - 15} fill="#94a3b8" fontSize="10">Day {horizonDays}</text>

              <text x={10} y={padding + 10} fill="#94a3b8" fontSize="10">₹{(maxCash / 1000).toFixed(0)}k</text>
              <text x={10} y={scaleY(50000) + 4} fill="#f59e0b" fontSize="9">₹50k Floor</text>
              <text x={10} y={chartHeight - padding} fill="#94a3b8" fontSize="10">₹0</text>
            </svg>
          </div>

          {/* Executive Summary Box */}
          {result && (
            <div style={{ marginTop: '16px', background: '#f8fafc', padding: '12px 16px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: '11px', fontWeight: 700, color: '#334155', marginBottom: '2px' }}>
                Executive Assessment:
              </div>
              <p style={{ fontSize: '12px', color: '#475569', lineHeight: 1.5, margin: 0 }}>
                {result.executive_summary}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
