'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useAuth } from '@/contexts/AuthContext';
import { transactionService } from '@/services/api';
import { Transaction } from '@/types';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { format } from 'date-fns';

export default function Dashboard() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState({
    total_income: 0,
    total_expenses: 0,
    balance: 0,
    recent_transactions: [] as Transaction[],
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await transactionService.getStats();
      setStats(data);
    } catch (error) {
      console.error('Error loading stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    router.push('/');
  };

  const handleDelete = async (id: string) => {
    if (confirm('Delete this transaction?')) {
      try {
        await transactionService.deleteTransaction(id);
        loadStats();
      } catch (error) {
        console.error('Error deleting transaction:', error);
      }
    }
  };

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50 p-4">
          <div className="max-w-6xl mx-auto">
            <div className="text-center py-20">Loading...</div>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-bold">Dashboard</h1>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => router.push('/income')}>
                Income
              </Button>
              <Button variant="outline" onClick={() => router.push('/expense')}>
                Expense
              </Button>
              <Button variant="ghost" onClick={handleLogout}>
                Logout
              </Button>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <Card>
              <CardContent>
                <div className="text-sm text-gray-600 mb-1">Total Income</div>
                <div className="text-2xl font-bold text-green-600">
                  ₹{stats.total_income.toLocaleString()}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent>
                <div className="text-sm text-gray-600 mb-1">Total Expenses</div>
                <div className="text-2xl font-bold text-red-600">
                  ₹{stats.total_expenses.toLocaleString()}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent>
                <div className="text-sm text-gray-600 mb-1">Balance</div>
                <div className={`text-2xl font-bold ${stats.balance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ₹{stats.balance.toLocaleString()}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recent Transactions */}
          <Card>
            <CardContent>
              <h2 className="text-lg font-semibold mb-4">Recent Transactions</h2>
              {stats.recent_transactions.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No transactions yet. Add income or expenses to get started.
                </div>
              ) : (
                <div className="space-y-2">
                  {stats.recent_transactions.map((tx) => (
                    <div
                      key={tx.id}
                      className="flex justify-between items-center p-3 bg-gray-50 rounded-lg"
                    >
                      <div className="flex-1">
                        <div className="font-medium">{tx.category}</div>
                        {tx.note && <div className="text-sm text-gray-500">{tx.note}</div>}
                        <div className="text-xs text-gray-400">
                          {format(new Date(tx.date), 'MMM dd, yyyy')}
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div
                          className={`font-bold ${
                            tx.type === 'income' ? 'text-green-600' : 'text-red-600'
                          }`}
                        >
                          {tx.type === 'income' ? '+' : '-'}₹{Number(tx.amount).toLocaleString()}
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(tx.id)}
                        >
                          Delete
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </ProtectedRoute>
  );
}
