import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { Sidebar } from './Sidebar';

export const Layout: React.FC = () => {
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        {/* Zomato-Style Global Store Header */}
        <header className="top-store-bar">
          <div className="store-badge">
            <span className="pin-icon">📍</span>
            <div>
              <span>Sharma Provision Store</span>
              <span className="store-market"> • Main Market, Bengaluru</span>
            </div>
          </div>

          <div className="header-status-group">
            <div className="status-pill">
              <span className="status-dot"></span>
              <span>Autonomous Engine Active</span>
            </div>
            
            <Link to="/recommendations" style={{ textDecoration: 'none' }}>
              <button className="btn btn-primary btn-sm">
                ⚡ Policy Approvals
              </button>
            </Link>

            <div className="user-profile-chip">
              <div className="profile-avatar">S</div>
              <span>Merchant Admin</span>
            </div>
          </div>
        </header>

        <Outlet />
      </main>
    </div>
  );
};
