'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../types';
import { authService } from '../services/api';
import { STORAGE_KEYS } from '../utils/constants';

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string, otp_code: string) => Promise<void>;
  requestOTP: (name: string, email: string) => Promise<void>;
  logout: () => Promise<void>;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      if (typeof window !== 'undefined') {
        const savedUser = localStorage.getItem(STORAGE_KEYS.USER_DATA);
        if (savedUser) {
          try {
            setUser(JSON.parse(savedUser));
            setLoading(false);
            return;
          } catch (error) {
            console.error('Error parsing stored user data:', error);
            localStorage.removeItem(STORAGE_KEYS.USER_DATA);
          }
        }

        try {
          const userData = await authService.checkAuthStatus();
          if (userData) {
            setUser(userData);
            localStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(userData));
          }
        } catch (error) {
          console.error('Error checking auth status:', error);
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const userData = await authService.login(email, password);

      setUser(userData);
      if (typeof window !== 'undefined') {
        localStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(userData));
        window.location.href = '/dashboard';
      }
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const signup = async (name: string, email: string, password: string, otp_code: string) => {
    setLoading(true);
    try {
      const userData = await authService.register({ name, email, password, otp_code });

      setUser(userData);
      if (typeof window !== 'undefined') {
        localStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(userData));
        window.location.href = '/dashboard';
      }
    } catch (error) {
      console.error('Signup error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const requestOTP = async (name: string, email: string) => {
    setLoading(true);
    try {
      await authService.requestOTP(name, email);
    } catch (error) {
      console.error('Request OTP error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      if (typeof window !== 'undefined') {
        localStorage.removeItem(STORAGE_KEYS.USER_DATA);
      }
    }
  };

  return (
    <AuthContext.Provider value={{ user, login, signup, requestOTP, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
