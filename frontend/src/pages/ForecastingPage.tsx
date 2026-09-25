import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  getProducts,
  runProductForecast,
  getProductForecasts,
  actOnForecast,
  Product,
  ForecastResponse,
  ForecastHistoryItem,
} from '../api';

export const ForecastingPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialProductId = searchParams.get('product_id') || '';

  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<string>(initialProductId);
  const [horizonDays, setHorizonDays] = useState<number>(7);

  const [runningForecast, setRunningForecast] = useState<boolean>(false);
  const [latestForecast, setLatestForecast] = useState<ForecastResponse | null>(null);
  const [history, setHistory] = useState<ForecastHistoryItem[]>([]);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Manual stock adjustment state
  const [showAdjustInput, setShowAdjustInput] = useState<boolean>(false);
  const [stockAdjustValue, setStockAdjustValue] = useState<number>(0);
  const [acting, setActing] = useState<boolean>(false);

  // Load products list
  useEffect(() => {
    const loadInitData = async () => {
      try {
        setLoading(true);
        setError(null);
        const prods = await getProducts();
        setProducts(prods);

        if (prods.length > 0) {
          const defaultId = initialProductId && prods.some((p) => p.id === initialProductId)
            ? initialProductId
            : prods[0].id;
          setSelectedProductId(defaultId);
        }
      } catch (err: any) {
        setError(err?.response?.data?.detail || err.message || 'Failed to load products');
      } finally {
        setLoading(false);
      }
    };
    loadInitData();
  }, []);

  // Load forecast history when selected product changes
  const loadProductHistory = async (productId: string) => {
    if (!productId) return;
    try {
      const hist = await getProductForecasts(productId);
      setHistory(hist);
    } catch (err: any) {
      // non-fatal for history
      console.error('History load error:', err);
    }
  };

  useEffect(() => {
    if (selectedProductId) {
      loadProductHistory(selectedProductId);
      setLatestForecast(null);
      setShowAdjustInput(false);
      setSuccessMsg(null);
    }
  }, [selectedProductId]);

  const handleProductChange = (productId: string) => {
    setSelectedProductId(productId);
    setSearchParams({ product_id: productId });
  };

  const handleRunForecast = async () => {
    if (!selectedProductId) return;
    try {
      setRunningForecast(true);
      setError(null);
      setSuccessMsg(null);
      setShowAdjustInput(false);

      const res = await runProductForecast(selectedProductId, horizonDays);
      setLatestForecast(res);
      setStockAdjustValue(res.current_stock);
      setSuccessMsg(`✅ Forecast generated: ${res.predicted_sales.toFixed(1)} units projected over ${res.horizon_days} days.`);
      await loadProductHistory(selectedProductId);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to generate forecast');
    } finally {
      setRunningForecast(false);
    }
  };

  const handleAct = async (
    forecastId: number,
    action: 'trigger_inventory_check' | 'adjust_stock' | 'dismiss',
    stockAdjustment?: number
  ) => {
    try {
      setActing(true);
      setError(null);
      setSuccessMsg(null);

      const res = await actOnForecast(forecastId, {
        action,
        stock_adjustment: stockAdjustment,
      });

      setSuccessMsg(`Action applied: ${res.message}`);
      setShowAdjustInput(false);

      // Update current displayed forecast status if matching
      if (latestForecast && latestForecast.id === forecastId) {
        setLatestForecast({
          ...latestForecast,
          status: res.status as any,
          current_stock: res.current_stock ?? latestForecast.current_stock,
        });
      }

      await loadProductHistory(selectedProductId);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to process action on forecast');
    } finally {
      setActing(false);
    }
  };

  const selectedProduct = products.find((p) => p.id === selectedProductId);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Sales Demand Forecasting</h1>
          <p className="page-subtitle">
            Decoupled Machine Learning & velocity demand projections with independent human decision controls
          </p>
        </div>
      </div>

      {error && <div className="error-banner">⚠️ {error}</div>}
      {successMsg && (
        <div className="success-banner">
          {successMsg}
        </div>
      )}

      {/* Control Panel: Product & Horizon Selector */}
      <div className="forecast-hero-card">
        <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: 18 }}>
          🎯 Run On-Demand Product Forecast
        </h2>

        <div className="form-grid">
          <div className="form-group" style={{ gridColumn: 'span 2' }}>
            <label>Select Target Product *</label>
            <select
              className="form-control"
              value={selectedProductId}
              onChange={(e) => handleProductChange(e.target.value)}
              disabled={loading || products.length === 0}
            >
              {products.length === 0 ? (
                <option value="">No products available</option>
              ) : (
                products.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.ml_ready ? '⚡ [RF Model]' : '○ [Baseline]'} {p.name} ({p.sku}) — Stock: {p.current_stock} — ₹{p.selling_price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </option>
                ))
              )}
            </select>

            {products.length === 0 && !loading && (
              <div style={{ marginTop: 12, padding: '12px 16px', background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 12, color: '#b45309', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span>📦 No products found in the database. Add your inventory first to run forecasts.</span>
                <Link to="/products" className="btn btn-primary btn-sm" style={{ padding: '6px 14px' }}>➕ Go to Products & Stock →</Link>
              </div>
            )}

            {selectedProduct && (
              <div style={{ marginTop: 10, fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-muted)' }}>
                {selectedProduct.ml_ready ? (
                  <span style={{ color: '#16a34a', display: 'flex', alignItems: 'center', gap: 6, fontWeight: 500 }}>
                    <span>⚡</span>
                    <strong>Trained Random Forest Ready:</strong> Store Type {selectedProduct.store_type?.toUpperCase()}, Assortment {selectedProduct.assortment?.toUpperCase()}, Comp: {selectedProduct.competition_distance || 0}m, Promo: {selectedProduct.promo_active ? 'Active' : 'Off'}
                  </span>
                ) : (
                  <span style={{ color: '#d97706', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span>⚠️</span>
                    <span>Using Historical Sales Velocity baseline (configure Store Type & Assortment in Product Details for ML).</span>
                  </span>
                )}
              </div>
            )}
          </div>

          <div className="form-group">
            <label>Forecast Horizon Window</label>
            <div style={{ display: 'flex', gap: 8 }}>
              {[7, 14, 30].map((days) => (
                <button
                  key={days}
                  type="button"
                  className={`btn btn-sm ${horizonDays === days ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ flex: 1, padding: '10px 0' }}
                  onClick={() => setHorizonDays(days)}
                >
                  {days} Days
                </button>
              ))}
            </div>
          </div>

          <div className="form-group" style={{ justifyContent: 'flex-end' }}>
            <button
              className="btn btn-primary"
              onClick={handleRunForecast}
              disabled={runningForecast || !selectedProductId}
              style={{ padding: '12px 24px', fontSize: '1rem' }}
            >
              {runningForecast ? (
                <>
                  <span className="spinner"></span>
                  <span>Forecasting Demand...</span>
                </>
              ) : (
                '📈 Generate Forecast'
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Latest Forecast Result & Human Decision Panel */}
      {latestForecast && (
        <div
          className={`forecast-result-card ${
            latestForecast.stockout_risk_preview === 'HIGH' ? 'risk-high' : ''
          }`}
        >
          <div className="card-header">
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                <span style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  📊 Forecast #{latestForecast.id}: {latestForecast.product_name || selectedProduct?.name}
                </span>
                <span
                  className={`badge ${
                    latestForecast.stockout_risk_preview === 'HIGH'
                      ? 'badge-high'
                      : latestForecast.stockout_risk_preview === 'MEDIUM'
                      ? 'badge-medium'
                      : 'badge-low'
                  }`}
                >
                  {latestForecast.stockout_risk_preview} RISK
                </span>
                <span
                  className={`badge ${
                    latestForecast.status === 'active'
                      ? 'badge-medium'
                      : latestForecast.status === 'acted_on'
                      ? 'badge-low'
                      : 'badge-high'
                  }`}
                >
                  {latestForecast.status.toUpperCase()}
                </span>
              </div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.86rem', marginTop: 4 }}>
                Planning Horizon: <strong>{latestForecast.horizon_days} Days</strong> • Generated {new Date(latestForecast.created_at).toLocaleTimeString()} • Model: <strong>{latestForecast.model_used}</strong>
              </div>
            </div>

            {selectedProduct && (
              <Link to={`/products/${selectedProduct.id}`} className="btn btn-outline btn-sm">
                View Product Details →
              </Link>
            )}
          </div>

          {/* Metric Tiles (Zomato-Style Clean Soft Gradients) */}
          <div className="agent-metric-grid" style={{ marginBottom: 24 }}>
            <div className="agent-metric" style={{ background: '#f0f7ff', borderColor: '#bfdbfe' }}>
              <div className="agent-metric-val" style={{ color: '#1d4ed8' }}>
                {latestForecast.predicted_sales.toFixed(1)} units
              </div>
              <div className="agent-metric-lbl" style={{ color: '#3b82f6' }}>
                Projected Customer Demand
              </div>
            </div>

            <div className="agent-metric" style={{ background: '#f8fafc', borderColor: '#e2e8f0' }}>
              <div className="agent-metric-val" style={{ color: '#1e293b' }}>
                {latestForecast.current_stock.toFixed(1)} units
              </div>
              <div className="agent-metric-lbl">Current On-Hand Stock</div>
            </div>

            <div
              className="agent-metric"
              style={{
                background: latestForecast.stock_gap_preview > 0 ? '#fff1f2' : '#f0fdf4',
                borderColor: latestForecast.stock_gap_preview > 0 ? '#fecdd3' : '#bbf7d0',
              }}
            >
              <div
                className="agent-metric-val"
                style={{ color: latestForecast.stock_gap_preview > 0 ? '#e11d48' : '#16a34a' }}
              >
                {latestForecast.stock_gap_preview > 0
                  ? `-${latestForecast.stock_gap_preview.toFixed(1)} units (Deficit)`
                  : '✓ Sufficient Stock'}
              </div>
              <div
                className="agent-metric-lbl"
                style={{ color: latestForecast.stock_gap_preview > 0 ? '#e11d48' : '#16a34a' }}
              >
                Stock Position / Reorder Gap
              </div>
            </div>
          </div>

          {/* Independent Human Decision Action Bar */}
          <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: 20 }}>
            <div style={{ fontSize: '0.84rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 12, letterSpacing: '0.5px' }}>
              Recommended Merchant Actions:
            </div>

            {latestForecast.status === 'active' ? (
              <div>
                {!showAdjustInput ? (
                  <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                    <button
                      className="btn btn-primary"
                      onClick={() => handleAct(latestForecast.id, 'trigger_inventory_check')}
                      disabled={acting}
                    >
                      {acting ? <span className="spinner"></span> : '⚡ Trigger Inventory Check & Queue Order'}
                    </button>

                    <button
                      className="btn btn-secondary"
                      onClick={() => setShowAdjustInput(true)}
                      disabled={acting}
                    >
                      📦 Adjust Stock Manually
                    </button>

                    <button
                      className="btn btn-outline"
                      onClick={() => handleAct(latestForecast.id, 'dismiss')}
                      disabled={acting}
                    >
                      ✕ Dismiss
                    </button>
                  </div>
                ) : (
                  <div style={{ background: '#ffffff', padding: 18, borderRadius: 14, border: '1px solid var(--border-color)', maxWidth: 520, boxShadow: 'var(--shadow-xs)' }}>
                    <label style={{ display: 'block', fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>
                      Set New Physical Stock Count for {selectedProduct?.name}:
                    </label>
                    <div style={{ display: 'flex', gap: 10 }}>
                      <input
                        type="number"
                        step="1"
                        min="0"
                        className="form-control"
                        value={stockAdjustValue}
                        onChange={(e) => setStockAdjustValue(Number(e.target.value))}
                      />
                      <button
                        className="btn btn-primary"
                        onClick={() => handleAct(latestForecast.id, 'adjust_stock', stockAdjustValue)}
                        disabled={acting}
                      >
                        {acting ? <span className="spinner"></span> : 'Save Stock'}
                      </button>
                      <button className="btn btn-secondary" onClick={() => setShowAdjustInput(false)}>
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                This forecast has already been <strong>{latestForecast.status}</strong>.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Historical Forecasts & Accuracy Table */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            📜 Forecast History & Real-World Accuracy ({history.length})
          </h2>
          {selectedProductId && (
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => loadProductHistory(selectedProductId)}
            >
              🔄 Refresh History
            </button>
          )}
        </div>

        {history.length === 0 ? (
          <div className="empty-state">
            <p>No historical forecasts recorded for this product yet. Click "Generate Forecast" above to run one.</p>
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Forecast ID</th>
                  <th>Date</th>
                  <th>Horizon</th>
                  <th>Predicted</th>
                  <th>Actual Sales</th>
                  <th>Accuracy / Deviation</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item) => (
                  <tr key={item.id}>
                    <td style={{ fontFamily: 'JetBrains Mono', color: 'var(--text-muted)' }}>#{item.id}</td>
                    <td>{item.forecast_date}</td>
                    <td><strong>{item.horizon_days}d</strong></td>
                    <td>
                      <strong style={{ color: '#60a5fa' }}>{item.predicted_sales.toFixed(1)}</strong>
                    </td>
                    <td>
                      {item.actual_sales !== null && item.actual_sales !== undefined ? (
                        <strong>{item.actual_sales.toFixed(1)}</strong>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>—</span>
                      )}
                    </td>
                    <td>
                      <span style={{ fontSize: '0.85rem', color: item.is_completed ? '#10b981' : '#94a3b8' }}>
                        {item.accuracy_note || 'Awaiting actual data'}
                      </span>
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          item.status === 'active'
                            ? 'badge-pending'
                            : item.status === 'acted_on'
                            ? 'badge-approved'
                            : 'badge-rejected'
                        }`}
                      >
                        {item.status}
                      </span>
                    </td>
                    <td>
                      {item.status === 'active' ? (
                        <div style={{ display: 'flex', gap: 6 }}>
                          <button
                            className="btn btn-primary btn-sm"
                            onClick={() => handleAct(item.id, 'trigger_inventory_check')}
                            disabled={acting}
                          >
                            Check Risk
                          </button>
                          <button
                            className="btn btn-outline btn-sm"
                            onClick={() => handleAct(item.id, 'dismiss')}
                            disabled={acting}
                          >
                            Dismiss
                          </button>
                        </div>
                      ) : (
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Closed</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
