import React, { createContext, useContext, useState, useEffect } from 'react';

export interface MerchantProfile {
  name: string;
  shopName: string;
  marketLocation: string;
  phone: string;
  email: string;
  category: string;
  isLoggedIn: boolean;
}

interface AuthContextType {
  merchant: MerchantProfile;
  login: (emailOrPhone: string, pass: string) => boolean;
  register: (profile: Omit<MerchantProfile, 'isLoggedIn'>) => void;
  logout: () => void;
  quickDemoLogin: (shopName?: string, ownerName?: string) => void;
}

const DEFAULT_MERCHANT: MerchantProfile = {
  name: 'Rajesh Sharma',
  shopName: 'Sharma Provision Store',
  marketLocation: 'Main Market, Bengaluru',
  phone: '+919611225645',
  email: 'sharma.kirana@example.com',
  category: 'Grocery & Supermarket',
  isLoggedIn: true,
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [merchant, setMerchant] = useState<MerchantProfile>(() => {
    try {
      const saved = localStorage.getItem('microbiz_merchant_profile');
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (e) {
      console.error('Error loading stored merchant profile:', e);
    }
    return DEFAULT_MERCHANT;
  });

  useEffect(() => {
    try {
      localStorage.setItem('microbiz_merchant_profile', JSON.stringify(merchant));
    } catch (e) {
      console.error('Error saving merchant profile:', e);
    }
  }, [merchant]);

  const login = (emailOrPhone: string, _pass: string): boolean => {
    // Allows logging in with any registered or demo credentials
    setMerchant((prev) => ({
      ...prev,
      email: emailOrPhone.includes('@') ? emailOrPhone : prev.email,
      phone: !emailOrPhone.includes('@') ? emailOrPhone : prev.phone,
      isLoggedIn: true,
    }));
    return true;
  };

  const register = (profile: Omit<MerchantProfile, 'isLoggedIn'>) => {
    const updated: MerchantProfile = {
      ...profile,
      isLoggedIn: true,
    };
    setMerchant(updated);
  };

  const logout = () => {
    setMerchant((prev) => ({
      ...prev,
      isLoggedIn: false,
    }));
  };

  const quickDemoLogin = (shopName?: string, ownerName?: string) => {
    setMerchant({
      name: ownerName || 'Chetan Gowda',
      shopName: shopName || 'Gowda Supermarket',
      marketLocation: 'Jayanagar 4th Block, Bengaluru',
      phone: '+919611225645',
      email: 'chetan.gowda@microbiz.ai',
      category: 'MSME Kirana & Retail',
      isLoggedIn: true,
    });
  };

  return (
    <AuthContext.Provider value={{ merchant, login, register, logout, quickDemoLogin }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
