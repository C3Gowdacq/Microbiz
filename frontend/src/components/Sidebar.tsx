import React, { useEffect, useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { getAnalytics, getSettings } from '../api';

export const Sidebar: React.FC = () => {
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [isAutonomous, setIsAutonomous] = useState<boolean>(true);
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

  useEffect(() => {
    const fetchMode = async () => {
      try {
        const settings = await getSettings();
        setIsAutonomous(settings.autonomous_mode);
      } catch {}
    };
    fetchMode();

    const handleModeChange = (e: any) => {
      if (typeof e.detail === 'boolean') {
        setIsAutonomous(e.detail);
      } else {
        fetchMode();
      }
    };
    window.addEventListener('modeChange', handleModeChange);
    return () => window.removeEventListener('modeChange', handleModeChange);
  }, []);

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div className="sidebar-brand">
        <div className="brand-icon">M</div>
        <div>
          <div className="brand-title">micro<span className="red-text">biz</span></div>
          <div className="brand-tag">
            {isAutonomous ? 'Autonomous Retail OS' : 'Kirana Store Manager'}
          </div>
        </div>
      </div>

      {/* Mode Status Pill in Sidebar */}
      <div
        style={{
          padding: '8px 12px',
          margin: '0 4px 16px 4px',
          borderRadius: '8px',
          fontSize: '11px',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: isAutonomous ? '#f0fdf4' : '#f8fafc',
          border: `1px solid ${isAutonomous ? '#bbf7d0' : '#e2e8f0'}`,
          color: isAutonomous ? '#15803d' : '#475569',
        }}
      >
        <span style={{ fontSize: '14px' }}>{isAutonomous ? '⚡' : '🔒'}</span>
        <div>
          <div style={{ fontWeight: 700 }}>
            {isAutonomous ? 'Automation Mode' : 'Manual Mode'}
          </div>
          <div style={{ fontSize: '10px', color: '#64748b', fontWeight: 400 }}>
            {isAutonomous ? 'AI Handling Operations' : 'Manual Shopkeeper Control'}
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {isAutonomous ? (
          /* ───────── AUTONOMOUS INTERFACE (STREAMLINED: ONLY 3 CORE + SETTINGS) ───────── */
          <>
            <div style={{ padding: '4px 12px', fontSize: '10px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Autonomous Operations
            </div>

            <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} end>
              <div className="nav-link-content">
                <span className="nav-icon">📊</span>
                <span>Executive Dashboard</span>
              </div>
            </NavLink>

            <NavLink to="/sales" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <div className="nav-link-content">
                <span className="nav-icon">🛒</span>
                <span>Sales Entry (POS)</span>
              </div>
            </NavLink>

            <NavLink to="/recommendations" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <div className="nav-link-content">
                <span className="nav-icon">🤖</span>
                <span>AI Approvals</span>
              </div>
              {pendingCount > 0 && <span className="nav-badge">{pendingCount}</span>}
            </NavLink>

            <NavLink to="/agent-graph" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <div className="nav-link-content">
                <span className="nav-icon">🧠</span>
                <span>LangGraph DAG</span>
              </div>
            </NavLink>

            <NavLink to="/simulation" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <div className="nav-link-content">
                <span className="nav-icon">🎲</span>
                <span>Digital Twin Sandbox</span>
              </div>
            </NavLink>

            <div style={{ marginTop: '16px', padding: '4px 12px', fontSize: '10px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              System
            </div>

            <NavLink to="/settings" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <div className="nav-link-content">
                <span className="nav-icon">⚙️</span>
                <span>Settings</span>
              </div>
            </NavLink>
          </>
        ) : (
          /* ───────── MANUAL INTERFACE (FULL MANUAL KIRANA MODULES - ZERO AI ENGINE) ───────── */
          <>
            <div style={{ padding: '4px 12px', fontSize: '10px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Store Management
            </div>

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

            <NavLink to="/forecasting" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <div className="nav-link-content">
                <span className="nav-icon">🔮</span>
                <span>Demand Forecasting</span>
              </div>
            </NavLink>

            <div style={{ marginTop: '16px', padding: '4px 12px', fontSize: '10px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Preferences
            </div>

            <NavLink to="/settings" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <div className="nav-link-content">
                <span className="nav-icon">⚙️</span>
                <span>Settings</span>
              </div>
            </NavLink>
          </>
        )}
      </nav>

      {/* Sidebar Footer */}
      <div className="sidebar-footer">
        <div className="status-dot"></div>
        <span>{isAutonomous ? 'Autonomous Loop Active' : 'Manual Register Ready'}</span>
      </div>
    </aside>
  );
};
