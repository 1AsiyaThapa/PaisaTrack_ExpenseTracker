/**
 * API Service Layer - Real Backend Integration
 * 
 * This file contains real API implementations for all backend calls.
 * All functions make actual HTTP requests to the backend server.
 * 
 * CURRENT STATUS: 
 * - All functions make real API calls
 * - Backend integration is active
 * - Authentication and error handling included
 * 
 * CONFIGURATION:
 * - BASE_URL: Set via NEXT_PUBLIC_API_BASE_URL environment variable
 * - Default: http://localhost:8000
 * - Authentication: Uses cookies for session management
 */

import { Transaction, User, Budget, RecurringTransaction } from '../types';

// Configuration
const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'; // Backend URL


/**
 * Generic API request function
 * This will handle all HTTP requests to your backend
 * Uses HTTP-only cookies for authentication (no manual token handling needed)
 */
async function apiRequest<T>(
  endpoint: string, 
  options?: RequestInit
): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      // Authentication is handled via HTTP-only cookies automatically
    },
    credentials: 'include', // Include cookies for authentication
    ...options,
  });

  if (!response.ok) {
    // Handle authentication errors specifically
    if (response.status === 401) {
      // Clear any stale user data from localStorage
      if (typeof window !== 'undefined') {
        localStorage.removeItem('paisatrack-user');
      }
      // Only throw authentication error for actual API calls, not auth status checks
      throw new Error('Authentication required. Please log in again.');
    }
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

// =============================================================================
// AUTH SERVICES
// =============================================================================

export const authService = {
  /**
   * Login user with email and password
   * Backend endpoint: POST /auth/login
   * JWT token is automatically set as HTTP-only cookie by backend
   */
  async login(email: string, password: string): Promise<User> {
    const response = await apiRequest<{ access_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    // Token is automatically stored in HTTP-only cookie by backend
    // We only need to return the user data
    return response.user;
  },

  /**
   * Register new user
   * Backend endpoint: POST /auth/signup
   * JWT token is automatically set as HTTP-only cookie by backend
   */
  async register(userData: {
    name: string;
    email: string;
    password: string;
  }): Promise<User> {
    const response = await apiRequest<{ access_token: string; user: User }>('/auth/signup', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
    // Token is automatically stored in HTTP-only cookie by backend
    // We only need to return the user data
    return response.user;
  },

  /**
   * Logout user
   * Backend endpoint: POST /auth/logout
   */
  async logout(): Promise<void> {
    try {
      await apiRequest<void>('/auth/logout', {
        method: 'POST',
      });
    } catch (error) {
      // Continue with logout even if API call fails
      console.error('Logout API call failed:', error);
    }
  },

  /**
   * Get current user from server using cookie authentication
   * Backend endpoint: GET /users/me
   */
  async getCurrentUser(): Promise<User | null> {
    try {
      return await apiRequest<User>('/users/me');
    } catch (error) {
      // Don't log this as an error since it's expected when user is not authenticated
      // Just return null to indicate no valid session
      return null;
    }
  },

  /**
   * Check if user is authenticated by making a direct request
   * This method doesn't use the generic apiRequest to avoid error throwing
   */
  async checkAuthStatus(): Promise<User | null> {
    try {
      const response = await fetch(`${BASE_URL}/users/me`, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        return await response.json();
      }
      return null;
    } catch (error) {
      return null;
    }
  },
};

// =============================================================================
// TRANSACTION SERVICES
// =============================================================================

export const transactionService = {
  /**
   * Get all transactions for the current user
   * Backend endpoint: GET /transactions
   */
  async getTransactions(): Promise<Transaction[]> {
    return apiRequest<Transaction[]>('/transactions');
  },

  /**
   * Create a new transaction
   * Backend endpoint: POST /transactions
   */
  async createTransaction(transaction: Omit<Transaction, 'id'>): Promise<Transaction> {
    return apiRequest<Transaction>('/transactions', {
      method: 'POST',
      body: JSON.stringify(transaction),
    });
  },

  /**
   * Update an existing transaction
   * Backend endpoint: PUT /transactions/:id
   */
  async updateTransaction(id: string, transaction: Partial<Transaction>): Promise<Transaction> {
    return apiRequest<Transaction>(`/transactions/${id}`, {
      method: 'PUT',
      body: JSON.stringify(transaction),
    });
  },

  /**
   * Delete a transaction
   * Backend endpoint: DELETE /transactions/:id
   */
  async deleteTransaction(id: string): Promise<void> {
    return apiRequest<void>(`/transactions/${id}`, {
      method: 'DELETE',
    });
  },
};

// =============================================================================
// BUDGET SERVICES
// =============================================================================

export const budgetService = {
  /**
   * Get user's budget settings
   * Backend endpoint: GET /budget
   */
  async getBudget(): Promise<Budget[]> {
    return apiRequest<Budget[]>('/budget');
  },

  /**
   * Update budget settings
   * Backend endpoint: PUT /budget
   */
  async updateBudget(budget: Partial<Budget>): Promise<Budget> {
    return apiRequest<Budget>('/budget', {
      method: 'PUT',
      body: JSON.stringify(budget),
    });
  },
};

// =============================================================================
// RECURRING TRANSACTION SERVICES
// =============================================================================

export const recurringTransactionService = {
  /**
   * Get all recurring transactions
   * Backend endpoint: GET /recurring-transactions
   */
  async getRecurringTransactions(): Promise<RecurringTransaction[]> {
    return apiRequest<RecurringTransaction[]>('/recurring-transactions');
  },

  /**
   * Mark a recurring transaction as paid
   * Backend endpoint: POST /recurring-transactions/:id/mark-paid
   */
  async markAsPaid(id: string): Promise<void> {
    return apiRequest<void>(`/recurring-transactions/${id}/mark-paid`, {
      method: 'POST',
    });
  },

  /**
   * Skip a recurring transaction this time
   * Backend endpoint: POST /recurring-transactions/:id/skip
   */
  async skipThisTime(id: string): Promise<void> {
    return apiRequest<void>(`/recurring-transactions/${id}/skip`, {
      method: 'POST',
    });
  },
};

// =============================================================================
// USER PROFILE SERVICES
// =============================================================================

export const userService = {
  /**
   * Get user profile
   * Backend endpoint: GET /user/profile
   */
  async getProfile(): Promise<User> {
    return apiRequest<User>('/user/profile');
  },

  /**
   * Update user profile
   * Backend endpoint: PUT /user/profile
   */
  async updateProfile(userData: Partial<User>): Promise<User> {
    return apiRequest<User>('/user/profile', {
      method: 'PUT',
      body: JSON.stringify(userData),
    });
  },
};
