import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getCustomers,
  getCustomerSummary,
  createCustomer,
  Customer,
  CustomerCreate,
  CustomerSummary,
} from '../api';

interface CustomerWithSummary extends Customer {
  summary?: CustomerSummary;
}

export const CustomersPage: React.FC = () => {
  const [customers, setCustomers] = useState<CustomerWithSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [creating, setCreating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<CustomerCreate>({
    name: '',
    email: '',
    phone: '',
  });

  const navigate = useNavigate();

  const loadCustomers = async () => {
    try {
      setLoading(true);
      setError(null);
      const custList = await getCustomers();

      // Fetch summaries in parallel for outstanding balances
      const withSummaries = await Promise.all(
        custList.map(async (c) => {
          try {
            const summary = await getCustomerSummary(c.id);
            return { ...c, summary };
          } catch {
            return { ...c };
          }
        })
      );

      setCustomers(withSummaries);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load customers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCustomers();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setCreating(true);
      setError(null);
      await createCustomer(formData);
      setShowAddModal(false);
      setFormData({ name: '', email: '', phone: '' });
      await loadCustomers();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to create customer');
    } finally {
      setCreating(false);
    }
  };

  const fillSampleCustomer = () => {
    const randNum = Math.floor(100 + Math.random() * 900);
    setFormData({
      name: `Sharma Kirana Store (${randNum})`,
      email: `sharma.kirana${randNum}@example.com`,
      phone: `98765${randNum}12`,
    });
  };

  const filtered = customers.filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      (c.email && c.email.toLowerCase().includes(search.toLowerCase())) ||
      (c.phone && c.phone.includes(search))
  );

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Customers & Trade Accounts</h1>
          <p className="page-subtitle">Manage customer profiles, credit risk profiles, and accounts receivable</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-primary" onClick={() => setShowAddModal(true)}>
            ➕ Add Customer
          </button>
        </div>
      </div>

      {error && <div className="error-banner">⚠️ {error}</div>}

      <div style={{ marginBottom: 20 }}>
        <input
          type="text"
          className="form-control"
          placeholder="🔍 Search customers by name, email, or phone..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ maxWidth: 400 }}
        />
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Customer Name</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Outstanding Balance</th>
              <th>Credit Status</th>
              <th>Invoices</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: 32 }}>
                  <span className="spinner"></span> Loading customers & balances...
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: 32 }}>
                  No customer records found. Click "Add Customer" to add one.
                </td>
              </tr>
            ) : (
              filtered.map((customer) => {
                const balance = customer.summary?.outstanding_balance ?? 0;
                const daysOverdue = customer.summary?.days_overdue;
                const invoiceCount = customer.summary?.invoice_history?.length ?? 0;
                const isOverdue = daysOverdue !== undefined && daysOverdue !== null && daysOverdue > 0;

                return (
                  <tr key={customer.id} onClick={() => navigate(`/customers/${customer.id}`)}>
                    <td>
                      <strong style={{ fontSize: '0.95rem' }}>{customer.name}</strong>
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>{customer.email || '—'}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{customer.phone || '—'}</td>
                    <td>
                      <strong style={{ color: balance > 0 ? '#f59e0b' : '#10b981', fontSize: '1rem' }}>
                        ₹{balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </strong>
                    </td>
                    <td>
                      {isOverdue ? (
                        <span className="badge badge-high">⚠️ {daysOverdue}d Overdue</span>
                      ) : balance > 0 ? (
                        <span className="badge badge-medium">Current Balance</span>
                      ) : (
                        <span className="badge badge-low">✓ Settled</span>
                      )}
                    </td>
                    <td>{invoiceCount} recorded</td>
                    <td>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/customers/${customer.id}`);
                        }}
                      >
                        Account Ledger →
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Add Customer Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">➕ Add New Customer</h2>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <button
                  type="button"
                  className="btn btn-sm btn-secondary"
                  onClick={fillSampleCustomer}
                  style={{ background: '#fef3c7', color: '#b45309', border: '1px solid #fde68a', fontWeight: 600 }}
                  title="Auto-fill sample customer profile"
                >
                  ✨ Auto-Fill Sample Data
                </button>
                <button className="modal-close" onClick={() => setShowAddModal(false)}>
                  ×
                </button>
              </div>
            </div>

            <form onSubmit={handleCreate}>
              <div className="form-group" style={{ marginBottom: 14 }}>
                <label>Customer / Business Name *</label>
                <input
                  type="text"
                  required
                  className="form-control"
                  placeholder="e.g. Acme Corp or Rosa Retailer"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>

              <div className="form-group" style={{ marginBottom: 14 }}>
                <label>Email Address</label>
                <input
                  type="email"
                  className="form-control"
                  placeholder="e.g. billing@acme.com"
                  value={formData.email || ''}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
              </div>

              <div className="form-group" style={{ marginBottom: 20 }}>
                <label>Phone Number</label>
                <input
                  type="tel"
                  className="form-control"
                  placeholder="e.g. +39-555-0101"
                  value={formData.phone || ''}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowAddModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={creating}>
                  {creating ? 'Creating...' : 'Save Customer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
