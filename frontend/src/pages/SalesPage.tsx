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
} from '../api';

export const SalesPage: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [sales, setSales] = useState<Sale[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [recording, setRecording] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const [formData, setFormData] = useState<SaleCreate>({
    product_id: '',
    customer_id: '',
    quantity: 1,
    unit_price: 0,
    date: new Date().toISOString().split('T')[0],
  });

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

      setSuccessMsg(`✅ Recorded Sale #${sale.id} for €${sale.total_amount.toFixed(2)} (Stock automatically decremented).`);
      setFormData((prev) => ({ ...prev, quantity: 1 }));
      await loadData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to record sale');
    } finally {
      setRecording(false);
    }
  };

  const selectedProduct = products.find((p) => p.id === formData.product_id);
  const totalAmount = Number(formData.quantity || 0) * Number(formData.unit_price || 0);

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
        <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10b981', color: '#a7f3d0', padding: 14, borderRadius: 10, marginBottom: 20 }}>
          {successMsg}
        </div>
      )}

      {/* Sale Entry Card */}
      <div className="card">
        <h2 className="card-title" style={{ marginBottom: 18 }}>🛒 Record POS Sale</h2>

        <form onSubmit={handleSubmit}>
          <div className="form-grid">
            <div className="form-group">
              <label>Select Product *</label>
              <select
                className="form-control"
                value={formData.product_id}
                onChange={(e) => handleProductChange(e.target.value)}
                required
              >
                <option value="" disabled>-- Select a Product --</option>
                {products.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.sku}) — Stock: {p.current_stock} — ₹{p.selling_price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Quantity *</label>
              <input
                type="number"
                min="1"
                step="1"
                required
                className="form-control"
                value={formData.quantity}
                onChange={(e) => setFormData({ ...formData, quantity: Number(e.target.value) })}
              />
              {selectedProduct && (
                <span style={{ fontSize: '0.75rem', color: selectedProduct.current_stock < formData.quantity ? '#ef4444' : 'var(--text-muted)' }}>
                  Available in stock: {selectedProduct.current_stock}
                </span>
              )}
            </div>

            <div className="form-group">
              <label>Unit Price (₹) *</label>
              <input
                type="number"
                step="0.01"
                required
                className="form-control"
                value={formData.unit_price}
                onChange={(e) => setFormData({ ...formData, unit_price: Number(e.target.value) })}
              />
            </div>

            <div className="form-group">
              <label>Customer (Optional)</label>
              <select
                className="form-control"
                value={formData.customer_id || ''}
                onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
              >
                <option value="">-- Walk-in / Anonymous Customer --</option>
                {customers.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} {c.email ? `(${c.email})` : ''}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Sale Date</label>
              <input
                type="date"
                className="form-control"
                value={formData.date || ''}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
              />
            </div>

            <div className="form-group" style={{ justifyContent: 'center' }}>
              <label>Total Bill Amount</label>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#38bdf8' }}>
                ₹{totalAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={recording || products.length === 0}
            style={{ width: '100%', marginTop: 8 }}
          >
            {recording ? <span className="spinner"></span> : '💳 Complete & Record Sale'}
          </button>
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
