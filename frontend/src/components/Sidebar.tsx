import React, { useEffect, useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { getAnalytics } from '../api';

export const Sidebar: React.FC = () => {
  const [pendingCount, setPendingCount] = useState<number>(0);
  const location = useLocation();

  useEffect(() => {
    const fetchPending = async () => {
      try {
        const stats = await getAnalytics();
        setPendingCount(stats.pending_count);
      } catch {
        // ignore background fetch errors
      }
    };
    fetchPending();
    const interval = setInterval(fetchPending, 10000);
    return () => clearInterval(interval);
  }, [location]);

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">M</div>
        <div>
          <div className="brand-title">micro<span className="red-text">biz</span></div>
          <div className="brand-tag">Retail Decision OS</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} end>
          <div className="nav-link-content">
            <span className="nav-icon">📊</span>
            <span>Dashboard</span>
          </div>
        </NavLink>

        <NavLink to="/products" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <div className="nav-link-content">
            <span className="nav-icon">📦</span>
            <span>Grocery & Stock</span>
          </div>
        </NavLink>

        <NavLink to="/forecasting" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <div className="nav-link-content">
            <span className="nav-icon">🔮</span>
            <span>Demand Forecasting</span>
          </div>
        </NavLink>

        <NavLink to="/sales" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <div className="nav-link-content">
            <span className="nav-icon">🛒</span>
            <span>Sales Entry (POS)</span>
          </div>
        </NavLink>

        <NavLink to="/purchase-orders" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <div className="nav-link-content">
            <span className="nav-icon">📝</span>
            <span>Purchase Orders</span>
          </div>
        </NavLink>

        <NavLink to="/automation" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <div className="nav-link-content">
            <span className="nav-icon">⚡</span>
            <span>Autonomous Engine</span>
          </div>
        </NavLink>

        <NavLink to="/customers" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <div className="nav-link-content">
            <span className="nav-icon">👥</span>
            <span>Customer Khata</span>
          </div>
        </NavLink>

        <NavLink to="/expenses" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <div className="nav-link-content">
            <span className="nav-icon">💸</span>
            <span>Expense Tracker</span>
          </div>
        </NavLink>

        <NavLink to="/recommendations" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <div className="nav-link-content">
            <span className="nav-icon">🤖</span>
            <span>AI Approvals</span>
          </div>
          {pendingCount > 0 && <span className="nav-badge">{pendingCount}</span>}
        </NavLink>

        <NavLink to="/settings" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <div className="nav-link-content">
            <span className="nav-icon">⚙️</span>
            <span>Settings</span>
          </div>
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <div className="status-dot"></div>
        <span>API Live on :8000</span>
      </div>
    </aside>
  );
};
