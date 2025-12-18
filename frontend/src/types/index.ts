export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  google_id?: string;
  picture?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Authentication types
export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface SignupData {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}


export interface Transaction {
  id: string;
  amount: number;
  type: 'income' | 'expense';
  category: string;
  note?: string;
  date: string;
  created_at: string;
}

export interface Budget {
  id: string;
  category: string;
  limit: number;
  spent: number;
  period: 'monthly' | 'weekly' | 'yearly';
}

export interface RecurringTransaction {
  id: string;
  amount: number;
  description: string;
  category: string;
  type: 'income' | 'expense';
  frequency: 'monthly' | 'weekly' | 'yearly' | 'daily';
  nextDate: string;
  isActive: boolean;
}

