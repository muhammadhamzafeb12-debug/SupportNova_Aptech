import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export const DEMO_CREDENTIALS = {
  CUSTOMER: { username: 'customer', password: 'customer123' },
  AGENT: { username: 'agent', password: 'agent123' },
  REVIEWER: { username: 'reviewer', password: 'reviewer123' },
  MANAGER: { username: 'manager', password: 'manager123' },
  ADMIN: { username: 'admin', password: 'admin123' }
};

// Robust helper function to safely parse API responses (JSON or plain text/HTML)
export const parseApiResponse = async (res, defaultErrorMsg = 'Operation failed. Please try again.') => {
  const contentType = res.headers.get('content-type') || '';
  let data = null;

  try {
    if (contentType.includes('application/json')) {
      data = await res.json();
    } else {
      const text = await res.text();
      if (text && text.trim().startsWith('{')) {
        try { data = JSON.parse(text); } catch (e) { data = { detail: text }; }
      } else {
        data = { detail: text || res.statusText };
      }
    }
  } catch (err) {
    data = { detail: defaultErrorMsg };
  }

  if (!res.ok) {
    let message = data?.detail || data?.message || defaultErrorMsg;
    if (typeof message === 'object') {
      message = JSON.stringify(message);
    }
    // Clean up raw HTML stacktraces or unhandled server crash messages
    if (typeof message === 'string' && (message.includes('<!DOCTYPE') || message.includes('Traceback') || message.includes('Internal Server Error'))) {
      message = 'Server response error (500). Please ensure backend service is active or try again.';
    }
    throw new Error(message);
  }

  return data;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
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

    const data = await parseApiResponse(res, 'Authentication failed. Please check your credentials.');

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
    return await parseApiResponse(res, 'Registration failed. Please check your inputs.');
  };

  const quickDemoLogin = async (roleName) => {
    const creds = DEMO_CREDENTIALS[roleName];
    if (!creds) throw new Error(`Unknown role profile: ${roleName}`);
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
        console.error('Logout notice:', err);
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
    return await parseApiResponse(res, 'Password reset request failed.');
  };

  const resetPassword = async (token_or_username, new_password) => {
    const res = await fetch('/api/auth/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token_or_username, new_password })
    });
    return await parseApiResponse(res, 'Password update failed.');
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
