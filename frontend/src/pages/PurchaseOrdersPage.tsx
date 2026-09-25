import React, { useEffect, useState } from 'react';
import {
  getPurchaseOrders,
  createPurchaseOrder,
  updatePurchaseOrderStatus,
  receivePurchaseOrder,
  getSuppliers,
  getProducts,
  PurchaseOrder,
  Supplier,
  Product,
  PurchaseOrderItemCreate,
} from '../api';

export const PurchaseOrdersPage: React.FC = () => {
  const [pos, setPos] = useState<PurchaseOrder[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // New PO Modal state
  const [showModal, setShowModal] = useState<boolean>(false);
  const [selectedSupplierId, setSelectedSupplierId] = useState<number | undefined>(undefined);
  const [priority, setPriority] = useState<string>('medium');
  const [reason, setReason] = useState<string>('');
  const [items, setItems] = useState<PurchaseOrderItemCreate[]>([
    { product_id: '', quantity: 10, unit_cost: 0 },
  ]);
  const [submitting, setSubmitting] = useState<boolean>(false);

  // Selected PO details modal
  const [activePo, setActivePo] = useState<PurchaseOrder | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [poData, supData, prodData] = await Promise.all([
        getPurchaseOrders(statusFilter === 'ALL' ? undefined : statusFilter),
        getSuppliers(),
        getProducts(),
      ]);
      setPos(poData);
      setSuppliers(supData);
      setProducts(prodData);
      if (supData.length > 0 && !selectedSupplierId) {
        setSelectedSupplierId(supData[0].id);
      }
      if (prodData.length > 0 && items[0].product_id === '') {
        setItems([{ product_id: prodData[0].id, quantity: 10, unit_cost: prodData[0].cost_price || 0 }]);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load purchase orders');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [statusFilter]);

  const handleCreatePo = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      setError(null);
      const validItems = items.filter((i) => i.product_id && i.quantity > 0);
      if (validItems.length === 0) {
        setError('Please add at least one valid product item');
        setSubmitting(false);
        return;
      }

      await createPurchaseOrder({
        supplier_id: selectedSupplierId,
        priority,
        reason: reason || 'Merchant stock replenishment',
        items: validItems,
      });

      setSuccessMsg('Purchase order created successfully!');
      setShowModal(false);
      fetchData();
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create purchase order');
    } finally {
      setSubmitting(false);
    }
  };

  const handleStatusChange = async (poId: number, newStatus: string) => {
    try {
      setError(null);
      await updatePurchaseOrderStatus(poId, newStatus);
      setSuccessMsg(`PO #${poId} status updated to ${newStatus}`);
      fetchData();
      if (activePo && activePo.id === poId) {
        setActivePo(null);
      }
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update PO status');
    }
  };

  const handleReceive = async (poId: number) => {
    try {
      setError(null);
      await receivePurchaseOrder(poId);
      setSuccessMsg(`PO #${poId} received! Stock automatically incremented and audited.`);
      fetchData();
      if (activePo && activePo.id === poId) {
        setActivePo(null);
      }
      setTimeout(() => setSuccessMsg(null), 5000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to receive purchase order');
    }
  };

  const addItemRow = () => {
    const defaultProd = products[0];
    setItems([
      ...items,
      { product_id: defaultProd?.id || '', quantity: 10, unit_cost: defaultProd?.cost_price || 0 },
    ]);
  };

  const fillSamplePo = () => {
    if (suppliers.length > 0) setSelectedSupplierId(suppliers[0].id);
    setPriority('high');
    setReason('Automated restock for fast-depleting grocery lines');
    if (products.length > 0) {
      const lineItems = products.slice(0, 2).map((p) => ({
        product_id: p.id,
        quantity: 20,
        unit_cost: p.cost_price,
      }));
      setItems(lineItems);
    }
  };

  const removeItemRow = (index: number) => {
    if (items.length > 1) {
      setItems(items.filter((_, i) => i !== index));
    }
  };

  const updateItem = (index: number, field: keyof PurchaseOrderItemCreate, val: any) => {
    const updated = [...items];
    if (field === 'product_id') {
      const p = products.find((prod) => prod.id === val);
      updated[index] = {
        ...updated[index],
        product_id: val,
        unit_cost: p?.cost_price || 0,
      };
    } else {
      updated[index] = { ...updated[index], [field]: val };
    }
    setItems(updated);
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'RECEIVED':
        return 'badge badge-success';
      case 'ORDERED':
        return 'badge badge-info';
      case 'APPROVED':
        return 'badge badge-primary';
      case 'PENDING_APPROVAL':
        return 'badge badge-warning';
      case 'REJECTED':
      case 'CANCELLED':
        return 'badge badge-danger';
      default:
        return 'badge badge-secondary';
    }
  };

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title">Purchase Orders & Replenishment</h1>
          <p className="page-subtitle">Manage procurement lifecycle from AI replenishment alerts to warehouse stock receipt</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          + Create Purchase Order
        </button>
      </div>

      {successMsg && (
        <div className="alert alert-success" style={{ margin: '16px 0', padding: '12px 16px', background: '#e6f4ea', color: '#137333', borderRadius: '8px', border: '1px solid #ceead6' }}>
          ✓ {successMsg}
        </div>
      )}

      {error && (
        <div className="alert alert-danger" style={{ margin: '16px 0', padding: '12px 16px', background: '#fce8e6', color: '#c5221f', borderRadius: '8px', border: '1px solid #fad2cf' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Filter Tabs */}
      <div className="filter-bar" style={{ display: 'flex', gap: '8px', margin: '20px 0', flexWrap: 'wrap' }}>
        {['ALL', 'PENDING_APPROVAL', 'APPROVED', 'ORDERED', 'RECEIVED', 'CANCELLED'].map((st) => (
          <button
            key={st}
            className={`btn btn-sm ${statusFilter === st ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setStatusFilter(st)}
            style={{ textTransform: 'capitalize' }}
          >
            {st.replace('_', ' ').toLowerCase()}
          </button>
        ))}
      </div>

      {/* Purchase Orders Table */}
      <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>Loading purchase orders...</div>
        ) : pos.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
            <p style={{ fontSize: '18px', marginBottom: '8px' }}>📦 No purchase orders found.</p>
            <p style={{ fontSize: '14px', color: '#888' }}>
              Create a purchase order manually or approve pending AI recommendations.
            </p>
          </div>
        ) : (
          <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#f8f9fa', borderBottom: '1px solid #eee', textAlign: 'left' }}>
                <th style={{ padding: '14px 16px' }}>PO Number</th>
                <th style={{ padding: '14px 16px' }}>Supplier</th>
                <th style={{ padding: '14px 16px' }}>Items</th>
                <th style={{ padding: '14px 16px' }}>Total Amount</th>
                <th style={{ padding: '14px 16px' }}>Status</th>
                <th style={{ padding: '14px 16px' }}>Date</th>
                <th style={{ padding: '14px 16px', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {pos.map((po) => (
                <tr key={po.id} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '14px 16px', fontWeight: 600 }}>
                    <a
                      href="#"
                      onClick={(e) => {
                        e.preventDefault();
                        setActivePo(po);
                      }}
                      style={{ color: '#e23744', textDecoration: 'none' }}
                    >
                      {po.po_number}
                    </a>
                  </td>
                  <td style={{ padding: '14px 16px' }}>{po.supplier_name || 'General Wholesale'}</td>
                  <td style={{ padding: '14px 16px' }}>
                    {po.items.length} {po.items.length === 1 ? 'item' : 'items'}
                    <span style={{ fontSize: '12px', color: '#666', display: 'block' }}>
                      {po.items[0]?.product_name || 'Product'} {po.items.length > 1 ? `+${po.items.length - 1} more` : ''}
                    </span>
                  </td>
                  <td style={{ padding: '14px 16px', fontWeight: 600 }}>₹{po.total_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                  <td style={{ padding: '14px 16px' }}>
                    <span className={getStatusBadgeClass(po.status)} style={{ padding: '4px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 600 }}>
                      {po.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td style={{ padding: '14px 16px', fontSize: '13px', color: '#666' }}>
                    {new Date(po.created_at).toLocaleDateString('en-IN')}
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: '6px' }}>
                      {po.status === 'PENDING_APPROVAL' && (
                        <button
                          className="btn btn-sm btn-primary"
                          onClick={() => handleStatusChange(po.id, 'APPROVED')}
                        >
                          Approve
                        </button>
                      )}
                      {po.status === 'APPROVED' && (
                        <button
                          className="btn btn-sm btn-outline"
                          onClick={() => handleStatusChange(po.id, 'ORDERED')}
                        >
                          Mark Ordered
                        </button>
                      )}
                      {(po.status === 'ORDERED' || po.status === 'APPROVED') && (
                        <button
                          className="btn btn-sm btn-success"
                          style={{ background: '#0f9d58', color: '#fff', border: 'none' }}
                          onClick={() => handleReceive(po.id)}
                        >
                          Receive Stock
                        </button>
                      )}
                      <button
                        className="btn btn-sm btn-outline"
                        onClick={() => setActivePo(po)}
                      >
                        View
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* PO Detail View Modal */}
      {activePo && (
        <div className="modal-overlay" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div className="modal-card" style={{ background: '#fff', borderRadius: '12px', width: '90%', maxWidth: '650px', padding: '24px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #eee', paddingBottom: '12px' }}>
              <div>
                <h3 style={{ margin: 0 }}>{activePo.po_number}</h3>
                <span className={getStatusBadgeClass(activePo.status)} style={{ marginTop: '4px', display: 'inline-block' }}>
                  {activePo.status}
                </span>
              </div>
              <button className="btn btn-sm btn-outline" onClick={() => setActivePo(null)}>✕</button>
            </div>

            <div style={{ margin: '16px 0', fontSize: '14px', lineHeight: 1.6 }}>
              <p><strong>Supplier:</strong> {activePo.supplier_name || 'General Supplier'}</p>
              <p><strong>Reason:</strong> {activePo.reason || 'Replenishment'}</p>
              {activePo.notes && <p><strong>Notes:</strong> {activePo.notes}</p>}
              <p><strong>Created:</strong> {new Date(activePo.created_at).toLocaleString()}</p>
              {activePo.received_at && <p><strong>Received At:</strong> {new Date(activePo.received_at).toLocaleString()}</p>}
            </div>

            <h4>Line Items</h4>
            <table style={{ width: '100%', borderCollapse: 'collapse', margin: '12px 0' }}>
              <thead>
                <tr style={{ background: '#f8f9fa', borderBottom: '1px solid #eee', textAlign: 'left' }}>
                  <th style={{ padding: '8px' }}>Product</th>
                  <th style={{ padding: '8px' }}>Qty</th>
                  <th style={{ padding: '8px' }}>Cost</th>
                  <th style={{ padding: '8px', textAlign: 'right' }}>Total</th>
                </tr>
              </thead>
              <tbody>
                {activePo.items.map((item) => (
                  <tr key={item.id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                    <td style={{ padding: '8px' }}>{item.product_name || item.product_id}</td>
                    <td style={{ padding: '8px' }}>{item.quantity}</td>
                    <td style={{ padding: '8px' }}>₹{item.unit_cost}</td>
                    <td style={{ padding: '8px', textAlign: 'right' }}>₹{item.total_cost}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div style={{ textAlign: 'right', fontWeight: 700, fontSize: '16px', margin: '12px 0' }}>
              Total Order Amount: ₹{activePo.total_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '16px' }}>
              {(activePo.status === 'ORDERED' || activePo.status === 'APPROVED') && (
                <button
                  className="btn btn-success"
                  style={{ background: '#0f9d58', color: '#fff', border: 'none' }}
                  onClick={() => handleReceive(activePo.id)}
                >
                  Receive Stock Now
                </button>
              )}
              <button className="btn btn-outline" onClick={() => setActivePo(null)}>Close</button>
            </div>
          </div>
        </div>
      )}

      {/* Create PO Modal */}
      {showModal && (
        <div className="modal-overlay" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div className="modal-card" style={{ background: '#fff', borderRadius: '12px', width: '90%', maxWidth: '700px', padding: '24px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #eee', paddingBottom: '12px' }}>
              <h3 style={{ margin: 0 }}>Create New Purchase Order</h3>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <button
                  type="button"
                  className="btn btn-sm btn-secondary"
                  onClick={fillSamplePo}
                  style={{ background: '#fef3c7', color: '#b45309', border: '1px solid #fde68a', fontWeight: 600 }}
                  title="Auto-fill sample supplier replenishment order"
                >
                  ✨ Auto-Fill Sample Data
                </button>
                <button className="btn btn-sm btn-outline" onClick={() => setShowModal(false)}>✕</button>
              </div>
            </div>

            <form onSubmit={handleCreatePo} style={{ marginTop: '16px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Supplier</label>
                  <select
                    className="form-control"
                    value={selectedSupplierId || ''}
                    onChange={(e) => setSelectedSupplierId(Number(e.target.value))}
                    required
                  >
                    {suppliers.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name} ({s.category || 'General'})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Priority</label>
                  <select
                    className="form-control"
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                  >
                    <option value="critical">Critical (Urgent Stockout)</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Reason / Notes</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. Weekly stock replenishment for staple grains"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                />
              </div>

              <h4>Order Line Items</h4>
              {items.map((item, idx) => (
                <div key={idx} style={{ display: 'grid', gridTemplateColumns: '3fr 1fr 1fr auto', gap: '8px', alignItems: 'center', marginBottom: '8px' }}>
                  <select
                    className="form-control"
                    value={item.product_id}
                    onChange={(e) => updateItem(idx, 'product_id', e.target.value)}
                    required
                  >
                    {products.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} (Stock: {p.current_stock})
                      </option>
                    ))}
                  </select>
                  <input
                    type="number"
                    className="form-control"
                    placeholder="Qty"
                    min="1"
                    step="any"
                    value={item.quantity}
                    onChange={(e) => updateItem(idx, 'quantity', Number(e.target.value))}
                    required
                  />
                  <input
                    type="number"
                    className="form-control"
                    placeholder="Unit Cost"
                    min="0"
                    step="any"
                    value={item.unit_cost}
                    onChange={(e) => updateItem(idx, 'unit_cost', Number(e.target.value))}
                  />
                  <button
                    type="button"
                    className="btn btn-sm btn-outline"
                    onClick={() => removeItemRow(idx)}
                    disabled={items.length <= 1}
                  >
                    ✕
                  </button>
                </div>
              ))}

              <button type="button" className="btn btn-sm btn-outline" style={{ marginTop: '8px' }} onClick={addItemRow}>
                + Add Product
              </button>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '24px', borderTop: '1px solid #eee', paddingTop: '16px' }}>
                <button type="button" className="btn btn-outline" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Creating...' : 'Submit Purchase Order'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
