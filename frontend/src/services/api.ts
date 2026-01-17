import { Transaction, User, Budget, RecurringTransaction, Category, CategoryCreate } from '../types';

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    ...options,
  });

  if (!response.ok) {
    if (response.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('paisatrack-user');
      }
      throw new Error('Authentication required. Please log in again.');
    }
    
    let errorMessage = `API Error: ${response.status} ${response.statusText}`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        if (Array.isArray(errorData.detail)) {
          errorMessage = errorData.detail.map((err: any) => 
            `${err.loc?.join('.')}: ${err.msg}`
          ).join(', ');
        } else {
          errorMessage = errorData.detail;
        }
      } else if (errorData.message) {
        errorMessage = errorData.message;
      }
    } catch {
    }
    
    throw new Error(errorMessage);
  }

  return response.json();
}

export const authService = {
  async login(email: string, password: string): Promise<User> {
    const response = await apiRequest<{ access_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    return response.user;
  },

  async register(userData: {
    name: string;
    email: string;
    password: string;
    otp_code: string;
  }): Promise<User> {
    const response = await apiRequest<{ access_token: string; user: User }>('/auth/signup', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
    return response.user;
  },

  async requestOTP(name: string, email: string): Promise<{ message: string }> {
    return apiRequest<{ message: string }>('/auth/request-otp', {
      method: 'POST',
      body: JSON.stringify({ name, email }),
    });
  },

  async logout(): Promise<void> {
    try {
      await apiRequest<void>('/auth/logout', {
        method: 'POST',
      });
    } catch (error) {
      console.error('Logout API call failed:', error);
    }
  },

  async getCurrentUser(): Promise<User | null> {
    try {
      return await apiRequest<User>('/users/me');
    } catch (error) {
      return null;
    }
  },

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

export const transactionService = {
  async getTransactions(type?: 'income' | 'expense'): Promise<Transaction[]> {
    const url = type ? `/transactions?type=${type}` : '/transactions';
    return apiRequest<Transaction[]>(url);
  },

  async getStats(): Promise<{
    total_income: number;
    total_expenses: number;
    balance: number;
    recent_transactions: Transaction[];
  }> {
    return apiRequest('/transactions/stats');
  },

  async createTransaction(transaction: {
    amount: number;
    type: 'income' | 'expense';
    category: string;
    note?: string;
    date: string;
  }): Promise<Transaction> {
    return apiRequest<Transaction>('/transactions', {
      method: 'POST',
      body: JSON.stringify(transaction),
    });
  },

  async deleteTransaction(id: string): Promise<void> {
    return apiRequest<void>(`/transactions/${id}`, {
      method: 'DELETE',
    });
  },
};

export const budgetService = {
  async getBudget(): Promise<Budget[]> {
    return apiRequest<Budget[]>('/budget');
  },

  async updateBudget(budget: Partial<Budget>): Promise<Budget> {
    return apiRequest<Budget>('/budget', {
      method: 'PUT',
      body: JSON.stringify(budget),
    });
  },
};

export const recurringTransactionService = {
  async getRecurringTransactions(): Promise<RecurringTransaction[]> {
    return apiRequest<RecurringTransaction[]>('/recurring-transactions');
  },

  async markAsPaid(id: string): Promise<void> {
    return apiRequest<void>(`/recurring-transactions/${id}/mark-paid`, {
      method: 'POST',
    });
  },

  async skipThisTime(id: string): Promise<void> {
    return apiRequest<void>(`/recurring-transactions/${id}/skip`, {
      method: 'POST',
    });
  },
};

export const userService = {
  async getProfile(): Promise<User> {
    return apiRequest<User>('/users/me');
  },

  async updateProfile(userData: { name?: string; password?: string; new_password?: string }): Promise<User> {
    return apiRequest<User>('/users/me', {
      method: 'PUT',
      body: JSON.stringify(userData),
    });
  },
};

export const categoryService = {
  async getCategories(type?: 'income' | 'expense'): Promise<Category[]> {
    const url = type ? `/categories?type=${type}` : '/categories';
    return apiRequest<Category[]>(url);
  },

  async createCategory(category: {
    name: string;
    type: 'income' | 'expense';
    icon: string;
    color?: string;
  }): Promise<Category> {
    return apiRequest<Category>('/categories', {
      method: 'POST',
      body: JSON.stringify(category),
    });
  },

  async updateCategory(id: string, category: {
    name: string;
    type: 'income' | 'expense';
    icon: string;
    color?: string;
  }): Promise<Category> {
    return apiRequest<Category>(`/categories/${id}`, {
      method: 'PUT',
      body: JSON.stringify(category),
    });
  },

  async deleteCategory(id: string): Promise<void> {
    return apiRequest<void>(`/categories/${id}`, {
      method: 'DELETE',
    });
  },
};
