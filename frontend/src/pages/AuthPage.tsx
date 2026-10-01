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
    }, 400);
  };

  const handleLoginSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      login(email || phone, password);
      setLoading(false);
      navigate('/');
    }, 350);
  };

  const handlePreset = (type: 'chetan' | 'rajesh') => {
    quickDemoLogin(type);
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
        gridTemplateColumns: 'minmax(420px, 1fr) minmax(480px, 1.25fr)',
        fontFamily: "'Outfit', 'Inter', -apple-system, sans-serif",
        background: '#ffffff',
        overflowX: 'hidden',
      }}
    >
      {/* ════════════════════════════════════════════════════════════════════════
          LEFT HERO PANEL: Edge-to-edge branded presentation
      ════════════════════════════════════════════════════════════════════════ */}
      <div
        style={{
          background: 'linear-gradient(155deg, #090d16 0%, #101626 45%, #1e1b4b 100%)',
          color: '#f8fafc',
          padding: '60px 48px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          position: 'relative',
          overflow: 'hidden',
          backgroundImage:
            'radial-gradient(circle, rgba(255, 255, 255, 0.07) 1px, transparent 1px), linear-gradient(155deg, #090d16 0%, #101626 45%, #1e1b4b 100%)',
          backgroundSize: '24px 24px, 100% 100%',
        }}
      >
        {/* Ambient Glowing Orbs */}
        <div
          style={{
            position: 'absolute',
            top: '-80px',
            left: '-80px',
            width: '380px',
            height: '380px',
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(226, 55, 68, 0.22) 0%, rgba(226, 55, 68, 0) 70%)',
            pointerEvents: 'none',
            filter: 'blur(50px)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            bottom: '5%',
            right: '-10%',
            width: '420px',
            height: '420px',
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(99, 102, 241, 0.25) 0%, rgba(99, 102, 241, 0) 70%)',
            pointerEvents: 'none',
            filter: 'blur(60px)',
          }}
        />

        {/* Top Branding */}
        <div style={{ position: 'relative', zIndex: 2 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '32px' }}>
            <div
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '14px',
                background: 'linear-gradient(135deg, #e23744 0%, #c92534 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 900,
                fontSize: '24px',
                color: '#ffffff',
                boxShadow: '0 6px 20px rgba(226, 55, 68, 0.45)',
                letterSpacing: '-0.5px',
              }}
            >
              M
            </div>
            <div>
              <div style={{ fontSize: '26px', fontWeight: 800, letterSpacing: '-0.5px', color: '#ffffff' }}>
                micro<span style={{ color: '#e23744' }}>biz</span>
              </div>
              <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.14em', color: '#94a3b8', fontWeight: 700 }}>
                Retail Decision OS & Kirana AI
              </div>
            </div>
          </div>

          {/* Headline */}
          <h1
            style={{
              fontSize: '34px',
              fontWeight: 800,
              lineHeight: 1.22,
              color: '#ffffff',
              marginBottom: '16px',
              letterSpacing: '-0.8px',
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

          <p style={{ fontSize: '15px', color: '#cbd5e1', lineHeight: 1.6, marginBottom: '36px', maxWidth: '520px' }}>
            Transform traditional counter billing into an enterprise retail OS. Automate stock replenishment, safeguard liquid reserves, and collect customer khata credit without paperwork.
          </p>

          {/* 4 Feature Highlights */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '520px' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '16px',
                background: 'rgba(255, 255, 255, 0.03)',
                padding: '12px 16px',
                borderRadius: '12px',
                border: '1px solid rgba(255, 255, 255, 0.06)',
              }}
            >
              <div
                style={{
                  width: '38px',
                  height: '38px',
                  borderRadius: '10px',
                  background: 'rgba(226, 55, 68, 0.18)',
                  border: '1px solid rgba(226, 55, 68, 0.35)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '18px',
                  flexShrink: 0,
                }}
              >
                ⚡
              </div>
              <div>
                <div style={{ fontSize: '14px', fontWeight: 700, color: '#ffffff' }}>
                  Closed-Loop Autonomous Engine
                </div>
                <div style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.4, marginTop: '2px' }}>
                  Continuous 5-agent loops monitoring stock gaps, safety buffers, and distributor lead times.
                </div>
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '16px',
                background: 'rgba(255, 255, 255, 0.03)',
                padding: '12px 16px',
                borderRadius: '12px',
                border: '1px solid rgba(255, 255, 255, 0.06)',
              }}
            >
              <div
                style={{
                  width: '38px',
                  height: '38px',
                  borderRadius: '10px',
                  background: 'rgba(37, 99, 235, 0.18)',
                  border: '1px solid rgba(37, 99, 235, 0.35)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '18px',
                  flexShrink: 0,
                }}
              >
                🛒
              </div>
              <div>
                <div style={{ fontSize: '14px', fontWeight: 700, color: '#ffffff' }}>
                  Rapid POS Checkout & Billing
                </div>
                <div style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.4, marginTop: '2px' }}>
                  Ring up customer purchases in milliseconds with instant stock deduction and ledger sync.
                </div>
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '16px',
                background: 'rgba(255, 255, 255, 0.03)',
                padding: '12px 16px',
                borderRadius: '12px',
                border: '1px solid rgba(255, 255, 255, 0.06)',
              }}
            >
              <div
                style={{
                  width: '38px',
                  height: '38px',
                  borderRadius: '10px',
                  background: 'rgba(16, 185, 129, 0.18)',
                  border: '1px solid rgba(16, 185, 129, 0.35)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '18px',
                  flexShrink: 0,
                }}
              >
                👥
              </div>
              <div>
                <div style={{ fontSize: '14px', fontWeight: 700, color: '#ffffff' }}>
                  Smart Khata & Automated Reminders
                </div>
                <div style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.4, marginTop: '2px' }}>
                  Dispatch polite WhatsApp and SMS collection payment links to recover customer udhaar.
                </div>
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '16px',
                background: 'rgba(255, 255, 255, 0.03)',
                padding: '12px 16px',
                borderRadius: '12px',
                border: '1px solid rgba(255, 255, 255, 0.06)',
              }}
            >
              <div
                style={{
                  width: '38px',
                  height: '38px',
                  borderRadius: '10px',
                  background: 'rgba(245, 158, 11, 0.18)',
                  border: '1px solid rgba(245, 158, 11, 0.35)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '18px',
                  flexShrink: 0,
                }}
              >
                🔒
              </div>
              <div>
                <div style={{ fontSize: '14px', fontWeight: 700, color: '#ffffff' }}>
                  Zomato-Style Dual Mode Switch
                </div>
                <div style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.4, marginTop: '2px' }}>
                  Switch on the fly between Autonomous AI executive loop and traditional Manual Kirana tools.
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Live System Operational Ticker Footnote */}
        <div
          style={{
            marginTop: '48px',
            paddingTop: '24px',
            borderTop: '1px solid rgba(255, 255, 255, 0.1)',
            position: 'relative',
            zIndex: 2,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#94a3b8' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', display: 'inline-block' }} />
              Twilio SMS Gateway Ready
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#94a3b8' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#3b82f6', display: 'inline-block' }} />
              5 Agents Synchronized
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#94a3b8' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f59e0b', display: 'inline-block' }} />
              ₹5,63,000 Liquid Reserve
            </div>
          </div>
        </div>
      </div>

      {/* ════════════════════════════════════════════════════════════════════════
          RIGHT FORM PANEL: Clean, bright, centered SaaS registration & login
      ════════════════════════════════════════════════════════════════════════ */}
      <div
        style={{
          background: '#f8fafc',
          padding: '60px 48px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          overflowY: 'auto',
        }}
      >
        <div
          style={{
            width: '100%',
            maxWidth: '540px',
            background: '#ffffff',
            borderRadius: '20px',
            border: '1px solid #e2e8f0',
            boxShadow: '0 10px 30px -5px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.02)',
            padding: '40px 36px',
          }}
        >
          {/* Top Segmented Tab Switcher */}
          <div
            style={{
              display: 'flex',
              background: '#f1f5f9',
              padding: '4px',
              borderRadius: '12px',
              marginBottom: '28px',
            }}
          >
            <button
              type="button"
              onClick={() => setIsRegisterTab(true)}
              style={{
                flex: 1,
                padding: '11px 16px',
                border: 'none',
                borderRadius: '8px',
                background: isRegisterTab ? '#ffffff' : 'transparent',
                color: isRegisterTab ? '#0f172a' : '#64748b',
                fontWeight: isRegisterTab ? 700 : 500,
                fontSize: '13px',
                cursor: 'pointer',
                boxShadow: isRegisterTab ? '0 2px 8px rgba(0, 0, 0, 0.08)' : 'none',
                transition: 'all 0.2s ease',
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
                padding: '11px 16px',
                border: 'none',
                borderRadius: '8px',
                background: !isRegisterTab ? '#ffffff' : 'transparent',
                color: !isRegisterTab ? '#0f172a' : '#64748b',
                fontWeight: !isRegisterTab ? 700 : 500,
                fontSize: '13px',
                cursor: 'pointer',
                boxShadow: !isRegisterTab ? '0 2px 8px rgba(0, 0, 0, 0.08)' : 'none',
                transition: 'all 0.2s ease',
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
                color: '#15803d',
                border: '1px solid #bbf7d0',
                padding: '10px 14px',
                borderRadius: '8px',
                marginBottom: '20px',
                fontSize: '13px',
                fontWeight: 600,
              }}
            >
              ✅ {successNotice}
            </div>
          )}

          {isRegisterTab ? (
            /* ───────── REGISTER NEW STORE FORM ───────── */
            <form onSubmit={handleRegisterSubmit}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '6px' }}>
                  Shopkeeper / Merchant Name *
                </label>
                <input
                  type="text"
                  required
                  value={ownerName}
                  onChange={(e) => setOwnerName(e.target.value)}
                  placeholder="e.g. Chetan Gowda"
                  style={{
                    width: '100%',
                    padding: '11px 14px',
                    borderRadius: '10px',
                    border: '1.5px solid #cbd5e1',
                    fontSize: '14px',
                    outline: 'none',
                    color: '#0f172a',
                    transition: 'border 0.2s',
                  }}
                  onFocus={(e) => (e.currentTarget.style.borderColor = '#e23744')}
                  onBlur={(e) => (e.currentTarget.style.borderColor = '#cbd5e1')}
                />
              </div>

              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '6px' }}>
                  Store / Kirana Business Name *
                </label>
                <input
                  type="text"
                  required
                  value={shopName}
                  onChange={(e) => setShopName(e.target.value)}
                  placeholder="e.g. Gowda Supermarket"
                  style={{
                    width: '100%',
                    padding: '11px 14px',
                    borderRadius: '10px',
                    border: '1.5px solid #cbd5e1',
                    fontSize: '14px',
                    outline: 'none',
                    color: '#0f172a',
                    transition: 'border 0.2s',
                  }}
                  onFocus={(e) => (e.currentTarget.style.borderColor = '#e23744')}
                  onBlur={(e) => (e.currentTarget.style.borderColor = '#cbd5e1')}
                />
              </div>

              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '6px' }}>
                  Market / Neighborhood Location *
                </label>
                <input
                  type="text"
                  required
                  value={marketLocation}
                  onChange={(e) => setMarketLocation(e.target.value)}
                  placeholder="e.g. Jayanagar 4th Block, Bengaluru"
                  style={{
                    width: '100%',
                    padding: '11px 14px',
                    borderRadius: '10px',
                    border: '1.5px solid #cbd5e1',
                    fontSize: '14px',
                    outline: 'none',
                    color: '#0f172a',
                    transition: 'border 0.2s',
                  }}
                  onFocus={(e) => (e.currentTarget.style.borderColor = '#e23744')}
                  onBlur={(e) => (e.currentTarget.style.borderColor = '#cbd5e1')}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '6px' }}>
                    Mobile Number *
                  </label>
                  <input
                    type="text"
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+919611225645"
                    style={{
                      width: '100%',
                      padding: '11px 14px',
                      borderRadius: '10px',
                      border: '1.5px solid #cbd5e1',
                      fontSize: '14px',
                      outline: 'none',
                      color: '#0f172a',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '6px' }}>
                    Retail Category
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '11px 12px',
                      borderRadius: '10px',
                      border: '1.5px solid #cbd5e1',
                      fontSize: '13px',
                      outline: 'none',
                      background: '#ffffff',
                      color: '#0f172a',
                    }}
                  >
                    <option value="Grocery & Kirana Supermarket">Grocery & Kirana</option>
                    <option value="FMCG Supermarket">FMCG Supermarket</option>
                    <option value="Provisions & Daily Needs">Provisions & Daily Needs</option>
                    <option value="General Store">General Merchant</option>
                  </select>
                </div>
              </div>

              {/* Dynamic Live Header Preview */}
              <div
                style={{
                  background: '#f8fafc',
                  border: '1.5px dashed #cbd5e1',
                  borderRadius: '10px',
                  padding: '12px 16px',
                  marginBottom: '20px',
                }}
              >
                <div style={{ fontSize: '10px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: '4px' }}>
                  Live Store Header Preview:
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '15px' }}>📍</span>
                  <div>
                    <span style={{ fontWeight: 700, color: '#0f172a', fontSize: '13px' }}>
                      {shopName || 'Your Store Name'}
                    </span>
                    <span style={{ color: '#64748b', fontSize: '12px' }}>
                      {' • '}{marketLocation || 'Your Market'}
                    </span>
                  </div>
                </div>
                <div style={{ fontSize: '11px', color: '#16a34a', fontWeight: 600, marginTop: '2px', marginLeft: '24px' }}>
                  Admin: {ownerName || 'Merchant'} (Store Admin)
                </div>
              </div>

              {/* Submit CTA */}
              <button
                type="submit"
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '13px',
                  borderRadius: '10px',
                  border: 'none',
                  background: 'linear-gradient(135deg, #e23744 0%, #c92534 100%)',
                  color: '#ffffff',
                  fontWeight: 700,
                  fontSize: '14px',
                  cursor: 'pointer',
                  boxShadow: '0 4px 14px rgba(226, 55, 68, 0.35)',
                  transition: 'transform 0.15s ease, box-shadow 0.15s ease',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-1px)')}
                onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
              >
                {loading ? 'Setting up Store...' : '🚀 Register & Launch Store OS'}
              </button>
            </form>
          ) : (
            /* ───────── MERCHANT SIGN IN FORM ───────── */
            <form onSubmit={handleLoginSubmit}>
              <div style={{ marginBottom: '18px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '6px' }}>
                  Mobile Number or Email *
                </label>
                <input
                  type="text"
                  required
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+919611225645 or merchant@microbiz.ai"
                  style={{
                    width: '100%',
                    padding: '12px 14px',
                    borderRadius: '10px',
                    border: '1.5px solid #cbd5e1',
                    fontSize: '14px',
                    outline: 'none',
                    color: '#0f172a',
                  }}
                  onFocus={(e) => (e.currentTarget.style.borderColor = '#e23744')}
                  onBlur={(e) => (e.currentTarget.style.borderColor = '#cbd5e1')}
                />
              </div>

              <div style={{ marginBottom: '22px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <label style={{ fontSize: '12px', fontWeight: 700, color: '#334155' }}>
                    Merchant Password *
                  </label>
                  <span style={{ fontSize: '11px', color: '#e23744', cursor: 'pointer', fontWeight: 600 }}>
                    Forgot?
                  </span>
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  style={{
                    width: '100%',
                    padding: '12px 14px',
                    borderRadius: '10px',
                    border: '1.5px solid #cbd5e1',
                    fontSize: '14px',
                    outline: 'none',
                    color: '#0f172a',
                  }}
                  onFocus={(e) => (e.currentTarget.style.borderColor = '#e23744')}
                  onBlur={(e) => (e.currentTarget.style.borderColor = '#cbd5e1')}
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '13px',
                  borderRadius: '10px',
                  border: 'none',
                  background: 'linear-gradient(135deg, #e23744 0%, #c92534 100%)',
                  color: '#ffffff',
                  fontWeight: 700,
                  fontSize: '14px',
                  cursor: 'pointer',
                  boxShadow: '0 4px 14px rgba(226, 55, 68, 0.35)',
                  transition: 'transform 0.15s ease',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-1px)')}
                onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
              >
                {loading ? 'Authenticating...' : 'Sign In to Dashboard →'}
              </button>
            </form>
          )}

          {/* 1-Click Pitch Presets for Live Evaluation */}
          <div
            style={{
              marginTop: '28px',
              paddingTop: '20px',
              borderTop: '1px solid #e2e8f0',
            }}
          >
            <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: '10px', letterSpacing: '0.04em' }}>
              ⚡ 1-Click Pitch Presets (For Live Demonstration):
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <button
                type="button"
                onClick={() => handlePreset('chetan')}
                style={{
                  padding: '10px 12px',
                  borderRadius: '8px',
                  border: '1px solid #cbd5e1',
                  background: '#f8fafc',
                  color: '#0f172a',
                  fontSize: '12px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  justifyContent: 'center',
                  transition: 'all 0.15s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = '#e23744';
                  e.currentTarget.style.background = '#fff1f2';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = '#cbd5e1';
                  e.currentTarget.style.background = '#f8fafc';
                }}
              >
                <span>👑</span>
                <span>Chetan Gowda</span>
              </button>

              <button
                type="button"
                onClick={() => handlePreset('rajesh')}
                style={{
                  padding: '10px 12px',
                  borderRadius: '8px',
                  border: '1px solid #cbd5e1',
                  background: '#f8fafc',
                  color: '#0f172a',
                  fontSize: '12px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  justifyContent: 'center',
                  transition: 'all 0.15s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = '#e23744';
                  e.currentTarget.style.background = '#fff1f2';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = '#cbd5e1';
                  e.currentTarget.style.background = '#f8fafc';
                }}
              >
                <span>🏪</span>
                <span>Rajesh Sharma</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
