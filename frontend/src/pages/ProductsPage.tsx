import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProducts, createProduct, adjustProductStock, Product, ProductCreate } from '../api';

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

  const fillSampleProduct = () => {
    const randNum = Math.floor(100 + Math.random() * 900);
    setFormData({
      sku: `OIL-MUSTARD-${randNum}`,
      name: `Pure Mustard Kachi Ghani Oil 5L (${randNum})`,
      selling_price: 850,
      cost_price: 720,
      current_stock: 8,
      reorder_level: 20,
      safety_stock: 6,
      lead_time_days: 3,
      store_type: 'a',
      assortment: 'c',
      competition_distance: 500,
      promo_active: true,
      promo2: false,
      school_holiday: false,
    });
  };

  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [restockProduct, setRestockProduct] = useState<Product | null>(null);
  const [addQty, setAddQty] = useState<number>(10);
  const [restocking, setRestocking] = useState<boolean>(false);

  const handleRestockSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!restockProduct) return;
    try {
      setRestocking(true);
      setError(null);
      const newTotal = Number(restockProduct.current_stock) + Number(addQty);
      await adjustProductStock(restockProduct.id, newTotal);
      setRestockProduct(null);
      await loadProducts();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to update stock');
    } finally {
      setRestocking(false);
    }
  };

  const getCategoryAndIcon = (name: string) => {
    const n = name.toLowerCase();
    if (n.includes('rice') || n.includes('atta') || n.includes('flour') || n.includes('dal')) {
      return { category: 'grains', label: '🌾 Grains & Flours', icon: '🌾' };
    }
    if (n.includes('tea') || n.includes('salt') || n.includes('sugar') || n.includes('turmeric')) {
      return { category: 'pantry', label: '🫖 Tea & Spices', icon: '🫖' };
    }
    if (n.includes('milk') || n.includes('dairy')) {
      return { category: 'dairy', label: '🥛 Dairy', icon: '🥛' };
    }
    if (n.includes('oil') || n.includes('ghee')) {
      return { category: 'oils', label: '🥫 Cooking Oils', icon: '🥫' };
    }
    if (n.includes('soap') || n.includes('detergent') || n.includes('toothpaste')) {
      return { category: 'hygiene', label: '🧼 Household', icon: '🧼' };
    }
    if (n.includes('onion') || n.includes('potato')) {
      return { category: 'produce', label: '🥔 Farm Fresh', icon: '🥔' };
    }
    if (n.includes('noodles')) {
      return { category: 'snacks', label: '🍜 Instant Snacks', icon: '🍜' };
    }
    return { category: 'other', label: '📦 General Grocery', icon: '📦' };
  };

  const categories = [
    { id: 'all', label: '✨ All Products' },
    { id: 'grains', label: '🌾 Grains & Pulses' },
    { id: 'oils', label: '🥫 Cooking Oils' },
    { id: 'pantry', label: '🫖 Tea & Spices' },
    { id: 'dairy', label: '🥛 Fresh Dairy' },
    { id: 'hygiene', label: '🧼 Household & Care' },
    { id: 'produce', label: '🥔 Farm Fresh' },
  ];

  const filtered = products.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.sku.toLowerCase().includes(search.toLowerCase());
    const info = getCategoryAndIcon(p.name);
    const matchesCategory = selectedCategory === 'all' || info.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Grocery Catalog & Inventory</h1>
          <p className="page-subtitle">Zomato-grade merchant stock manager with AI demand intelligence</p>
        </div>
        <div className="header-actions">
          <div style={{ display: 'flex', gap: 6, background: '#ffffff', padding: 4, borderRadius: 12, border: '1px solid #edeef2' }}>
            <button
              className={`btn btn-sm ${viewMode === 'grid' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setViewMode('grid')}
            >
              🎴 Catalog Cards
            </button>
            <button
              className={`btn btn-sm ${viewMode === 'table' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setViewMode('table')}
            >
              📋 Table View
            </button>
          </div>

          <button className="btn btn-primary" onClick={() => setShowAddModal(true)}>
            ➕ Add Product
          </button>
        </div>
      </div>

      {error && <div className="error-banner">⚠️ {error}</div>}

      {/* Zomato-Style Category Chips */}
      <div className="filter-category-bar">
        {categories.map((cat) => (
          <button
            key={cat.id}
            className={`category-chip ${selectedCategory === cat.id ? 'active' : ''}`}
            onClick={() => setSelectedCategory(cat.id)}
          >
            {cat.label}
          </button>
        ))}
      </div>

      <div style={{ marginBottom: 20, display: 'flex', gap: 12, alignItems: 'center' }}>
        <input
          type="text"
          className="form-control"
          placeholder="🔍 Search groceries, pulses, oil, spices, or SKU..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ maxWidth: 450 }}
        />
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600 }}>
          Showing {filtered.length} items
        </span>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <span className="spinner"></span>
          <div style={{ marginTop: 12, fontWeight: 600, color: 'var(--text-muted)' }}>
            Loading store inventory...
          </div>
        </div>
      ) : filtered.length === 0 ? (
        <div style={{ background: '#ffffff', borderRadius: 20, padding: 48, textAlign: 'center', border: '1px solid #edeef2' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: 12 }}>🔍</div>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: 6 }}>No items found</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Try selecting a different category or click "Add Product" to create one.
          </p>
        </div>
      ) : viewMode === 'grid' ? (
        /* Zomato-Style Product Catalog Grid */
        <div className="product-catalog-grid">
          {filtered.map((product) => {
            const isLowStock = product.current_stock < product.reorder_level;
            const margin =
              product.selling_price > 0
                ? ((product.selling_price - product.cost_price) / product.selling_price) * 100
                : 0;
            const { category, icon } = getCategoryAndIcon(product.name);

            return (
              <div
                key={product.id}
                className="product-card"
                onClick={() => navigate(`/products/${product.id}`)}
              >
                <div className="product-card-top">
                  <span className="product-category-chip">{category}</span>
                  {isLowStock ? (
                    <span className="badge badge-high">⚠️ Reorder Needed</span>
                  ) : (
                    <span className="badge badge-low">✓ In Stock</span>
                  )}
                </div>

                <div className="product-icon-box">{icon}</div>

                <h3 className="product-title">{product.name}</h3>
                <div className="product-sku-tag">{product.sku}</div>

                <div className="product-pricing-row">
                  <div className="product-price-bold">
                    ₹{product.selling_price.toLocaleString('en-IN', { minimumFractionDigits: 0 })}
                  </div>
                  <div className="product-cost-sub">
                    Cost: ₹{product.cost_price.toLocaleString('en-IN', { minimumFractionDigits: 0 })}
                  </div>
                  <span
                    className="product-margin-pill"
                    style={{
                      backgroundColor: margin < 0 ? '#fee2e2' : margin < 15 ? '#fef3c7' : '#ecfdf5',
                      color: margin < 0 ? '#dc2626' : margin < 15 ? '#d97706' : '#059669',
                      borderColor: margin < 0 ? '#fca5a5' : margin < 15 ? '#fde68a' : '#a7f3d0',
                    }}
                  >
                    {margin.toFixed(0)}% Margin
                  </span>
                </div>

                <div className="product-stock-bar">
                  <div className={`stock-indicator ${isLowStock ? 'low' : 'ok'}`}>
                    Stock: <strong>{product.current_stock} units</strong>
                    <div style={{ display: 'flex', gap: 8, fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>
                      <span>ROP: {product.reorder_level}</span>
                      <span>•</span>
                      <span>Coverage: ~{(product.current_stock / Math.max(1, (product.reorder_level / (product.lead_time_days || 3)))).toFixed(1)}d</span>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: 6 }}>
                    <button
                      className="btn btn-secondary btn-sm"
                      style={{ borderColor: '#fca5a5', color: '#e23744', fontWeight: 700 }}
                      onClick={(e) => {
                        e.stopPropagation();
                        setRestockProduct(product);
                        setAddQty(10);
                      }}
                      title="Quickly record incoming supplier delivery"
                    >
                      + Add Stock
                    </button>
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/forecasting?product=${product.id}`);
                      }}
                    >
                      🔮 Forecast
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* Table View */
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Product Name</th>
                <th>Current Stock</th>
                <th>Reorder Point</th>
                <th>Coverage (est.)</th>
                <th>Risk Status</th>
                <th>Rec. Order</th>
                <th>Selling Price</th>
                <th>Margin</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((product) => {
                const isLowStock = product.current_stock < product.reorder_level;
                const margin =
                  product.selling_price > 0
                    ? ((product.selling_price - product.cost_price) / product.selling_price) * 100
                    : 0;
                const { icon } = getCategoryAndIcon(product.name);
                const dailyBurn = Math.max(0.5, product.reorder_level / (product.lead_time_days || 3));
                const coverageDays = (product.current_stock / dailyBurn).toFixed(1);
                const recOrderQty = Math.max(0, Math.ceil(product.reorder_level * 1.5 - product.current_stock));

                let riskLevel = 'HEALTHY';
                let riskBadgeClass = 'badge-low';
                if (product.current_stock <= 0) {
                  riskLevel = 'CRITICAL';
                  riskBadgeClass = 'badge-high';
                } else if (product.current_stock < (product.safety_stock || 5)) {
                  riskLevel = 'HIGH RISK';
                  riskBadgeClass = 'badge-high';
                } else if (product.current_stock < product.reorder_level) {
                  riskLevel = 'REORDER';
                  riskBadgeClass = 'badge-medium';
                }

                return (
                  <tr key={product.id} onClick={() => navigate(`/products/${product.id}`)}>
                    <td>
                      <span style={{ fontFamily: 'JetBrains Mono', fontWeight: 600, color: 'var(--text-muted)' }}>
                        {product.sku}
                      </span>
                    </td>
                    <td>
                      <span style={{ marginRight: 8 }}>{icon}</span>
                      <strong>{product.name}</strong>
                    </td>
                    <td>
                      <span
                        style={{
                          fontWeight: 700,
                          fontSize: '1rem',
                          color: isLowStock ? '#e11d48' : '#16a34a',
                        }}
                      >
                        {product.current_stock}
                      </span>
                    </td>
                    <td>{product.reorder_level}</td>
                    <td>
                      <span style={{ fontWeight: 600, color: Number(coverageDays) < 3 ? '#e11d48' : '#cbd5e1' }}>
                        {coverageDays}d
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${riskBadgeClass}`}>
                        {riskLevel}
                      </span>
                    </td>
                    <td>
                      {recOrderQty > 0 ? (
                        <span style={{ color: '#60a5fa', fontWeight: 700 }}>
                          +{recOrderQty} units
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>—</span>
                      )}
                    </td>
                    <td>₹{product.selling_price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                    <td>
                      <span style={{ fontWeight: 700, color: margin < 0 ? '#dc2626' : margin < 15 ? '#d97706' : '#16a34a' }}>
                        {margin.toFixed(1)}%
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <button
                          className="btn btn-secondary btn-sm"
                          style={{ borderColor: '#fca5a5', color: '#e23744', fontWeight: 700 }}
                          onClick={(e) => {
                            e.stopPropagation();
                            setRestockProduct(product);
                            setAddQty(10);
                          }}
                        >
                          + Add Stock
                        </button>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/products/${product.id}`);
                          }}
                        >
                          Details →
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Add Product Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">➕ Add New Product</h2>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <button
                  type="button"
                  className="btn btn-sm btn-secondary"
                  onClick={fillSampleProduct}
                  style={{ background: '#fef3c7', color: '#b45309', border: '1px solid #fde68a', fontWeight: 600 }}
                  title="Auto-fill sample product with realistic retail inventory & ML parameters"
                >
                  ✨ Auto-Fill Sample Data
                </button>
                <button className="modal-close" onClick={() => setShowAddModal(false)}>
                  ×
                </button>
              </div>
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

      {/* Quick Restock Delivery Modal */}
      {restockProduct && (
        <div className="modal-overlay" onClick={() => setRestockProduct(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 460 }}>
            <div className="modal-header">
              <h2 className="modal-title">📦 Add Stock / Restock</h2>
              <button className="modal-close" onClick={() => setRestockProduct(null)}>
                ×
              </button>
            </div>

            <form onSubmit={handleRestockSubmit}>
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: 4 }}>
                  {restockProduct.name}
                </div>
                <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                  SKU: {restockProduct.sku} • Reorder Threshold: {restockProduct.reorder_level} units
                </div>
              </div>

              <div style={{ background: '#f8f9fc', borderRadius: 14, padding: 16, marginBottom: 18, border: '1px solid #edeef2' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontSize: '0.9rem' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Current On-Hand Stock:</span>
                  <strong>{restockProduct.current_stock} units</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.95rem' }}>
                  <span style={{ color: '#e23744', fontWeight: 600 }}>New Total After Restock:</span>
                  <strong style={{ color: '#16a34a', fontSize: '1.1rem' }}>
                    {Number(restockProduct.current_stock) + Number(addQty || 0)} units
                  </strong>
                </div>
              </div>

              <div className="form-group">
                <label>Delivered Quantity to Add (+ Units) *</label>
                <input
                  type="number"
                  className="form-control"
                  value={addQty}
                  onChange={(e) => setAddQty(Number(e.target.value))}
                  min={1}
                  required
                  autoFocus
                />
              </div>

              <div style={{ display: 'flex', gap: 10, marginTop: 22, justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setRestockProduct(null)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={restocking || addQty <= 0}
                >
                  {restocking ? 'Updating Stock...' : '✓ Confirm & Restock'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
