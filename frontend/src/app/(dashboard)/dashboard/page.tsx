'use client';

import { useAuth } from '@/contexts/AuthContext';
import { transactionService } from '@/services/api';
import { Transaction } from '@/types';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useEffect, useState } from 'react';
import { format } from 'date-fns';
import { Wallet, CreditCard, PiggyBank, TrendingDown, ArrowRight, AlertCircle } from 'lucide-react';
import { DashboardSummaryChart } from '@/components/charts/DashboardSummaryChart';
import Link from 'next/link';

import { ConfirmationModal } from '@/components/ui/ConfirmationModal';

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    total_income: 0,
    total_expenses: 0,
    balance: 0,
    monthly_budget: 0,
    monthly_spent: 0,
    reset_date: '',
    recent_transactions: [] as Transaction[],
  });
  const [chartData, setChartData] = useState<Array<Record<string, string | number>>>([]);
  const [loading, setLoading] = useState(true);

  // Delete Confirmation State
  const [deleteId, setDeleteId] = useState<string | null>(null);

  useEffect(() => {
    loadStats();
    loadChartData();
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

  const loadChartData = async () => {
    try {
      const response = await transactionService.getDashboardSummary(6);
      setChartData(response.data);
    } catch (error) {
      console.error('Error loading chart data:', error);
    }
  };

  const confirmDelete = async () => {
    if (!deleteId) return;
    try {
      await transactionService.deleteTransaction(deleteId);
      loadStats();
    } catch (error) {
      console.error('Error deleting transaction:', error);
    } finally {
      setDeleteId(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center py-20">Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">Welcome back, {user?.email}</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="border-none shadow-sm bg-white/50 backdrop-blur-sm hover:shadow-md transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-50 rounded-xl">
                <div className="w-6 h-6 text-green-600">
                  <Wallet size={24} />
                </div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-500">Total Income</div>
                <div className="text-2xl font-bold text-gray-900">
                  ₹{stats.total_income.toLocaleString()}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-none shadow-sm bg-white/50 backdrop-blur-sm hover:shadow-md transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-red-50 rounded-xl">
                <div className="w-6 h-6 text-red-600">
                  <CreditCard size={24} />
                </div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-500">Total Expenses</div>
                <div className="text-2xl font-bold text-gray-900">
                  ₹{stats.total_expenses.toLocaleString()}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-none shadow-sm bg-white/50 backdrop-blur-sm hover:shadow-md transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-50 rounded-xl">
                <div className="w-6 h-6 text-blue-600">
                  <PiggyBank size={24} />
                </div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-500">Total Balance</div>
                <div className={`text-2xl font-bold ${stats.balance >= 0 ? 'text-gray-900' : 'text-red-600'}`}>
                  ₹{stats.balance.toLocaleString()}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Link href="/budget" className="block">
          <Card className="border-none shadow-sm bg-white/50 backdrop-blur-sm hover:shadow-md transition-all hover:scale-[1.02] cursor-pointer">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-purple-50 rounded-xl">
                  <div className="w-6 h-6 text-purple-600">
                    <TrendingDown size={24} />
                  </div>
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-500">Monthly Budget</div>
                  {stats.monthly_budget > 0 ? (
                    <>
                      <div className="text-2xl font-bold text-gray-900">
                        ₹{stats.monthly_spent.toLocaleString()}
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <div className="text-xs text-gray-500">
                          of ₹{stats.monthly_budget.toLocaleString()}
                        </div>
                        <div className={`text-xs font-semibold ${
                          Math.round((stats.monthly_spent / stats.monthly_budget) * 100) >= 100 ? 'text-red-600' :
                          Math.round((stats.monthly_spent / stats.monthly_budget) * 100) >= 80 ? 'text-orange-600' :
                          'text-green-600'
                        }`}>
                          ({Math.round((stats.monthly_spent / stats.monthly_budget) * 100)}%)
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="text-sm text-purple-600 font-medium mt-1 flex items-center gap-1">
                      Set budget <ArrowRight className="w-3 h-3" />
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* Budget Summary Card */}
      {stats.monthly_budget > 0 && (
        <Card className="border-none shadow-sm bg-gradient-to-br from-purple-50 to-white backdrop-blur-sm">
          <CardContent className="p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <PiggyBank className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-gray-900">Monthly Budget</h2>
                  <p className="text-sm text-gray-500">Track your spending this month</p>
                </div>
              </div>
              <Link href="/budget">
                <Button variant="ghost" size="sm" className="text-purple-600 hover:text-purple-700 hover:bg-purple-50">
                  View Details
                  <ArrowRight className="w-4 h-4 ml-1" />
                </Button>
              </Link>
            </div>

            <div className="space-y-4">
              {/* Budget Stats */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-white/70 rounded-lg p-4">
                  <div className="text-xs text-gray-500 mb-1">Budget</div>
                  <div className="text-xl font-bold text-gray-900">
                    ₹{stats.monthly_budget.toLocaleString()}
                  </div>
                </div>
                <div className="bg-white/70 rounded-lg p-4">
                  <div className="text-xs text-gray-500 mb-1">Spent</div>
                  <div className="text-xl font-bold text-red-600">
                    ₹{stats.monthly_spent.toLocaleString()}
                  </div>
                </div>
                <div className="bg-white/70 rounded-lg p-4">
                  <div className="text-xs text-gray-500 mb-1">Remaining</div>
                  <div className={`text-xl font-bold ${(stats.monthly_budget - stats.monthly_spent) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    ₹{Math.abs(stats.monthly_budget - stats.monthly_spent).toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-700">Progress</span>
                  <span className={`text-sm font-bold ${
                    Math.round((stats.monthly_spent / stats.monthly_budget) * 100) >= 100 ? 'text-red-600' :
                    Math.round((stats.monthly_spent / stats.monthly_budget) * 100) >= 80 ? 'text-orange-600' :
                    'text-green-600'
                  }`}>
                    {Math.round((stats.monthly_spent / stats.monthly_budget) * 100)}%
                  </span>
                </div>
                <div className="relative w-full h-3 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ease-out ${
                      Math.round((stats.monthly_spent / stats.monthly_budget) * 100) >= 100 ? 'bg-red-600' :
                      Math.round((stats.monthly_spent / stats.monthly_budget) * 100) >= 80 ? 'bg-orange-500' :
                      'bg-green-600'
                    }`}
                    style={{ width: `${Math.min(Math.round((stats.monthly_spent / stats.monthly_budget) * 100), 100)}%` }}
                  />
                </div>
              </div>

              {/* Status Alert */}
              {Math.round((stats.monthly_spent / stats.monthly_budget) * 100) >= 80 && (
                <div className={`flex items-start gap-2 p-3 rounded-lg ${
                  Math.round((stats.monthly_spent / stats.monthly_budget) * 100) >= 100 
                    ? 'bg-red-50 border border-red-200' 
                    : 'bg-orange-50 border border-orange-200'
                }`}>
                  <AlertCircle className={`w-4 h-4 mt-0.5 flex-shrink-0 ${
                    Math.round((stats.monthly_spent / stats.monthly_budget) * 100) >= 100 
                      ? 'text-red-600' 
                      : 'text-orange-600'
                  }`} />
                  <p className={`text-sm ${
                    Math.round((stats.monthly_spent / stats.monthly_budget) * 100) >= 100 
                      ? 'text-red-800' 
                      : 'text-orange-800'
                  }`}>
                    {Math.round((stats.monthly_spent / stats.monthly_budget) * 100) >= 100 
                      ? `You've exceeded your budget by ₹${Math.abs(stats.monthly_budget - stats.monthly_spent).toLocaleString()}`
                      : `You're approaching your budget limit. ₹${(stats.monthly_budget - stats.monthly_spent).toLocaleString()} remaining.`
                    }
                  </p>
                </div>
              )}

              {/* Reset Date */}
              <div className="text-xs text-gray-500 text-center pt-2">
                Budget resets on {format(new Date(stats.reset_date), 'MMM dd, yyyy')}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* No Budget Set */}
      {stats.monthly_budget === 0 && (
        <Card className="border-none shadow-sm bg-gradient-to-br from-purple-50 to-white backdrop-blur-sm">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-purple-100 rounded-lg">
                  <PiggyBank className="w-8 h-8 text-purple-600" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">Set Your Monthly Budget</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Track your spending and stay on top of your finances
                  </p>
                </div>
              </div>
              <Link href="/budget">
                <Button className="bg-purple-600 hover:bg-purple-700">
                  Set Budget
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Financial Summary Chart */}
      <Card className="border-none shadow-sm bg-white/50 backdrop-blur-sm">
        <CardContent className="p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-6">Financial Summary</h2>
          <p className="text-sm text-gray-500 mb-6">
            Stacked bars show expenses by category. The green line shows your income.
            The gap between them indicates your savings (or overspending).
          </p>
          <DashboardSummaryChart data={chartData} />
        </CardContent>
      </Card>

      {/* Recent Transactions */}
      <Card className="border-none shadow-sm bg-white/50 backdrop-blur-sm">
        <CardContent className="p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-6">Recent Transactions</h2>
          {stats.recent_transactions.length === 0 ? (
            <div className="text-center py-12 text-gray-500 bg-gray-50/50 rounded-xl border border-dashed border-gray-200">
              No transactions yet. Add income or expenses to get started.
            </div>
          ) : (
            <div className="space-y-3">
              {stats.recent_transactions.map((tx) => (
                <div
                  key={tx.id}
                  className="flex justify-between items-center p-4 bg-white rounded-xl border border-gray-100 hover:shadow-sm transition-all duration-200 group"
                >
                  <div className="flex items-center gap-4">
                    <div className={`p-2 rounded-lg ${tx.type === 'income' ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'
                      }`}>
                      {tx.type === 'income' ? (
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>
                      ) : (
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline><polyline points="17 18 23 18 23 12"></polyline></svg>
                      )}
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900">{tx.category}</div>
                      <div className="flex items-center gap-2 text-sm text-gray-500">
                        <span>{format(new Date(tx.date), 'MMM dd, yyyy')}</span>
                        {tx.note && (
                          <>
                            <span>•</span>
                            <span>{tx.note}</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div
                      className={`font-bold text-lg ${tx.type === 'income' ? 'text-green-600' : 'text-red-600'
                        }`}
                    >
                      {tx.type === 'income' ? '+' : '-'}₹{Number(tx.amount).toLocaleString()}
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setDeleteId(tx.id)}
                      className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-600 hover:bg-red-50 transition-all"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <ConfirmationModal
        isOpen={!!deleteId}
        onClose={() => setDeleteId(null)}
        onConfirm={confirmDelete}
        title="Delete Transaction"
        message="Are you sure you want to delete this transaction? This action cannot be undone."
        confirmText="Delete"
        variant="danger"
      />
    </div>
  );
}

