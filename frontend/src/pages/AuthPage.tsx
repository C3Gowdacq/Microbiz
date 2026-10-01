import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const AuthPage: React.FC = () => {
  const navigate = useNavigate();
  const { register, login, quickDemoLogin } = useAuth();

  const [isRegisterTab, setIsRegisterTab] = useState<boolean>(true);

  // Form fields
  const [shopName, setShopName] = useState<string>('Gowda Supermarket');
  const [ownerName, setOwnerName] = useState<string>('Chetan Gowda');
  const [marketLocation, setMarketLocation] = useState<string>('Jayanagar 4th Block, Bengaluru');
  const [phone, setPhone] = useState<string>('+919611225645');
  const [email, setEmail] = useState<string>('chetan.gowda@microbiz.ai');
  const [category, setCategory] = useState<string>('Grocery & Kirana Supermarket');
  const [password, setPassword] = useState<string>('password123');
  const [showPassword, setShowPassword] = useState<boolean>(false);

  const [loading, setLoading] = useState<boolean>(false);
  const [successNotice, setSuccessNotice] = useState<string | null>(null);

  const handleRegisterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!shopName.trim() || !ownerName.trim()) return;

    setLoading(true);
    setSuccessNotice(`Registering "${shopName}" into MicroBiz Decision OS...`);

    setTimeout(() => {
      register({
        name: ownerName.trim(),
        shopName: shopName.trim(),
        marketLocation: marketLocation.trim() || 'Bengaluru',
        phone: phone.trim() || '+919611225645',
        email: email.trim() || 'merchant@microbiz.ai',
        category: category,
      });
      setLoading(false);
      navigate('/');
    }, 350);
  };

  const handleLoginSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      login(email || phone, password);
      setLoading(false);
      navigate('/');
    }, 300);
  };

  const handlePreset = (type: 'chetan' | 'rajesh') => {
    if (type === 'chetan') {
      quickDemoLogin('Gowda Supermarket', 'Chetan Gowda');
    } else {
      quickDemoLogin('Sharma Provision Store', 'Rajesh Sharma');
    }
    navigate('/');
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        width: '100vw',
        margin: 0,
        padding: 0,
        display: 'grid',
        gridTemplateColumns: 'minmax(460px, 1.05fr) minmax(520px, 1.2fr)',
        fontFamily: "'Outfit', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        background: '#090d16',
        overflowX: 'hidden',
      }}
    >
      {/* ════════════════════════════════════════════════════════════════════════
          LEFT HERO PANEL: Live Retail Intelligence Cockpit
      ════════════════════════════════════════════════════════════════════════ */}
      <div
        style={{
          background: 'linear-gradient(155deg, #070a12 0%, #0d1322 45%, #141b30 100%)',
          color: '#f8fafc',
          padding: '48px 44px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          position: 'relative',
          overflow: 'hidden',
          borderRight: '1px solid rgba(255, 255, 255, 0.08)',
        }}
      >
        {/* Subtle Ambient Glowing Mesh */}
        <div
          style={{
            position: 'absolute',
            top: '-10%',
            left: '-10%',
            width: '420px',
            height: '420px',
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(226, 55, 68, 0.28) 0%, rgba(226, 55, 68, 0) 70%)',
            pointerEvents: 'none',
            filter: 'blur(70px)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            bottom: '10%',
            right: '-15%',
            width: '460px',
            height: '460px',
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(79, 70, 229, 0.25) 0%, rgba(79, 70, 229, 0) 70%)',
            pointerEvents: 'none',
            filter: 'blur(80px)',
          }}
        />

        {/* Top Header & Brand */}
        <div style={{ position: 'relative', zIndex: 2 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '32px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              <div
                style={{
                  width: '46px',
                  height: '46px',
                  borderRadius: '13px',
                  background: 'linear-gradient(135deg, #e23744 0%, #991b1b 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 900,
                  fontSize: '22px',
                  color: '#ffffff',
                  boxShadow: '0 6px 22px rgba(226, 55, 68, 0.45)',
                  letterSpacing: '-0.5px',
                }}
              >
                M
              </div>
              <div>
                <div style={{ fontSize: '24px', fontWeight: 800, letterSpacing: '-0.5px', color: '#ffffff' }}>
                  micro<span style={{ color: '#e23744' }}>biz</span>
                </div>
                <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.14em', color: '#94a3b8', fontWeight: 700 }}>
                  Retail Decision OS & Kirana AI
                </div>
              </div>
            </div>

            {/* Live Status Pill */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '7px',
                background: 'rgba(16, 185, 129, 0.12)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                padding: '5px 12px',
                borderRadius: '20px',
                fontSize: '11px',
                fontWeight: 700,
                color: '#34d399',
              }}
            >
              <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 8px #10b981' }} />
              5 AGENTS ONLINE
            </div>
          </div>

          {/* Headline */}
          <h1
            style={{
              fontSize: '32px',
              fontWeight: 800,
              lineHeight: 1.25,
              color: '#ffffff',
              marginBottom: '14px',
              letterSpacing: '-0.6px',
            }}
          >
            Empowering Kirana Stores with{' '}
            <span
              style={{
                background: 'linear-gradient(135deg, #f43f5e 0%, #fb923c 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Autonomous Intelligence.
            </span>
          </h1>

          <p style={{ fontSize: '14px', color: '#94a3b8', lineHeight: 1.6, marginBottom: '26px' }}>
            Transform counter billing into an enterprise retail OS. Automate safety replenishment, safeguard working capital reserves, and recover customer credit effortlessly.
          </p>

          {/* ── Interactive Live Store Telemetry Showcase Card ── */}
          <div
            style={{
              background: 'rgba(255, 255, 255, 0.04)',
              backdropFilter: 'blur(16px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '16px',
              padding: '18px 20px',
              marginBottom: '26px',
              boxShadow: '0 12px 30px rgba(0, 0, 0, 0.35)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <div style={{ fontSize: '11px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span>⚡</span> LIVE ENGINE TELEMETRY
              </div>
              <span style={{ fontSize: '11px', color: '#64748b', fontFamily: "'JetBrains Mono', monospace" }}>
                127.0.0.1:8000
              </span>
            </div>

            {/* 3 Metric Badges */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginBottom: '14px' }}>
              <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '10px', padding: '10px 12px' }}>
                <div style={{ fontSize: '10px', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700 }}>Catalog Items</div>
                <div style={{ fontSize: '17px', fontWeight: 800, color: '#f8fafc', marginTop: '2px' }}>80 SKUs</div>
              </div>
              <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '10px', padding: '10px 12px' }}>
                <div style={{ fontSize: '10px', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700 }}>Khata Ledger</div>
                <div style={{ fontSize: '17px', fontWeight: 800, color: '#38bdf8', marginTop: '2px' }}>25 Accounts</div>
              </div>
              <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '10px', padding: '10px 12px' }}>
                <div style={{ fontSize: '10px', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700 }}>Liquid Reserve</div>
                <div style={{ fontSize: '17px', fontWeight: 800, color: '#34d399', marginTop: '2px' }}>₹5,63,000</div>
              </div>
            </div>

            {/* Real-time Agent Loop Feed */}
            <div style={{ background: 'rgba(0, 0, 0, 0.35)', borderRadius: '10px', padding: '10px 12px', border: '1px solid rgba(255, 255, 255, 0.05)', fontSize: '12px', color: '#cbd5e1' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <span style={{ color: '#e23744' }}>●</span>
                <span style={{ fontWeight: 600 }}>Replenishment Loop:</span>
                <span style={{ color: '#94a3b8', fontSize: '11px' }}>Auto-drafted PO #PO-2026-008 (40x Atta)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ color: '#10b981' }}>●</span>
                <span style={{ fontWeight: 600 }}>Digital Twin Sandbox:</span>
                <span style={{ color: '#94a3b8', fontSize: '11px' }}>Monte Carlo 10k runs pass 99.4% safety</span>
              </div>
            </div>
          </div>

          {/* 4 Feature Highlights Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px',
                background: 'rgba(255, 255, 255, 0.03)',
                padding: '12px 14px',
                borderRadius: '12px',
                border: '1px solid rgba(255, 255, 255, 0.06)',
              }}
            >
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: 'rgba(226, 55, 68, 0.18)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '15px',
                  flexShrink: 0,
                }}
              >
                ⚡
              </div>
              <div>
                <div style={{ fontSize: '12.5px', fontWeight: 700, color: '#ffffff' }}>Autonomous Replenishment</div>
                <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>Lead-time aware PO dispatch</div>
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px',
                background: 'rgba(255, 255, 255, 0.03)',
                padding: '12px 14px',
                borderRadius: '12px',
                border: '1px solid rgba(255, 255, 255, 0.06)',
              }}
            >
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: 'rgba(37, 99, 235, 0.18)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '15px',
                  flexShrink: 0,
                }}
              >
                🛒
              </div>
              <div>
                <div style={{ fontSize: '12.5px', fontWeight: 700, color: '#ffffff' }}>Rapid POS Billing</div>
                <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>Sub-second checkout & stock sync</div>
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px',
                background: 'rgba(255, 255, 255, 0.03)',
                padding: '12px 14px',
                borderRadius: '12px',
                border: '1px solid rgba(255, 255, 255, 0.06)',
              }}
            >
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: 'rgba(16, 185, 129, 0.18)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '15px',
                  flexShrink: 0,
                }}
              >
                👥
              </div>
              <div>
                <div style={{ fontSize: '12.5px', fontWeight: 700, color: '#ffffff' }}>Smart Khata Ledger</div>
                <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>WhatsApp collection reminders</div>
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px',
                background: 'rgba(255, 255, 255, 0.03)',
                padding: '12px 14px',
                borderRadius: '12px',
                border: '1px solid rgba(255, 255, 255, 0.06)',
              }}
            >
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: 'rgba(245, 158, 11, 0.18)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '15px',
                  flexShrink: 0,
                }}
              >
                🔒
              </div>
              <div>
                <div style={{ fontSize: '12.5px', fontWeight: 700, color: '#ffffff' }}>Zomato-Style Toggle</div>
                <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>Autonomous vs Manual modes</div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Infrastructure Badges */}
        <div
          style={{
            marginTop: '28px',
            paddingTop: '18px',
            borderTop: '1px solid rgba(255, 255, 255, 0.08)',
            position: 'relative',
            zIndex: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '11px',
            color: '#64748b',
          }}
        >
          <span>Powered by LangGraph DAG & FastAPI</span>
          <span>Twilio SMS Gateway • 256-bit Security</span>
        </div>
      </div>

      {/* ════════════════════════════════════════════════════════════════════════
          RIGHT FORM PANEL: High-Contrast, Elevated Merchant Portal
      ════════════════════════════════════════════════════════════════════════ */}
      <div
        style={{
          background: 'linear-gradient(135deg, #f8fafc 0%, #edf2f7 100%)',
          padding: '40px 36px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          overflowY: 'auto',
          position: 'relative',
        }}
      >
        {/* Soft Radial Ambient Glow */}
        <div
          style={{
            position: 'absolute',
            top: '20%',
            right: '15%',
            width: '350px',
            height: '350px',
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(226, 55, 68, 0.08) 0%, transparent 70%)',
            pointerEvents: 'none',
            filter: 'blur(50px)',
          }}
        />

        <div
          style={{
            width: '100%',
            maxWidth: '520px',
            background: '#ffffff',
            borderRadius: '24px',
            border: '1px solid rgba(226, 232, 240, 0.95)',
            boxShadow:
              '0 20px 50px -12px rgba(15, 23, 42, 0.12), 0 0 0 1px rgba(241, 245, 249, 0.8)',
            padding: '36px 34px',
            position: 'relative',
            zIndex: 2,
          }}
        >
          {/* Card Top Title & Subtitle */}
          <div style={{ textAlign: 'center', marginBottom: '22px' }}>
            <h2 style={{ fontSize: '24px', fontWeight: 800, color: '#0f172a', margin: '0 0 6px 0', letterSpacing: '-0.4px' }}>
              {isRegisterTab ? '🏪 Register Your Store' : '👋 Welcome Back, Merchant'}
            </h2>
            <p style={{ fontSize: '13px', color: '#64748b', margin: 0 }}>
              {isRegisterTab
                ? 'Launch your autonomous retail OS in under 30 seconds'
                : 'Sign in to monitor counter sales and AI recommendations'}
            </p>
          </div>

          {/* Top Segmented Tab Switcher */}
          <div
            style={{
              display: 'flex',
              background: '#f1f5f9',
              padding: '4px',
              borderRadius: '14px',
              marginBottom: '24px',
            }}
          >
            <button
              type="button"
              onClick={() => setIsRegisterTab(true)}
              style={{
                flex: 1,
                padding: '10px 14px',
                border: 'none',
                borderRadius: '10px',
                background: isRegisterTab ? '#ffffff' : 'transparent',
                color: isRegisterTab ? '#e23744' : '#64748b',
                fontWeight: isRegisterTab ? 800 : 600,
                fontSize: '13px',
                cursor: 'pointer',
                boxShadow: isRegisterTab ? '0 3px 10px rgba(0, 0, 0, 0.08)' : 'none',
                transition: 'all 0.18s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
              }}
            >
              <span>🏪</span>
              <span>Register New Store</span>
            </button>

            <button
              type="button"
              onClick={() => setIsRegisterTab(false)}
              style={{
                flex: 1,
                padding: '10px 14px',
                border: 'none',
                borderRadius: '10px',
                background: !isRegisterTab ? '#ffffff' : 'transparent',
                color: !isRegisterTab ? '#e23744' : '#64748b',
                fontWeight: !isRegisterTab ? 800 : 600,
                fontSize: '13px',
                cursor: 'pointer',
                boxShadow: !isRegisterTab ? '0 3px 10px rgba(0, 0, 0, 0.08)' : 'none',
                transition: 'all 0.18s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
              }}
            >
              <span>🔑</span>
              <span>Merchant Sign In</span>
            </button>
          </div>

          {successNotice && (
            <div
              style={{
                background: '#f0fdf4',
                color: '#166534',
                border: '1px solid #bbf7d0',
                padding: '10px 14px',
                borderRadius: '10px',
                marginBottom: '18px',
                fontSize: '13px',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span>✅</span>
              <span>{successNotice}</span>
            </div>
          )}

          {isRegisterTab ? (
            /* ───────── REGISTER NEW STORE FORM ───────── */
            <form onSubmit={handleRegisterSubmit}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '5px' }}>
                    Merchant Name *
                  </label>
                  <div style={{ position: 'relative' }}>
                    <span style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', fontSize: '14px' }}>
                      👤
                    </span>
                    <input
                      type="text"
                      required
                      value={ownerName}
                      onChange={(e) => setOwnerName(e.target.value)}
                      placeholder="e.g. Chetan Gowda"
                      style={{
                        width: '100%',
                        padding: '10px 12px 10px 36px',
                        borderRadius: '10px',
                        border: '1.5px solid #cbd5e1',
                        fontSize: '13.5px',
                        outline: 'none',
                        background: '#ffffff',
                        color: '#0f172a',
                        fontWeight: 600,
                        transition: 'all 0.18s',
                      }}
                      onFocus={(e) => {
                        e.currentTarget.style.borderColor = '#e23744';
                        e.currentTarget.style.boxShadow = '0 0 0 3px rgba(226, 55, 68, 0.12)';
                      }}
                      onBlur={(e) => {
                        e.currentTarget.style.borderColor = '#cbd5e1';
                        e.currentTarget.style.boxShadow = 'none';
                      }}
                    />
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '5px' }}>
                    Store / Kirana Name *
                  </label>
                  <div style={{ position: 'relative' }}>
                    <span style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', fontSize: '14px' }}>
                      🏪
                    </span>
                    <input
                      type="text"
                      required
                      value={shopName}
                      onChange={(e) => setShopName(e.target.value)}
                      placeholder="e.g. Gowda Supermarket"
                      style={{
                        width: '100%',
                        padding: '10px 12px 10px 36px',
                        borderRadius: '10px',
                        border: '1.5px solid #cbd5e1',
                        fontSize: '13.5px',
                        outline: 'none',
                        background: '#ffffff',
                        color: '#0f172a',
                        fontWeight: 600,
                        transition: 'all 0.18s',
                      }}
                      onFocus={(e) => {
                        e.currentTarget.style.borderColor = '#e23744';
                        e.currentTarget.style.boxShadow = '0 0 0 3px rgba(226, 55, 68, 0.12)';
                      }}
                      onBlur={(e) => {
                        e.currentTarget.style.borderColor = '#cbd5e1';
                        e.currentTarget.style.boxShadow = 'none';
                      }}
                    />
                  </div>
                </div>
              </div>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '5px' }}>
                  Market / Neighborhood Location *
                </label>
                <div style={{ position: 'relative' }}>
                  <span style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', fontSize: '14px' }}>
                    📍
                  </span>
                  <input
                    type="text"
                    required
                    value={marketLocation}
                    onChange={(e) => setMarketLocation(e.target.value)}
                    placeholder="e.g. Jayanagar 4th Block, Bengaluru"
                    style={{
                      width: '100%',
                      padding: '10px 12px 10px 36px',
                      borderRadius: '10px',
                      border: '1.5px solid #cbd5e1',
                      fontSize: '13.5px',
                      outline: 'none',
                      background: '#ffffff',
                      color: '#0f172a',
                      fontWeight: 600,
                      transition: 'all 0.18s',
                    }}
                    onFocus={(e) => {
                      e.currentTarget.style.borderColor = '#e23744';
                      e.currentTarget.style.boxShadow = '0 0 0 3px rgba(226, 55, 68, 0.12)';
                    }}
                    onBlur={(e) => {
                      e.currentTarget.style.borderColor = '#cbd5e1';
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '5px' }}>
                    Mobile Number *
                  </label>
                  <div style={{ position: 'relative' }}>
                    <span style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', fontSize: '14px' }}>
                      📱
                    </span>
                    <input
                      type="text"
                      required
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="+919611225645"
                      style={{
                        width: '100%',
                        padding: '10px 12px 10px 36px',
                        borderRadius: '10px',
                        border: '1.5px solid #cbd5e1',
                        fontSize: '13.5px',
                        outline: 'none',
                        background: '#ffffff',
                        color: '#0f172a',
                        fontWeight: 600,
                        transition: 'all 0.18s',
                      }}
                      onFocus={(e) => {
                        e.currentTarget.style.borderColor = '#e23744';
                        e.currentTarget.style.boxShadow = '0 0 0 3px rgba(226, 55, 68, 0.12)';
                      }}
                      onBlur={(e) => {
                        e.currentTarget.style.borderColor = '#cbd5e1';
                        e.currentTarget.style.boxShadow = 'none';
                      }}
                    />
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '5px' }}>
                    Retail Category
                  </label>
                  <div style={{ position: 'relative' }}>
                    <span style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', fontSize: '14px' }}>
                      🛒
                    </span>
                    <select
                      value={category}
                      onChange={(e) => setCategory(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '10px 12px 10px 36px',
                        borderRadius: '10px',
                        border: '1.5px solid #cbd5e1',
                        fontSize: '13px',
                        outline: 'none',
                        background: '#ffffff',
                        color: '#0f172a',
                        fontWeight: 600,
                        cursor: 'pointer',
                        transition: 'all 0.18s',
                      }}
                      onFocus={(e) => {
                        e.currentTarget.style.borderColor = '#e23744';
                        e.currentTarget.style.boxShadow = '0 0 0 3px rgba(226, 55, 68, 0.12)';
                      }}
                      onBlur={(e) => {
                        e.currentTarget.style.borderColor = '#cbd5e1';
                        e.currentTarget.style.boxShadow = 'none';
                      }}
                    >
                      <option value="Grocery & Kirana Supermarket">Grocery & Kirana</option>
                      <option value="FMCG Supermarket">FMCG Supermarket</option>
                      <option value="Provisions & Daily Needs">Provisions & Daily Needs</option>
                      <option value="General Store">General Merchant</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* ── Illuminated Live Store Signboard Preview ── */}
              <div
                style={{
                  background: 'linear-gradient(135deg, #ffffff 0%, #fff1f2 100%)',
                  border: '1.5px solid #fecdd3',
                  borderRadius: '14px',
                  padding: '14px 16px',
                  marginBottom: '20px',
                  boxShadow: '0 4px 14px rgba(226, 55, 68, 0.08)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontSize: '10px', fontWeight: 800, textTransform: 'uppercase', color: '#9f1239', letterSpacing: '0.06em' }}>
                    ✨ STORE SIGNBOARD PREVIEW:
                  </span>
                  <span
                    style={{
                      background: '#dcfce7',
                      color: '#15803d',
                      border: '1px solid #86efac',
                      fontSize: '10px',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '12px',
                    }}
                  >
                    ● READY TO DEPLOY
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div
                    style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '10px',
                      background: '#e23744',
                      color: '#ffffff',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '18px',
                      fontWeight: 800,
                      flexShrink: 0,
                    }}
                  >
                    🏪
                  </div>
                  <div style={{ minWidth: 0, flex: 1 }}>
                    <div style={{ fontWeight: 800, color: '#0f172a', fontSize: '14px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {shopName || 'Your Kirana Store'}
                    </div>
                    <div style={{ fontSize: '11.5px', color: '#64748b', marginTop: '1px' }}>
                      📍 {marketLocation || 'Bengaluru'} • Admin: {ownerName || 'Merchant'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Submit CTA */}
              <button
                type="submit"
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '14px',
                  borderRadius: '12px',
                  border: 'none',
                  background: 'linear-gradient(135deg, #e23744 0%, #b91c1c 100%)',
                  color: '#ffffff',
                  fontWeight: 800,
                  fontSize: '14.5px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  boxShadow: '0 6px 18px rgba(226, 55, 68, 0.38)',
                  transition: 'transform 0.15s ease, box-shadow 0.15s ease',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-1px)')}
                onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
              >
                {loading ? 'Initializing Store OS...' : '🚀 Register & Launch Store OS →'}
              </button>
            </form>
          ) : (
            /* ───────── MERCHANT SIGN IN FORM ───────── */
            <form onSubmit={handleLoginSubmit}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '5px' }}>
                  Mobile Number or Email *
                </label>
                <div style={{ position: 'relative' }}>
                  <span style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', fontSize: '14px' }}>
                    📱
                  </span>
                  <input
                    type="text"
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+919611225645 or merchant@microbiz.ai"
                    style={{
                      width: '100%',
                      padding: '11px 12px 11px 36px',
                      borderRadius: '10px',
                      border: '1.5px solid #cbd5e1',
                      fontSize: '14px',
                      outline: 'none',
                      background: '#ffffff',
                      color: '#0f172a',
                      fontWeight: 600,
                      transition: 'all 0.18s',
                    }}
                    onFocus={(e) => {
                      e.currentTarget.style.borderColor = '#e23744';
                      e.currentTarget.style.boxShadow = '0 0 0 3px rgba(226, 55, 68, 0.12)';
                    }}
                    onBlur={(e) => {
                      e.currentTarget.style.borderColor = '#cbd5e1';
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                  <label style={{ fontSize: '12px', fontWeight: 700, color: '#334155' }}>
                    Merchant Password *
                  </label>
                  <span style={{ fontSize: '11.5px', color: '#e23744', cursor: 'pointer', fontWeight: 700 }}>
                    Forgot Password?
                  </span>
                </div>
                <div style={{ position: 'relative' }}>
                  <span style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', fontSize: '14px' }}>
                    🔒
                  </span>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    style={{
                      width: '100%',
                      padding: '11px 38px 11px 36px',
                      borderRadius: '10px',
                      border: '1.5px solid #cbd5e1',
                      fontSize: '14px',
                      outline: 'none',
                      background: '#ffffff',
                      color: '#0f172a',
                      fontWeight: 600,
                      transition: 'all 0.18s',
                    }}
                    onFocus={(e) => {
                      e.currentTarget.style.borderColor = '#e23744';
                      e.currentTarget.style.boxShadow = '0 0 0 3px rgba(226, 55, 68, 0.12)';
                    }}
                    onBlur={(e) => {
                      e.currentTarget.style.borderColor = '#cbd5e1';
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{
                      position: 'absolute',
                      right: '12px',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      fontSize: '14px',
                      padding: 0,
                    }}
                    title={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? '🙈' : '👁️'}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '14px',
                  borderRadius: '12px',
                  border: 'none',
                  background: 'linear-gradient(135deg, #e23744 0%, #b91c1c 100%)',
                  color: '#ffffff',
                  fontWeight: 800,
                  fontSize: '14.5px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  boxShadow: '0 6px 18px rgba(226, 55, 68, 0.38)',
                  transition: 'transform 0.15s ease',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-1px)')}
                onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
              >
                {loading ? 'Authenticating...' : 'Sign In to Store Dashboard →'}
              </button>
            </form>
          )}

          {/* ── 1-Click Presentation Demo Presets ── */}
          <div
            style={{
              marginTop: '26px',
              paddingTop: '20px',
              borderTop: '1px solid #e2e8f0',
            }}
          >
            <div
              style={{
                fontSize: '11px',
                fontWeight: 800,
                color: '#64748b',
                textTransform: 'uppercase',
                marginBottom: '10px',
                letterSpacing: '0.04em',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span>⚡ 1-Click Guide Demo Presets:</span>
              <span style={{ color: '#10b981', fontWeight: 700 }}>● Instant Entry</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div
                role="button"
                tabIndex={0}
                onClick={() => handlePreset('chetan')}
                style={{
                  padding: '10px 12px',
                  borderRadius: '12px',
                  border: '1.5px solid #e2e8f0',
                  background: '#f8fafc',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  transition: 'all 0.16s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = '#e23744';
                  e.currentTarget.style.background = '#fff1f2';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = '#e2e8f0';
                  e.currentTarget.style.background = '#f8fafc';
                }}
              >
                <div
                  style={{
                    width: '30px',
                    height: '30px',
                    borderRadius: '8px',
                    background: '#fee2e2',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '14px',
                    flexShrink: 0,
                  }}
                >
                  👑
                </div>
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontSize: '12px', fontWeight: 800, color: '#0f172a', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    Chetan Gowda
                  </div>
                  <div style={{ fontSize: '10px', color: '#64748b' }}>Gowda Supermarket</div>
                </div>
              </div>

              <div
                role="button"
                tabIndex={0}
                onClick={() => handlePreset('rajesh')}
                style={{
                  padding: '10px 12px',
                  borderRadius: '12px',
                  border: '1.5px solid #e2e8f0',
                  background: '#f8fafc',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  transition: 'all 0.16s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = '#e23744';
                  e.currentTarget.style.background = '#fff1f2';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = '#e23744';
                  e.currentTarget.style.background = '#f8fafc';
                }}
              >
                <div
                  style={{
                    width: '30px',
                    height: '30px',
                    borderRadius: '8px',
                    background: '#e0f2fe',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '14px',
                    flexShrink: 0,
                  }}
                >
                  🏪
                </div>
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontSize: '12px', fontWeight: 800, color: '#0f172a', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    Rajesh Sharma
                  </div>
                  <div style={{ fontSize: '10px', color: '#64748b' }}>Sharma Provisions</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
