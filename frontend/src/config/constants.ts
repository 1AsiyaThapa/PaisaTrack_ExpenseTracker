/**
 * Application Constants for PaisaTrack
 * Centralized configuration for the PaisaTrack application
 */

// Application Configuration
export const APP_CONFIG = {
  name: 'PaisaTrack',
  description: 'Personal Finance Management Platform',
  version: '1.0.0',
} as const;

// API Configuration
export const API_CONFIG = {
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  version: 'v1',
  timeout: 10000, // 10 seconds
} as const;

// Export API_BASE_URL for backward compatibility
export const API_BASE_URL = API_CONFIG.baseUrl;

// Google OAuth Configuration
export const GOOGLE_CONFIG = {
  clientId: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || 'your_google_client_id_here',
  redirectUri: typeof window !== 'undefined' ? `${window.location.origin}/auth/callback` : '',
  scope: 'openid email profile',
} as const;

// Route Paths
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  SIGNUP: '/signup',
  AUTH_CALLBACK: '/auth/callback',
  DASHBOARD: '/dashboard',
} as const;

// Form Validation
export const VALIDATION = {
  email: {
    pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    message: 'Please enter a valid email address',
  },
  password: {
    minLength: 8,
    message: 'Password must be at least 8 characters long',
  },
  name: {
    minLength: 2,
    message: 'Name must be at least 2 characters long',
  },
} as const;

// Animation Durations
export const ANIMATIONS = {
  fast: 0.3,
  normal: 0.6,
  slow: 1.0,
} as const;

// Loading States
export const LOADING_TIMES = {
  login: 1500,
  signup: 2000,
  default: 1000,
} as const;

// Feature Highlights (for landing page)
export const FEATURES = [
  'Track your expenses and income',
  'Set and monitor budgets', 
  'Visualize your spending patterns',
  'Get insights into your finances',
] as const;

// Environment
export const IS_DEVELOPMENT = process.env.NODE_ENV === 'development';
export const IS_PRODUCTION = process.env.NODE_ENV === 'production';
