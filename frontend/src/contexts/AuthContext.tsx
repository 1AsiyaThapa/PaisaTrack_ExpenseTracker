'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../types';
import { authService } from '../services/api';
import { STORAGE_KEYS } from '../utils/constants';

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing session
    const checkAuth = async () => {
      if (typeof window !== 'undefined') {
        // First check localStorage
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

        // If no localStorage data, check if we have a valid session via cookie
        try {
          const userData = await authService.checkAuthStatus();
          if (userData) {
            setUser(userData);
            localStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(userData));
          }
          // If no userData, that's fine - user is just not authenticated
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
        // Redirect to dashboard after successful login
        window.location.href = '/dashboard';
      }
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const signup = async (name: string, email: string, password: string) => {
    setLoading(true);
    try {
      const userData = await authService.register({ name, email, password });
      
      setUser(userData);
      if (typeof window !== 'undefined') {
        localStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(userData));
        // Redirect to dashboard after successful signup
        window.location.href = '/dashboard';
      }
    } catch (error) {
      console.error('Signup error:', error);
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
      // Continue with logout even if API call fails
    } finally {
      setUser(null);
      if (typeof window !== 'undefined') {
        localStorage.removeItem(STORAGE_KEYS.USER_DATA);
        // No need to remove AUTH_TOKEN as it's handled by HTTP-only cookies
      }
    }
  };

  return (
    <AuthContext.Provider value={{ user, login, signup, logout, loading }}>
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
