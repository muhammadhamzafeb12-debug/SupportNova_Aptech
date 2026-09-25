import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

const DEMO_CREDENTIALS = {
  CUSTOMER: { username: 'customer', password: 'customer123' },
  AGENT: { username: 'agent', password: 'agent123' },
  REVIEWER: { username: 'reviewer', password: 'reviewer123' },
  MANAGER: { username: 'manager', password: 'manager123' },
  ADMIN: { username: 'admin', password: 'admin123' }
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Restore persistent session from localStorage on client side
    if (typeof window !== 'undefined') {
      const savedUser = localStorage.getItem('supportnova_user');
      const savedToken = localStorage.getItem('supportnova_token');
      if (savedUser && savedToken) {
        try {
          setUser(JSON.parse(savedUser));
          setToken(savedToken);
        } catch (err) {
          localStorage.removeItem('supportnova_token');
          localStorage.removeItem('supportnova_user');
        }
      }
    }
    setLoading(false);
  }, []);

  const login = async (username_or_email, password, remember_me = false) => {
    const res = await fetch('/api/auth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username_or_email, password, remember_me })
    });
    
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || 'Login failed');
    }

    const data = await res.json();
    const userObj = {
      username: data.username,
      email: data.email,
      role: data.role,
      full_name: data.full_name,
      is_active: data.is_active
    };

    setToken(data.access_token);
    setUser(userObj);
    localStorage.setItem('supportnova_token', data.access_token);
    localStorage.setItem('supportnova_user', JSON.stringify(userObj));
    return userObj;
  };

  const register = async (username, email, full_name, password, role = 'CUSTOMER') => {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, full_name, password, role })
    });
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || 'Registration failed');
    }
    return await res.json();
  };

  const quickDemoLogin = async (roleName) => {
    const creds = DEMO_CREDENTIALS[roleName];
    if (!creds) throw new Error(`Unknown role: ${roleName}`);
    return await login(creds.username, creds.password, true);
  };

  const logout = async () => {
    if (token) {
      try {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        });
      } catch (err) {
        console.error('Logout error:', err);
      }
    }
    setUser(null);
    setToken('');
    localStorage.removeItem('supportnova_token');
    localStorage.removeItem('supportnova_user');
  };

  const forgotPassword = async (email_or_username) => {
    const res = await fetch('/api/auth/forgot-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email_or_username })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Request failed');
    }
    return await res.json();
  };

  const resetPassword = async (token_or_username, new_password) => {
    const res = await fetch('/api/auth/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token_or_username, new_password })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Reset failed');
    }
    return await res.json();
  };

  return (
    <AuthContext.Provider value={{
      user, token, loading, login, register, logout, quickDemoLogin, switchRoleDemo: quickDemoLogin, forgotPassword, resetPassword
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
