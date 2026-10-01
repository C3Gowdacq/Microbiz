import React, { useEffect, useState } from 'react';
import { api } from '../api';

export const ZomatoModeToggle: React.FC = () => {
  const [isAutonomous, setIsAutonomous] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);

  const fetchCurrentMode = async () => {
    try {
      const res = await api.get('/api/settings');
      if (res.data && typeof res.data.autonomous_mode === 'boolean') {
        setIsAutonomous(res.data.autonomous_mode);
      }
    } catch (err) {
      console.error('Failed to fetch store mode:', err);
    }
  };

  useEffect(() => {
    fetchCurrentMode();

    const handleExternalChange = (e: any) => {
      if (typeof e.detail === 'boolean') {
        setIsAutonomous(e.detail);
      } else {
        fetchCurrentMode();
      }
    };

    window.addEventListener('modeChange', handleExternalChange);
    return () => window.removeEventListener('modeChange', handleExternalChange);
  }, []);

  const handleSelectMode = async (targetAutonomous: boolean) => {
    if (loading || targetAutonomous === isAutonomous) return;
    try {
      setLoading(true);
      setIsAutonomous(targetAutonomous); // Optimistic UI update
      const res = await api.put('/api/settings', { autonomous_mode: targetAutonomous });
      if (res.data) {
        setIsAutonomous(res.data.autonomous_mode);
        window.dispatchEvent(new CustomEvent('modeChange', { detail: res.data.autonomous_mode }));
      }
    } catch (err) {
      console.error('Failed to update store mode:', err);
      fetchCurrentMode(); // Rollback on error
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="zomato-switch-wrapper" title="Zomato-style Store Operating Mode Switch">
      <div
        className="zomato-switch-container"
        role="group"
        aria-label="Store Operating Mode"
      >
        {/* Sliding Thumb */}
        <div className={`zomato-switch-thumb ${isAutonomous ? 'automation' : 'manual'}`} />

        {/* Manual Button */}
        <button
          type="button"
          className={`zomato-switch-btn ${!isAutonomous ? 'active-text' : 'inactive-text'}`}
          onClick={() => handleSelectMode(false)}
          disabled={loading}
          title="Manual Mode: Merchant manually supervises and triggers all operational decisions"
        >
          <span style={{ fontSize: '13px' }}>🔒</span>
          <span>Manual</span>
        </button>

        {/* Automation Button */}
        <button
          type="button"
          className={`zomato-switch-btn ${isAutonomous ? 'active-text' : 'inactive-text'}`}
          onClick={() => handleSelectMode(true)}
          disabled={loading}
          title="Autonomous Mode: Closed-loop event listeners auto-evaluate stock, draft POs, and trigger alerts"
        >
          <span style={{ fontSize: '13px' }}>⚡</span>
          <span>Automation</span>
        </button>
      </div>

      {/* Mode Status Badge */}
      <span className={`zomato-mode-label ${isAutonomous ? 'automation' : 'manual'}`}>
        <span className={`zomato-indicator-dot ${isAutonomous ? 'green' : 'amber'}`}></span>
        {isAutonomous ? 'Auto Loop Active' : 'Supervised'}
      </span>
    </div>
  );
};
