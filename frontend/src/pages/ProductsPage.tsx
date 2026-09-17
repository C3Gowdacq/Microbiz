import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProducts, createProduct, Product, ProductCreate } from '../api';

export const ProductsPage: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [search, setSearch] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState<boolean>(false);

  const [formData, setFormData] = useState<ProductCreate>({
    sku: '',
    name: '',
    selling_price: 0,
    cost_price: 0,
    current_stock: 0,
    reorder_level: 10,
    safety_stock: 5,
    lead_time_days: 3,
    store_type: 'a',
    assortment: 'a',
    competition_distance: 1000,
    promo_active: false,
    promo2: false,
    school_holiday: false,
  });

  const navigate = useNavigate();

  const loadProducts = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getProducts();
      setProducts(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to fetch products');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setCreating(true);
      setError(null);
      await createProduct({
        ...formData,
        selling_price: Number(formData.selling_price),
        cost_price: Number(formData.cost_price),
        current_stock: Number(formData.current_stock),
        reorder_level: Number(formData.reorder_level),
        safety_stock: Number(formData.safety_stock),
        lead_time_days: Number(formData.lead_time_days),
        competition_distance: formData.competition_distance ? Number(formData.competition_distance) : undefined,
      });
      setShowAddModal(false);
      setFormData({
        sku: '',
        name: '',
        selling_price: 0,
        cost_price: 0,
        current_stock: 0,
        reorder_level: 10,
        safety_stock: 5,
        lead_time_days: 3,
        store_type: 'a',
        assortment: 'a',
        competition_distance: 1000,
        promo_active: false,
        promo2: false,
        school_holiday: false,
      });
      await loadProducts();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to create product');
    } finally {
      setCreating(false);
    }
  };

  const filtered = products.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.sku.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Products & Inventory</h1>
          <p className="page-subtitle">Track stock levels, configure pricing, and inspect stockout risks</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-primary" onClick={() => setShowAddModal(true)}>
            ➕ Add Product
          </button>
        </div>
      </div>

      {error && <div className="error-banner">⚠️ {error}</div>}

      <div style={{ marginBottom: 20, display: 'flex', gap: 12 }}>
        <input
          type="text"
          className="form-control"
          placeholder="🔍 Search product by SKU or name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ maxWidth: 400 }}
        />
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>SKU</th>
              <th>Product Name</th>
              <th>Current Stock</th>
              <th>Reorder Point</th>
              <th>Stock Status</th>
              <th>ML Model Status</th>
              <th>Selling Price</th>
              <th>Cost Price</th>
              <th>Margin</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={10} style={{ textAlign: 'center', padding: 32 }}>
                  <span className="spinner"></span> Loading products...
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={10} style={{ textAlign: 'center', padding: 32 }}>
                  No products found. Click "Add Product" to create one.
                </td>
              </tr>
            ) : (
              filtered.map((product) => {
                const isLowStock = product.current_stock < product.reorder_level;
                const margin =
                  product.selling_price > 0
                    ? ((product.selling_price - product.cost_price) / product.selling_price) * 100
                    : 0;

                return (
                  <tr key={product.id} onClick={() => navigate(`/products/${product.id}`)}>
                    <td>
                      <span style={{ fontFamily: 'JetBrains Mono', fontWeight: 600, color: '#94a3b8' }}>
                        {product.sku}
                      </span>
                    </td>
                    <td>
                      <strong>{product.name}</strong>
                    </td>
                    <td>
                      <span
                        style={{
                          fontWeight: 700,
                          fontSize: '1rem',
                          color: isLowStock ? '#f87171' : '#f8fafc',
                        }}
                      >
                        {product.current_stock}
                      </span>
                    </td>
                    <td>{product.reorder_level}</td>
                    <td>
                      {isLowStock ? (
                        <span className="badge badge-high">⚠️ Low Stock</span>
                      ) : (
                        <span className="badge badge-low">✓ In Stock</span>
                      )}
                    </td>
                    <td>
                      {product.ml_ready ? (
                        <span className="badge badge-low" title="Trained RF Model Ready (StoreType + Assortment configured)">
                          ⚡ RF Model Ready
                        </span>
                      ) : (
                        <span className="badge badge-medium" style={{ background: '#334155', color: '#94a3b8' }} title="Missing store type or assortment; will use sales velocity baseline">
                          ○ Baseline Only
                        </span>
                      )}
                    </td>
                    <td>₹{product.selling_price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                    <td>₹{product.cost_price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                    <td>
                      <span style={{ color: margin < 0 ? '#ef4444' : margin < 15 ? '#f59e0b' : '#10b981' }}>
                        {margin.toFixed(1)}%
                      </span>
                    </td>
                    <td>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/products/${product.id}`);
                        }}
                      >
                        Details →
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Add Product Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">➕ Add New Product</h2>
              <button className="modal-close" onClick={() => setShowAddModal(false)}>
                ×
              </button>
            </div>

            <form onSubmit={handleCreate}>
              <div className="form-grid">
                <div className="form-group">
                  <label>SKU *</label>
                  <input
                    type="text"
                    required
                    className="form-control"
                    placeholder="e.g. ELEC-001"
                    value={formData.sku}
                    onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label>Product Name *</label>
                  <input
                    type="text"
                    required
                    className="form-control"
                    placeholder="e.g. Wireless Headphones"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label>Selling Price (₹) *</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    className="form-control"
                    value={formData.selling_price}
                    onChange={(e) => setFormData({ ...formData, selling_price: Number(e.target.value) })}
                  />
                </div>

                <div className="form-group">
                  <label>Cost Price (₹) *</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    className="form-control"
                    value={formData.cost_price}
                    onChange={(e) => setFormData({ ...formData, cost_price: Number(e.target.value) })}
                  />
                </div>

                <div className="form-group">
                  <label>Initial Stock (Units) *</label>
                  <input
                    type="number"
                    step="1"
                    required
                    className="form-control"
                    value={formData.current_stock}
                    onChange={(e) => setFormData({ ...formData, current_stock: Number(e.target.value) })}
                  />
                </div>

                <div className="form-group">
                  <label>Reorder Level *</label>
                  <input
                    type="number"
                    step="1"
                    required
                    className="form-control"
                    value={formData.reorder_level}
                    onChange={(e) => setFormData({ ...formData, reorder_level: Number(e.target.value) })}
                  />
                </div>

                <div className="form-group">
                  <label>Safety Stock</label>
                  <input
                    type="number"
                    step="1"
                    className="form-control"
                    value={formData.safety_stock}
                    onChange={(e) => setFormData({ ...formData, safety_stock: Number(e.target.value) })}
                  />
                </div>

                <div className="form-group">
                  <label>Supplier Lead Time (Days)</label>
                  <input
                    type="number"
                    step="1"
                    className="form-control"
                    value={formData.lead_time_days}
                    onChange={(e) => setFormData({ ...formData, lead_time_days: Number(e.target.value) })}
                  />
                </div>
              </div>

              {/* ML Store Profile Group */}
              <div style={{ marginTop: 24, padding: 16, background: 'rgba(59, 130, 246, 0.05)', borderRadius: 8, border: '1px solid rgba(59, 130, 246, 0.2)' }}>
                <h4 style={{ margin: '0 0 12px 0', fontSize: '0.95rem', color: '#60a5fa', display: 'flex', alignItems: 'center', gap: 6 }}>
                  🤖 ML Model Profile (Rossmann RF Feature Mapping)
                </h4>
                <p style={{ margin: '0 0 16px 0', fontSize: '0.8rem', color: '#94a3b8' }}>
                  Features expected by the trained Random Forest model for store-level uplift & demand allocation:
                </p>

                <div className="form-grid">
                  <div className="form-group">
                    <label>Store Type *</label>
                    <select
                      className="form-control"
                      value={formData.store_type || 'a'}
                      onChange={(e) => setFormData({ ...formData, store_type: e.target.value })}
                    >
                      <option value="a">Type A (Standard Retail)</option>
                      <option value="b">Type B (Superstore)</option>
                      <option value="c">Type C (Express / Convenience)</option>
                      <option value="d">Type D (Extended Assortment)</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Assortment Level *</label>
                    <select
                      className="form-control"
                      value={formData.assortment || 'a'}
                      onChange={(e) => setFormData({ ...formData, assortment: e.target.value })}
                    >
                      <option value="a">Assortment A (Basic essentials)</option>
                      <option value="b">Assortment B (Extra variety)</option>
                      <option value="c">Assortment C (Extended full catalog)</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Competition Distance (Meters)</label>
                    <input
                      type="number"
                      step="10"
                      className="form-control"
                      placeholder="e.g. 500"
                      value={formData.competition_distance || ''}
                      onChange={(e) => setFormData({ ...formData, competition_distance: Number(e.target.value) })}
                    />
                  </div>

                  <div className="form-group" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', marginTop: 16 }}>
                      <input
                        type="checkbox"
                        checked={formData.promo_active || false}
                        onChange={(e) => setFormData({ ...formData, promo_active: e.target.checked })}
                      />
                      <span>Active Promotion Running (Promo)</span>
                    </label>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', marginTop: 8 }}>
                      <input
                        type="checkbox"
                        checked={formData.school_holiday || false}
                        onChange={(e) => setFormData({ ...formData, school_holiday: e.target.checked })}
                      />
                      <span>School Holiday Active</span>
                    </label>
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 20 }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowAddModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={creating}>
                  {creating ? 'Creating...' : 'Save Product'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
