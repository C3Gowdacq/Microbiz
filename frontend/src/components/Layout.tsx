import React, { useState, useEffect } from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { ZomatoModeToggle } from './ZomatoModeToggle';
import { useAuth } from '../context/AuthContext';
import { getSettings } from '../api';

export const Layout: React.FC = () => {
  const { merchant, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [showProfileMenu, setShowProfileMenu] = useState<boolean>(false);
  const [isAutonomous, setIsAutonomous] = useState<boolean>(true);

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

  // Strict route isolation between Autonomous Mode and Manual Mode
  useEffect(() => {
    const p = location.pathname;
    if (isAutonomous) {
      // In Autonomous Mode: disallow manual micro-management modules
      const manualOnlyPrefixes = ['/products', '/customers', '/expenses', '/purchase-orders', '/forecasting', '/automation'];
      if (manualOnlyPrefixes.some((prefix) => p === prefix || p.startsWith(prefix + '/'))) {
        navigate('/', { replace: true });
      }
    } else {
      // In Manual Mode: disallow autonomous agent engines
      const autoOnlyRoutes = ['/agent-graph', '/simulation', '/recommendations'];
      if (autoOnlyRoutes.some((route) => p === route || p.startsWith(route + '/'))) {
        navigate('/', { replace: true });
      }
    }
  }, [isAutonomous, location.pathname, navigate]);

  const initialLetter = merchant.name ? merchant.name.trim().charAt(0).toUpperCase() : 'M';

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="app-layout">
      <Sidebar />
      <div className="content-wrapper">
        {/* Dynamic Global Store Header (Permanently Sticky at Top) */}
        <header className="top-store-bar">
          <div
            className="store-badge"
            onClick={() => navigate('/register')}
            title="Click to switch or register store profile"
            style={{ cursor: 'pointer' }}
          >
            <span className="pin-icon">📍</span>
            <div>
              <span style={{ fontWeight: 700, fontSize: '14px', color: '#0f172a' }}>
                {merchant.shopName || 'MicroBiz Kirana Store'}
              </span>
              <span className="store-market" style={{ fontSize: '12px', color: '#64748b' }}>
                {' '}• {merchant.marketLocation || 'Bengaluru'}
              </span>
            </div>
          </div>

          <div className="header-status-group">
            {/* Zomato-Style Sliding Switch: Manual vs Automation */}
            <ZomatoModeToggle />

            {isAutonomous ? (
              <Link to="/recommendations" style={{ textDecoration: 'none' }}>
                <button className="btn btn-primary btn-sm" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span>🤖</span>
                  <span>AI Approvals</span>
                </button>
              </Link>
            ) : (
              <Link to="/sales" style={{ textDecoration: 'none' }}>
                <button
                  className="btn btn-primary btn-sm"
                  style={{ background: '#16a34a', borderColor: '#16a34a', display: 'flex', alignItems: 'center', gap: '6px' }}
                >
                  <span>🛒</span>
                  <span>New POS Bill</span>
                </button>
              </Link>
            )}

            {/* Dynamic Merchant Profile Chip with Dropdown */}
            <div style={{ position: 'relative' }}>
              <div
                className="user-profile-chip"
                onClick={() => setShowProfileMenu((prev) => !prev)}
                style={{ cursor: 'pointer', userSelect: 'none' }}
                title="Account & Store Settings"
              >
                <div className="profile-avatar">{initialLetter}</div>
                <span style={{ fontWeight: 600, fontSize: '13px' }}>{merchant.name || 'Merchant Admin'}</span>
                <span style={{ fontSize: '10px', color: '#64748b' }}>▼</span>
              </div>

              {showProfileMenu && (
                <div
                  style={{
                    position: 'absolute',
                    top: '115%',
                    right: 0,
                    width: '240px',
                    background: '#ffffff',
                    borderRadius: '12px',
                    boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.15), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
                    border: '1px solid #e2e8f0',
                    padding: '12px',
                    zIndex: 100,
                  }}
                >
                  <div style={{ paddingBottom: '10px', borderBottom: '1px solid #f1f5f9', marginBottom: '8px' }}>
                    <div style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a' }}>{merchant.name}</div>
                    <div style={{ fontSize: '11px', color: '#16a34a', fontWeight: 600 }}>{merchant.shopName}</div>
                    <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>{merchant.phone}</div>
                  </div>

                  <button
                    onClick={() => {
                      setShowProfileMenu(false);
                      navigate('/register');
                    }}
                    style={{
                      width: '100%',
                      textAlign: 'left',
                      padding: '8px 10px',
                      background: 'transparent',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '12px',
                      fontWeight: 600,
                      color: '#334155',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = '#f1f5f9')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                  >
                    <span>🏪</span> Switch / Register New Store
                  </button>

                  <button
                    onClick={() => {
                      setShowProfileMenu(false);
                      handleLogout();
                    }}
                    style={{
                      width: '100%',
                      textAlign: 'left',
                      padding: '8px 10px',
                      background: 'transparent',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '12px',
                      fontWeight: 600,
                      color: '#dc2626',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      marginTop: '4px',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = '#fee2e2')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                  >
                    <span>🚪</span> Sign Out
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Scrollable Main Content Area */}
        <main className="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

