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
        <div className="brand-icon">µB</div>
        <div>
          <div className="brand-title">MicroBizAI</div>
          <div className="brand-tag">Autonomous BI Engine</div>
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
            <span>Products & Stock</span>
          </div>
        </NavLink>

        <NavLink to="/forecasting" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <div className="nav-link-content">
            <span className="nav-icon">📈</span>
            <span>Sales Forecasting</span>
          </div>
        </NavLink>

        <NavLink to="/sales" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <div className="nav-link-content">
            <span className="nav-icon">🛒</span>
            <span>Sales Entry</span>
          </div>
        </NavLink>

        <NavLink to="/customers" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <div className="nav-link-content">
            <span className="nav-icon">👥</span>
            <span>Customers & Credit</span>
          </div>
        </NavLink>

        <NavLink to="/expenses" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <div className="nav-link-content">
            <span className="nav-icon">💸</span>
            <span>Expense Tracking</span>
          </div>
        </NavLink>

        <NavLink to="/recommendations" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <div className="nav-link-content">
            <span className="nav-icon">🤖</span>
            <span>AI Approvals</span>
          </div>
          {pendingCount > 0 && <span className="nav-badge">{pendingCount}</span>}
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <div className="status-dot"></div>
        <span>API Live on :8000</span>
      </div>
    </aside>
  );
};
