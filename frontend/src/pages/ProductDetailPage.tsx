import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  getProduct,
  updateProduct,
  adjustProductStock,
  checkProductInventory,
  checkProductProfitability,
  getSales,
  getProductForecasts,
  Product,
  Sale,
  CheckInventoryResponse,
  CheckProfitabilityResponse,
  ForecastHistoryItem,
} from '../api';

export const ProductDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [product, setProduct] = useState<Product | null>(null);
  const [sales, setSales] = useState<Sale[]>([]);
  const [latestForecast, setLatestForecast] = useState<ForecastHistoryItem | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [stockInput, setStockInput] = useState<number>(0);
  const [adjustingStock, setAdjustingStock] = useState<boolean>(false);

  const [priceInput, setPriceInput] = useState<number>(0);
  const [updatingPrice, setUpdatingPrice] = useState<boolean>(false);

  // Agent results
  const [checkingInventory, setCheckingInventory] = useState<boolean>(false);
  const [inventoryResult, setInventoryResult] = useState<CheckInventoryResponse | null>(null);

  const [checkingProfitability, setCheckingProfitability] = useState<boolean>(false);
  const [profitabilityResult, setProfitabilityResult] = useState<CheckProfitabilityResponse | null>(null);

  const loadProductData = async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const [prodData, salesData, forecastsData] = await Promise.all([
        getProduct(id),
        getSales(id),
        getProductForecasts(id).catch(() => []),
      ]);
      setProduct(prodData);
      setStockInput(prodData.current_stock);
      setPriceInput(prodData.selling_price);
      setSales(salesData);
      if (forecastsData.length > 0) {
        setLatestForecast(forecastsData[0]);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load product details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProductData();
  }, [id]);

  const handleAdjustStock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    try {
      setAdjustingStock(true);
      setError(null);
      const updated = await adjustProductStock(id, Number(stockInput));
      setProduct(updated);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to adjust stock');
    } finally {
      setAdjustingStock(false);
    }
  };

  const handleUpdatePrice = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    try {
      setUpdatingPrice(true);
      setError(null);
      const updated = await updateProduct(id, { selling_price: Number(priceInput) });
      setProduct(updated);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to update price');
    } finally {
      setUpdatingPrice(false);
    }
  };

  const handleCheckInventoryRisk = async () => {
    if (!id) return;
    try {
      setCheckingInventory(true);
      setError(null);
      const res = await checkProductInventory(id);
      setInventoryResult(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Inventory risk assessment failed');
    } finally {
      setCheckingInventory(false);
    }
  };

  const handleCheckProfitability = async () => {
    if (!id) return;
    try {
      setCheckingProfitability(true);
      setError(null);
      const res = await checkProductProfitability(id);
      setProfitabilityResult(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Profitability assessment failed');
    } finally {
      setCheckingProfitability(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 48 }}>
        <span className="spinner"></span> Loading product details...
      </div>
    );
  }

  if (!product) {
    return (
      <div className="empty-state">
        <h2>Product not found</h2>
        <button className="btn btn-secondary" onClick={() => navigate('/products')} style={{ marginTop: 16 }}>
          ← Back to Products
        </button>
      </div>
    );
  }

  const isLowStock = product.current_stock < product.reorder_level;
  const margin =
    product.selling_price > 0
      ? ((product.selling_price - product.cost_price) / product.selling_price) * 100
      : 0;

  return (
    <div>
      <div className="page-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
            <Link to="/products" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>
              ← Products
            </Link>
            <span style={{ color: 'var(--text-muted)' }}>/</span>
            <span style={{ fontFamily: 'JetBrains Mono', color: '#94a3b8' }}>{product.sku}</span>
          </div>
          <h1 className="page-title">{product.name}</h1>
        </div>

        <div className="header-actions">
          <button
            className="btn btn-primary"
            onClick={handleCheckInventoryRisk}
            disabled={checkingInventory}
          >
            {checkingInventory ? <span className="spinner"></span> : '🔍 Check Stockout Risk'}
          </button>

          <button
            className="btn btn-secondary"
            onClick={handleCheckProfitability}
            disabled={checkingProfitability}
          >
            {checkingProfitability ? <span className="spinner"></span> : '📊 Check Margin'}
          </button>
        </div>
      </div>

      {error && <div className="error-banner">⚠️ {error}</div>}

      {/* Real-time Agent Result Box: Inventory */}
      {inventoryResult && (
        <div className="card" style={{ borderColor: '#38bdf8', background: 'rgba(15, 23, 42, 0.9)' }}>
          <div className="card-header">
            <div className="card-title" style={{ color: '#38bdf8', display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>📦 Live Inventory Agent Risk Assessment</span>
              <span
                className={`badge ${
                  inventoryResult.agent_result.stockout_risk === 'HIGH'
                    ? 'badge-high'
                    : inventoryResult.agent_result.stockout_risk === 'MEDIUM'
                    ? 'badge-medium'
                    : 'badge-low'
                }`}
              >
                {inventoryResult.agent_result.stockout_risk} RISK
              </span>
            </div>
            {inventoryResult.recommendation_created && (
              <Link to="/recommendations" className="btn btn-success btn-sm">
                Action Created in Inbox →
              </Link>
            )}
          </div>

          <div className="agent-metric-grid">
            <div className="agent-metric">
              <div className="agent-metric-val">{inventoryResult.agent_result.current_stock}</div>
              <div className="agent-metric-lbl">Current Stock</div>
            </div>
            <div className="agent-metric">
              <div className="agent-metric-val">{inventoryResult.agent_result.forecast_demand}</div>
              <div className="agent-metric-lbl">7-Day Demand</div>
            </div>
            <div className="agent-metric">
              <div className="agent-metric-val" style={{ color: inventoryResult.agent_result.stock_gap > 0 ? '#ef4444' : '#10b981' }}>
                {inventoryResult.agent_result.stock_gap}
              </div>
              <div className="agent-metric-lbl">Stock Gap</div>
            </div>
            <div className="agent-metric">
              <div className="agent-metric-val">
                {inventoryResult.agent_result.stock_coverage_days !== null
                  ? `${inventoryResult.agent_result.stock_coverage_days}d`
                  : '∞'}
              </div>
              <div className="agent-metric-lbl">Coverage Days</div>
            </div>
            <div className="agent-metric">
              <div className="agent-metric-val" style={{ color: '#60a5fa' }}>
                {inventoryResult.agent_result.recommended_order_quantity}
              </div>
              <div className="agent-metric-lbl">Recommended Order</div>
            </div>
          </div>
        </div>
      )}

      {/* Real-time Agent Result Box: Profitability */}
      {profitabilityResult && (
        <div className="card" style={{ borderColor: '#a855f7', background: 'rgba(30, 27, 75, 0.4)' }}>
          <div className="card-header">
            <div className="card-title" style={{ color: '#c084fc', display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>💰 Profitability Agent Analysis</span>
              <span
                className={`badge ${
                  profitabilityResult.agent_result.classification === 'loss_making'
                    ? 'badge-high'
                    : profitabilityResult.agent_result.classification === 'low_margin'
                    ? 'badge-medium'
                    : 'badge-low'
                }`}
              >
                {profitabilityResult.agent_result.classification.replace('_', ' ')}
              </span>
            </div>
            {profitabilityResult.recommendation_created && (
              <Link to="/recommendations" className="btn btn-primary btn-sm">
                Pricing Action Created →
              </Link>
            )}
          </div>

          <div className="agent-metric-grid">
            <div className="agent-metric">
              <div className="agent-metric-val">₹{profitabilityResult.agent_result.unit_profit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
              <div className="agent-metric-lbl">Unit Profit</div>
            </div>
            <div className="agent-metric">
              <div className="agent-metric-val" style={{ color: profitabilityResult.agent_result.profit_margin < 0 ? '#ef4444' : '#10b981' }}>
                {profitabilityResult.agent_result.profit_margin.toFixed(1)}%
              </div>
              <div className="agent-metric-lbl">Margin %</div>
            </div>
            <div className="agent-metric">
              <div className="agent-metric-val">₹{profitabilityResult.agent_result.gross_profit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
              <div className="agent-metric-lbl">Gross Profit (30d)</div>
            </div>
          </div>
        </div>
      )}

      {/* Latest Forecast Widget */}
      <div
        className="card"
        style={{
          background: 'linear-gradient(135deg, rgba(30, 27, 75, 0.5), rgba(15, 23, 42, 0.8))',
          border: '1px solid rgba(99, 102, 241, 0.4)',
          marginBottom: 24,
        }}
      >
        <div className="card-header" style={{ marginBottom: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: '1.2rem' }}>📈</span>
            <h3 className="card-title" style={{ margin: 0, color: '#818cf8' }}>
              Sales Demand Forecast
            </h3>
            {latestForecast && (
              <span
                className={`badge ${
                  latestForecast.status === 'active'
                    ? 'badge-pending'
                    : latestForecast.status === 'acted_on'
                    ? 'badge-approved'
                    : 'badge-rejected'
                }`}
              >
                {latestForecast.status}
              </span>
            )}
          </div>

          <Link
            to={`/forecasting?product_id=${product.id}`}
            className="btn btn-primary btn-sm"
          >
            {latestForecast ? 'Open in Forecasting Hub →' : 'Run Dedicated Forecast →'}
          </Link>
        </div>

        {latestForecast ? (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Latest projection ({latestForecast.horizon_days}-Day Horizon • {latestForecast.forecast_date}):
              </div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#60a5fa', marginTop: 2 }}>
                {latestForecast.predicted_sales.toFixed(1)} units projected
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Stock Gap vs {product.current_stock.toFixed(0)} units on hand:
              </div>
              <div
                style={{
                  fontSize: '1.2rem',
                  fontWeight: 700,
                  color: latestForecast.predicted_sales > product.current_stock ? '#ef4444' : '#10b981',
                  marginTop: 2,
                }}
              >
                {latestForecast.predicted_sales > product.current_stock
                  ? `Shortage of ${(latestForecast.predicted_sales - product.current_stock).toFixed(1)} units`
                  : '✓ Adequate inventory'}
              </div>
            </div>
          </div>
        ) : (
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', margin: 0 }}>
            No sales forecast has been generated for this product yet. Click above to run an on-demand projection.
          </p>
        )}
      </div>

      {/* Grid: Product specs & stock adjustment */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 24, marginBottom: 24 }}>
        {/* Specs Card */}
        <div className="card">
          <h3 className="card-title" style={{ marginBottom: 16 }}>Product Specifications</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>SKU</div>
              <div style={{ fontFamily: 'JetBrains Mono', fontWeight: 600 }}>{product.sku}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Current Stock</div>
              <div style={{ fontWeight: 700, fontSize: '1.2rem', color: isLowStock ? '#f87171' : '#f8fafc' }}>
                {product.current_stock} units {isLowStock && <span className="badge badge-high">Low</span>}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Reorder Threshold</div>
              <div>{product.reorder_level} units</div>
            </div>
            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Safety Buffer</div>
              <div>{product.safety_stock} units</div>
            </div>
            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Cost Price</div>
              <div>₹{product.cost_price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Supplier Lead Time</div>
              <div>{product.lead_time_days} days</div>
            </div>
          </div>

          <hr style={{ borderColor: 'var(--border-color)', margin: '18px 0' }} />

          {/* Edit Selling Price Form */}
          <form onSubmit={handleUpdatePrice} style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
            <div className="form-group" style={{ flex: 1 }}>
              <label>Selling Price (₹)</label>
              <input
                type="number"
                step="0.01"
                required
                className="form-control"
                value={priceInput}
                onChange={(e) => setPriceInput(Number(e.target.value))}
              />
            </div>
            <button type="submit" className="btn btn-secondary" disabled={updatingPrice}>
              {updatingPrice ? 'Saving...' : 'Update Price'}
            </button>
          </form>
        </div>

        {/* ML Profile Card */}
        <div className="card" style={{ border: '1px solid rgba(59, 130, 246, 0.3)', background: 'rgba(15, 23, 42, 0.6)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 className="card-title" style={{ color: '#60a5fa', margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>🤖 ML Model Profile</span>
            </h3>
            {product.ml_ready ? (
              <span className="badge badge-low">✓ Trained RF Ready</span>
            ) : (
              <span className="badge badge-medium">○ Baseline Velocity</span>
            )}
          </div>

          <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: 16 }}>
            Parameters mapped directly into the 25-feature input vector for the trained Random Forest demand forecaster:
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Store Type</div>
              <div style={{ fontWeight: 600 }}>
                {product.store_type ? `Type ${product.store_type.toUpperCase()}` : 'Not set (default A)'}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Assortment</div>
              <div style={{ fontWeight: 600 }}>
                {product.assortment ? `Level ${product.assortment.toUpperCase()}` : 'Not set (default A)'}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Competition Distance</div>
              <div style={{ fontWeight: 600 }}>
                {product.competition_distance ? `${product.competition_distance} meters` : 'None nearby (default)'}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Active Promo</div>
              <div style={{ fontWeight: 600, color: product.promo_active ? '#34d399' : '#94a3b8' }}>
                {product.promo_active ? '🔥 Active (Promo=1)' : 'Inactive (Promo=0)'}
              </div>
            </div>
          </div>

          <div style={{ marginTop: 16, padding: 12, background: 'rgba(59, 130, 246, 0.08)', borderRadius: 6, fontSize: '0.8rem', color: '#93c5fd' }}>
            ℹ️ When you run a sales forecast, the trained Random Forest model predicts overall store demand incorporating these features, then scales this product's historical demand proportionally.
          </div>
        </div>

        {/* Stock Adjustment Card */}
        <div className="card">
          <h3 className="card-title" style={{ marginBottom: 16 }}>🚚 Adjust Stock Level (Delivery / Inventory Audit)</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: 16 }}>
            Directly update physical count after receiving a supplier delivery or reconciling inventory count.
          </p>
          <form onSubmit={handleAdjustStock}>
            <div className="form-group" style={{ marginBottom: 16 }}>
              <label>New On-Hand Stock Count</label>
              <input
                type="number"
                step="1"
                required
                className="form-control"
                value={stockInput}
                onChange={(e) => setStockInput(Number(e.target.value))}
              />
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={adjustingStock}>
              {adjustingStock ? 'Updating Stock...' : 'Save New Stock Count'}
            </button>
          </form>
        </div>
      </div>

      {/* Sales History Table for this Product */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Recent Product Sales ({sales.length})</h3>
          <Link to="/sales" className="btn btn-outline btn-sm">
            ➕ Log Sale
          </Link>
        </div>

        {sales.length === 0 ? (
          <div className="empty-state">
            <p>No sales recorded for this product yet.</p>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Sale ID</th>
                <th>Date</th>
                <th>Quantity</th>
                <th>Unit Price</th>
                <th>Total Revenue</th>
                <th>Customer ID</th>
              </tr>
            </thead>
            <tbody>
              {sales.map((s) => (
                <tr key={s.id}>
                  <td>#{s.id}</td>
                  <td>{s.date || 'Today'}</td>
                  <td><strong>{s.quantity}</strong></td>
                  <td>₹{s.unit_price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                  <td><strong style={{ color: '#10b981' }}>₹{s.total_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong></td>
                  <td>
                    {s.customer_id ? (
                      <Link to={`/customers/${s.customer_id}`} style={{ color: '#60a5fa' }}>
                        {s.customer_id.slice(0, 8)}...
                      </Link>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>Walk-in</span>
                    )}
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
