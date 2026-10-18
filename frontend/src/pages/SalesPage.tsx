import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  getProducts,
  getCustomers,
  getSales,
  createSale,
  Product,
  Customer,
  Sale,
  SaleCreate,
  InventoryRisk,
} from '../api';
import { ProductCombobox } from '../components/ProductCombobox';

export const SalesPage: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [sales, setSales] = useState<Sale[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [recording, setRecording] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [lastRiskFeedback, setLastRiskFeedback] = useState<InventoryRisk | null>(null);
  const [activeAlarm, setActiveAlarm] = useState<{
    message: string;
    level: string;
    productName: string;
    remainingStock: number;
    rop: number;
    recId?: number | null;
    poId?: number | null;
  } | null>(null);

  const [formData, setFormData] = useState<SaleCreate>({
    product_id: '',
    customer_id: '',
    quantity: 1,
    unit_price: 0,
    date: new Date().toISOString().split('T')[0],
  });

  const [paymentMethod, setPaymentMethod] = useState<'CASH' | 'UPI' | 'CREDIT'>('CASH');

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [prods, custs, salesList] = await Promise.all([
        getProducts(),
        getCustomers(),
        getSales(),
      ]);
      setProducts(prods);
      setCustomers(custs);
      setSales(salesList);

      if (prods.length > 0 && !formData.product_id) {
        setFormData((prev) => ({
          ...prev,
          product_id: prods[0].id,
          unit_price: prods[0].selling_price,
        }));
      }

      // Automatically display latest post-sale risk feedback from recent transactions
      if (salesList.length > 0) {
        const recentWithRisk = salesList.find((s) => s.inventory_risk);
        if (recentWithRisk?.inventory_risk) {
          setLastRiskFeedback(recentWithRisk.inventory_risk);
        }
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load sales data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleProductChange = (productId: string) => {
    const selected = products.find((p) => p.id === productId);
    setFormData((prev) => ({
      ...prev,
      product_id: productId,
      unit_price: selected ? selected.selling_price : prev.unit_price,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.product_id) {
      setError('Please select a product');
      return;
    }
    try {
      setRecording(true);
      setError(null);
      setSuccessMsg(null);
      const sale = await createSale({
        product_id: formData.product_id,
        customer_id: formData.customer_id || undefined,
        quantity: Number(formData.quantity),
        unit_price: Number(formData.unit_price),
        date: formData.date || undefined,
      });

      setSuccessMsg(`✅ Recorded Sale #${sale.id} for ₹${sale.total_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })} (Stock automatically decremented).`);
      setLastRiskFeedback(sale.inventory_risk || null);

      if (sale.alarm_triggered && sale.alarm_message) {
        const prod = products.find((p) => p.id === formData.product_id);
        setActiveAlarm({
          message: sale.alarm_message,
          level: sale.alarm_level || 'CRITICAL',
          productName: prod ? prod.name : 'Product',
          remainingStock: sale.inventory_risk?.current_stock ?? 0,
          rop: sale.inventory_risk?.reorder_point ?? 0,
          recId: sale.recommendation_id,
          poId: sale.purchase_order_id,
        });
      }

      setFormData((prev) => ({ ...prev, quantity: 1 }));
      await loadData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to record sale');
    } finally {
      setRecording(false);
    }
  };

  const fillSampleSale = () => {
    if (products.length === 0) return;
    const sorted = [...products].sort((a, b) => a.current_stock - b.current_stock);
    const target = sorted[0];
    setFormData({
      product_id: target.id,
      customer_id: customers.length > 0 ? customers[0].id : '',
      quantity: Math.min(2, Math.max(1, Math.floor(target.current_stock / 2) || 1)),
      unit_price: target.selling_price,
      date: new Date().toISOString().split('T')[0],
    });
  };

  const selectedProduct = products.find((p) => p.id === formData.product_id);
  const totalAmount = Number(formData.quantity || 0) * Number(formData.unit_price || 0);

  // Projected stock calculations for live preview
  const currentStock = selectedProduct ? selectedProduct.current_stock : 0;
  const reorderPoint = selectedProduct ? selectedProduct.reorder_level : 15;
  const leadTimeDays = selectedProduct?.lead_time_days || 3;
  const dailyBurnEst = Math.max(0.5, reorderPoint / leadTimeDays);
  const coverageDaysEst = (currentStock / dailyBurnEst).toFixed(1);
  const projectedStockAfter = currentStock - Number(formData.quantity || 1);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Point of Sale & Transaction History</h1>
          <p className="page-subtitle">Record item purchases with instant on-hand inventory reconciliation</p>
        </div>
      </div>

      {error && <div className="error-banner">⚠️ {error}</div>}
      {successMsg && (
        <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10b981', color: '#065f46', padding: 14, borderRadius: 10, marginBottom: 16 }}>
          {successMsg}
        </div>
      )}

      {/* Real-time Stock Breach Alarm Banner */}
      {activeAlarm && (
        <div
          className="card"
          style={{
            margin: '0 0 24px 0',
            border: '2px solid #ef4444',
            borderLeft: '8px solid #dc2626',
            background: 'linear-gradient(135deg, #fff1f2 0%, #fee2e2 100%)',
            boxShadow: '0 8px 30px rgba(225, 29, 72, 0.25)',
            padding: '20px 24px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 14 }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14, flex: 1 }}>
              <span style={{ fontSize: '2.4rem' }}>🚨</span>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginBottom: 6 }}>
                  <strong style={{ fontSize: '1.25rem', color: '#991b1b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Critical Stockout Alarm Triggered
                  </strong>
                  <span className="badge badge-critical" style={{ fontSize: '0.82rem', padding: '4px 10px' }}>
                    {activeAlarm.level} STOCK BREACH
                  </span>
                  <span className="badge" style={{ background: '#dbeafe', color: '#1e40af', border: '1px solid #93c5fd', fontSize: '0.8rem' }}>
                    AUTONOMOUS PIPELINE FIRED
                  </span>
                </div>
                <p style={{ margin: '4px 0 10px 0', fontSize: '0.98rem', color: '#7f1d1d', lineHeight: 1.5, fontWeight: 500 }}>
                  {activeAlarm.message}
                </p>
                <div style={{ display: 'flex', gap: 16, fontSize: '0.85rem', color: '#991b1b', flexWrap: 'wrap' }}>
                  <span>Product: <strong>{activeAlarm.productName}</strong></span>
                  <span>•</span>
                  <span>Remaining Stock: <strong>{activeAlarm.remainingStock} units</strong></span>
                  <span>•</span>
                  <span>Safety Threshold (ROP): <strong>{activeAlarm.rop} units</strong></span>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'flex-end' }}>
              <Link to="/recommendations" style={{ textDecoration: 'none' }}>
                <button
                  className="btn btn-primary"
                  style={{
                    background: '#dc2626',
                    borderColor: '#b91c1c',
                    fontWeight: 700,
                    padding: '10px 18px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    boxShadow: '0 4px 12px rgba(220, 38, 38, 0.4)',
                  }}
                >
                  ⚡ Authorize Replenishment in HITL Inbox (Ref #{activeAlarm.recId ?? 'NEW'}) →
                </button>
              </Link>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => setActiveAlarm(null)}
                style={{ fontSize: '0.78rem', color: '#7f1d1d', borderColor: '#fca5a5' }}
              >
                ✕ Silence Alarm
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Real-time Post-Sale Inventory Risk Feedback Card */}
      {lastRiskFeedback && (
        <div
          className="card"
          style={{
            margin: '0 0 24px 0',
            borderLeft: `6px solid ${
              lastRiskFeedback.risk_level === 'CRITICAL'
                ? '#e11d48'
                : lastRiskFeedback.risk_level === 'HIGH'
                ? '#f97316'
                : lastRiskFeedback.risk_level === 'MEDIUM'
                ? '#eab308'
                : '#16a34a'
            }`,
            background: '#ffffff',
            boxShadow: '0 4px 20px rgba(0,0,0,0.06)',
            borderRadius: '16px',
            padding: '20px 24px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
                <span style={{ fontSize: '1.4rem' }}>
                  {lastRiskFeedback.risk_level === 'CRITICAL' ? '🚨' : lastRiskFeedback.risk_level === 'HIGH' ? '⚠️' : '📦'}
                </span>
                <strong style={{ fontSize: '1.15rem', color: '#0f172a' }}>
                  Real-Time Post-Sale Risk Feedback: {lastRiskFeedback.product_name}
                </strong>
                <span
                  className={`badge ${
                    lastRiskFeedback.risk_level === 'CRITICAL'
                      ? 'badge-critical'
                      : lastRiskFeedback.risk_level === 'HIGH'
                      ? 'badge-high'
                      : lastRiskFeedback.risk_level === 'MEDIUM'
                      ? 'badge-medium'
                      : 'badge-low'
                  }`}
                  style={{ fontSize: '0.78rem' }}
                >
                  {lastRiskFeedback.risk_level} RISK
                </span>
              </div>
              <div style={{ display: 'flex', gap: '20px', marginTop: '10px', fontSize: '0.88rem', color: '#475569', flexWrap: 'wrap' }}>
                <span>
                  <strong>Remaining Stock:</strong>{' '}
                  <span style={{ color: lastRiskFeedback.current_stock < lastRiskFeedback.reorder_point ? '#e11d48' : '#0f172a', fontWeight: 700 }}>
                    {lastRiskFeedback.current_stock} units
                  </span>
                </span>
                <span>
                  <strong>Coverage Days:</strong>{' '}
                  <span style={{ color: Number(lastRiskFeedback.coverage_days) < 2 ? '#e11d48' : '#0f172a', fontWeight: 700 }}>
                    {lastRiskFeedback.coverage_days !== null && lastRiskFeedback.coverage_days !== undefined
                      ? `${Number(lastRiskFeedback.coverage_days).toFixed(1)} days`
                      : 'N/A'}
                  </span>
                </span>
                <span>
                  <strong>Reorder Point (ROP):</strong> <span style={{ fontWeight: 700 }}>{lastRiskFeedback.reorder_point} units</span>
                </span>
                <span>
                  <strong>Supplier Lead Time:</strong> <span style={{ fontWeight: 700 }}>{lastRiskFeedback.lead_time_days} days</span>
                </span>
              </div>
            </div>

            {lastRiskFeedback.reorder_needed ? (
              <div style={{ textAlign: 'right', background: '#fff1f2', border: '1px solid #fecdd3', borderRadius: '12px', padding: '12px 18px' }}>
                <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#9f1239', fontWeight: 700 }}>
                  Recommended Order Quantity
                </div>
                <div style={{ fontSize: '1.25rem', color: '#e11d48', fontWeight: 800 }}>
                  +{lastRiskFeedback.recommended_order_qty} units
                </div>
                <Link to="/recommendations" style={{ textDecoration: 'none' }}>
                  <button className="btn btn-sm btn-primary" style={{ marginTop: '6px' }}>
                    View Approvals →
                  </button>
                </Link>
              </div>
            ) : (
              <div style={{ textAlign: 'right', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '12px', padding: '12px 18px' }}>
                <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#166534', fontWeight: 700 }}>
                  Stock Status
                </div>
                <div style={{ fontSize: '1.1rem', color: '#16a34a', fontWeight: 800 }}>
                  ✓ Safe Reserve
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Sale Entry Card */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18, flexWrap: 'wrap', gap: 10 }}>
          <h2 className="card-title" style={{ margin: 0 }}>🛒 Record POS Sale</h2>
          <button
            type="button"
            className="btn btn-sm btn-secondary"
            onClick={fillSampleSale}
            style={{ background: '#fef3c7', color: '#b45309', border: '1px solid #fde68a', fontWeight: 600 }}
            title="Auto-fill sale for low-stock item to demonstrate instant risk computation"
          >
            ✨ Auto-Fill Sample Sale
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Live Pre-Sale Stock & Risk Indicator */}
          {selectedProduct && (
            <div
              style={{
                marginBottom: '20px',
                background: '#f8fafc',
                border: '1.5px solid #e2e8f0',
                borderRadius: '12px',
                padding: '14px 18px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '14px',
              }}
            >
              <div style={{ display: 'flex', gap: '20px', alignItems: 'center', flexWrap: 'wrap' }}>
                <div>
                  <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: '#64748b', fontWeight: 700, display: 'block' }}>
                    Current On-Hand
                  </span>
                  <strong style={{ fontSize: '1.1rem', color: currentStock < reorderPoint ? '#e11d48' : '#059669' }}>
                    {currentStock} units
                  </strong>
                </div>
                <div>
                  <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: '#64748b', fontWeight: 700, display: 'block' }}>
                    Reorder Point (ROP)
                  </span>
                  <strong style={{ fontSize: '1.1rem', color: '#0f172a' }}>
                    {reorderPoint} units
                  </strong>
                </div>
                <div>
                  <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: '#64748b', fontWeight: 700, display: 'block' }}>
                    Est. Coverage
                  </span>
                  <strong style={{ fontSize: '1.1rem', color: Number(coverageDaysEst) < 2 ? '#e11d48' : '#0f172a' }}>
                    {coverageDaysEst} days
                  </strong>
                </div>
                <div>
                  <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: '#64748b', fontWeight: 700, display: 'block' }}>
                    Projected After Sale
                  </span>
                  <strong style={{ fontSize: '1.1rem', color: projectedStockAfter < reorderPoint ? '#e11d48' : '#059669' }}>
                    {projectedStockAfter.toFixed(1)} units
                  </strong>
                </div>
              </div>

              <div>
                {projectedStockAfter <= 0 ? (
                  <span className="badge badge-critical" style={{ fontSize: '0.8rem' }}>
                    🚨 CRITICAL (STOCKOUT)
                  </span>
                ) : projectedStockAfter < (selectedProduct.safety_stock || 5) ? (
                  <span className="badge badge-high" style={{ fontSize: '0.8rem' }}>
                    ⚠️ HIGH STOCK RISK
                  </span>
                ) : projectedStockAfter < reorderPoint ? (
                  <span className="badge badge-medium" style={{ fontSize: '0.8rem' }}>
                    ⚠️ BELOW REORDER POINT
                  </span>
                ) : (
                  <span className="badge badge-low" style={{ fontSize: '0.8rem' }}>
                    ✓ SAFE RESERVE
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Modern 2-Column POS Workspace */}
          <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 1.4fr) minmax(260px, 1fr)', gap: '24px', alignItems: 'start' }}>
            {/* Left Column: Product Selection & Pricing */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
              <div className="form-group">
                <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.88rem', color: '#0f172a' }}>Select Catalog Product *</span>
                  <span style={{ fontSize: '0.74rem', color: '#64748b' }}>
                    Quick search across {products.length} catalog items
                  </span>
                </label>
                <ProductCombobox
                  products={products}
                  selectedProductId={formData.product_id}
                  onSelect={handleProductChange}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                <div className="form-group">
                  <label style={{ fontWeight: 700, fontSize: '0.84rem', color: '#334155' }}>Quantity *</label>
                  <input
                    type="number"
                    min="1"
                    step="1"
                    required
                    className="form-control"
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: Number(e.target.value) })}
                    style={{ fontSize: '1.05rem', fontWeight: 700 }}
                  />
                  {selectedProduct && (
                    <span style={{ fontSize: '0.74rem', fontWeight: 600, color: selectedProduct.current_stock < formData.quantity ? '#dc2626' : '#16a34a', marginTop: '4px', display: 'block' }}>
                      Available in stock: {selectedProduct.current_stock}
                    </span>
                  )}
                </div>

                <div className="form-group">
                  <label style={{ fontWeight: 700, fontSize: '0.84rem', color: '#334155' }}>Unit Price (₹) *</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    className="form-control"
                    value={formData.unit_price}
                    onChange={(e) => setFormData({ ...formData, unit_price: Number(e.target.value) })}
                    style={{ fontSize: '1.05rem', fontWeight: 700 }}
                  />
                </div>
              </div>
            </div>

            {/* Right Column: Customer Khata, Date, and Live Bill Summary Card */}
            <div style={{ background: '#f8fafc', border: '1.5px solid #e2e8f0', borderRadius: '16px', padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div className="form-group">
                <label style={{ fontWeight: 700, fontSize: '0.84rem', color: '#334155' }}>Customer (Khata Credit or Walk-in)</label>
                <select
                  className="form-control"
                  value={formData.customer_id || ''}
                  onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
                  style={{ background: '#ffffff', borderRadius: '10px' }}
                >
                  <option value="">👤 Walk-in / Cash Customer</option>
                  {customers.map((c) => (
                    <option key={c.id} value={c.id}>
                      📖 {c.name} {c.phone ? `(${c.phone})` : ''}
                    </option>
                  ))}
                </select>

                {/* Live Khata Credit Status Warning */}
                {formData.customer_id && (() => {
                  const selCust = customers.find((c) => c.id === formData.customer_id);
                  if (!selCust) return null;
                  const isDelinquent = selCust.name.toLowerCase().includes('sharma mess') || selCust.name.toLowerCase().includes('vikram');
                  const isCommercial = selCust.name.toLowerCase().includes('udupi') || selCust.name.toLowerCase().includes('bawarchi');

                  return (
                    <div
                      style={{
                        marginTop: '8px',
                        padding: '10px 12px',
                        borderRadius: '8px',
                        background: isDelinquent ? '#fff1f2' : isCommercial ? '#fffbeb' : '#f0fdf4',
                        border: `1.5px solid ${isDelinquent ? '#fecdd3' : isCommercial ? '#fde68a' : '#bbf7d0'}`,
                      }}
                    >
                      <div
                        style={{
                          fontSize: '11px',
                          fontWeight: 800,
                          color: isDelinquent ? '#e11d48' : isCommercial ? '#b45309' : '#166534',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                        }}
                      >
                        <span>{isDelinquent ? '🚫 Credit Hold Alert' : isCommercial ? '⚠️ B2B Ledger Alert' : '✅ Active Khata Account'}</span>
                      </div>
                      <div style={{ fontSize: '11px', color: '#475569', marginTop: '2px', lineHeight: 1.4 }}>
                        {isDelinquent && 'Overdue balance ₹4,850.00 (68 days overdue). AI Credit Copilot policy: Uncollateralized credit paused. Cash settlement required!'}
                        {isCommercial && 'Commercial hotel account. Balance ₹18,500.00 pending weekly ledger statement reconciliation.'}
                        {!isDelinquent && !isCommercial && 'Account in good credit standing. Eligible for standard 30-day Kirana trade credit.'}
                      </div>
                    </div>
                  );
                })()}
              </div>

              <div className="form-group">
                <label style={{ fontWeight: 700, fontSize: '0.84rem', color: '#334155' }}>Billing Date</label>
                <input
                  type="date"
                  className="form-control"
                  value={formData.date || ''}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  style={{ background: '#ffffff', borderRadius: '10px' }}
                />
              </div>

              {/* Payment Mode Selector */}
              <div className="form-group" style={{ marginBottom: '16px' }}>
                <label style={{ fontWeight: 700, fontSize: '0.84rem', color: '#334155', display: 'flex', justifyContent: 'space-between' }}>
                  <span>Payment Method *</span>
                  <span style={{ fontSize: '11px', color: '#64748b' }}>Select Settlement Mode</span>
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginTop: '6px' }}>
                  {[
                    { id: 'CASH', label: '💵 Cash', desc: 'Instant Cash' },
                    { id: 'UPI', label: '📱 UPI', desc: 'GPay/PhonePe' },
                    { id: 'CREDIT', label: '📖 Khata Credit', desc: 'Store Udhar' },
                  ].map((pm) => (
                    <button
                      key={pm.id}
                      type="button"
                      onClick={() => setPaymentMethod(pm.id as any)}
                      style={{
                        padding: '10px 8px',
                        borderRadius: '10px',
                        border: paymentMethod === pm.id ? '2px solid #e23744' : '1.5px solid #e2e8f0',
                        background: paymentMethod === pm.id ? '#fff1f2' : '#ffffff',
                        color: paymentMethod === pm.id ? '#9f1239' : '#334155',
                        fontWeight: paymentMethod === pm.id ? 800 : 600,
                        cursor: 'pointer',
                        textAlign: 'center',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <div style={{ fontSize: '13px' }}>{pm.label}</div>
                      <div style={{ fontSize: '10px', color: paymentMethod === pm.id ? '#e11d48' : '#94a3b8', marginTop: '2px' }}>{pm.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Credit Block Warning when Credit Mode Selected for Delinquent Customer */}
              {(() => {
                const selCust = customers.find((c) => c.id === formData.customer_id);
                const isDelinquent = selCust && (selCust.name.toLowerCase().includes('sharma mess') || selCust.name.toLowerCase().includes('vikram'));
                if (paymentMethod === 'CREDIT' && isDelinquent) {
                  return (
                    <div style={{ background: '#fef2f2', border: '1.5px solid #f87171', borderRadius: '10px', padding: '12px 14px', marginBottom: '14px' }}>
                      <div style={{ fontWeight: 800, fontSize: '12px', color: '#dc2626', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span>🚫 ACCESS DENIED TO PRODUCT ON CREDIT</span>
                      </div>
                      <div style={{ fontSize: '11px', color: '#991b1b', marginTop: '4px', lineHeight: 1.45 }}>
                        <strong>{selCust.name}</strong> has ₹4,850.00 overdue for 68 days. AI Credit Copilot strictly forbids releasing goods on Credit. 
                        <strong> Switch payment method to 💵 Cash or 📱 UPI to proceed with sale!</strong>
                      </div>
                    </div>
                  );
                }
                if (paymentMethod === 'CREDIT' && !formData.customer_id) {
                  return (
                    <div style={{ background: '#fffbeb', border: '1.5px solid #fcd34d', borderRadius: '10px', padding: '10px 12px', marginBottom: '14px' }}>
                      <div style={{ fontSize: '11px', color: '#92400e', fontWeight: 600 }}>
                        ⚠️ Please select a customer account from dropdown to bill on Khata Credit.
                      </div>
                    </div>
                  );
                }
                if ((paymentMethod === 'CASH' || paymentMethod === 'UPI') && isDelinquent) {
                  return (
                    <div style={{ background: '#f0fdf4', border: '1.5px solid #86efac', borderRadius: '10px', padding: '10px 12px', marginBottom: '14px' }}>
                      <div style={{ fontSize: '11px', color: '#166534', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span>✓ ACCESS GRANTED: Upfront {paymentMethod} settlement bypasses Khata credit hold.</span>
                      </div>
                    </div>
                  );
                }
                return null;
              })()}

              {/* Total Calculation Tile */}
              <div style={{ background: 'linear-gradient(135deg, #ffffff 0%, #fff1f2 100%)', border: '1.5px solid #fecdd3', borderRadius: '12px', padding: '14px 16px', marginTop: '2px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: '#9f1239', fontWeight: 700, letterSpacing: '0.04em' }}>
                    Total Bill Amount
                  </div>
                  <span style={{ fontSize: '11px', fontWeight: 800, padding: '2px 8px', borderRadius: '6px', background: paymentMethod === 'CREDIT' ? '#fef3c7' : '#dcfce7', color: paymentMethod === 'CREDIT' ? '#92400e' : '#15803d' }}>
                    Paid via {paymentMethod}
                  </span>
                </div>
                <div style={{ fontSize: '1.85rem', fontWeight: 900, color: '#e23744', marginTop: '2px' }}>
                  ₹{totalAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </div>
                {selectedProduct && (
                  <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>
                    {formData.quantity} × ₹{Number(formData.unit_price).toFixed(2)} ({selectedProduct.name})
                  </div>
                )}
              </div>

              {(() => {
                const selCust = customers.find((c) => c.id === formData.customer_id);
                const isDelinquent = selCust && (selCust.name.toLowerCase().includes('sharma mess') || selCust.name.toLowerCase().includes('vikram'));
                const isCreditBlocked = (paymentMethod === 'CREDIT' && isDelinquent) || (paymentMethod === 'CREDIT' && !formData.customer_id);

                return (
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={recording || products.length === 0 || isCreditBlocked}
                    style={{
                      width: '100%',
                      padding: '13px',
                      fontSize: '1rem',
                      fontWeight: 800,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '8px',
                      background: isCreditBlocked ? '#94a3b8' : '#e23744',
                      borderColor: isCreditBlocked ? '#64748b' : '#e23744',
                      boxShadow: isCreditBlocked ? 'none' : '0 4px 14px rgba(226, 55, 68, 0.35)',
                      cursor: recording || products.length === 0 || isCreditBlocked ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {recording ? (
                      <span className="spinner"></span>
                    ) : isCreditBlocked ? (
                      '🚫 Product Access Blocked (Credit Hold)'
                    ) : (
                      `💳 Complete & Record Sale (${paymentMethod})`
                    )}
                  </button>
                );
              })()}
            </div>
          </div>
        </form>
      </div>


      {/* Recent Sales History */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Recent Transactions ({sales.length})</h2>
          <button className="btn btn-secondary btn-sm" onClick={loadData} disabled={loading}>
            Refresh
          </button>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Sale ID</th>
                <th>Date</th>
                <th>Product</th>
                <th>Qty</th>
                <th>Unit Price</th>
                <th>Total</th>
                <th>Customer</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: 32 }}>
                    <span className="spinner"></span> Loading transactions...
                  </td>
                </tr>
              ) : sales.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: 32 }}>
                    No sales recorded yet. Use the form above to record your first sale.
                  </td>
                </tr>
              ) : (
                sales.map((sale) => {
                  const prod = products.find((p) => p.id === sale.product_id);
                  const cust = customers.find((c) => c.id === sale.customer_id);

                  return (
                    <tr key={sale.id}>
                      <td style={{ fontFamily: 'JetBrains Mono', color: 'var(--text-muted)' }}>#{sale.id}</td>
                      <td>{sale.date || 'Today'}</td>
                      <td>
                        <Link to={`/products/${sale.product_id}`} style={{ color: '#60a5fa', textDecoration: 'none', fontWeight: 600 }}>
                          {prod ? prod.name : sale.product_id.slice(0, 8)}
                        </Link>
                      </td>
                      <td><strong>{sale.quantity}</strong></td>
                      <td>₹{sale.unit_price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                      <td><strong style={{ color: '#10b981' }}>₹{sale.total_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong></td>
                      <td>
                        {sale.customer_id ? (
                          <Link to={`/customers/${sale.customer_id}`} style={{ color: '#93c5fd', textDecoration: 'none' }}>
                            {cust ? cust.name : sale.customer_id.slice(0, 8)}
                          </Link>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>Walk-in</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
