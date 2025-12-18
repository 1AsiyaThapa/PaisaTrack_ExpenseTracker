'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { transactionService } from '@/services/api';
import { Transaction } from '@/types';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { format } from 'date-fns';

export default function IncomePage() {
  const router = useRouter();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    amount: '',
    category: '',
    note: '',
    date: format(new Date(), 'yyyy-MM-dd'),
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadTransactions();
  }, []);

  const loadTransactions = async () => {
    try {
      const data = await transactionService.getTransactions('income');
      setTransactions(data);
    } catch (error) {
      console.error('Error loading transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.amount || !formData.category) {
      alert('Please fill in amount and category');
      return;
    }

    setSubmitting(true);
    try {
      await transactionService.createTransaction({
        amount: Number(formData.amount),
        type: 'income',
        category: formData.category,
        note: formData.note || undefined,
        date: new Date(formData.date).toISOString(),
      });
      setFormData({ amount: '', category: '', note: '', date: format(new Date(), 'yyyy-MM-dd') });
      loadTransactions();
    } catch (error) {
      console.error('Error creating transaction:', error);
      alert('Failed to add income');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('Delete this income?')) {
      try {
        await transactionService.deleteTransaction(id);
        loadTransactions();
      } catch (error) {
        console.error('Error deleting transaction:', error);
      }
    }
  };

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50 p-4">
          <div className="max-w-4xl mx-auto">
            <div className="text-center py-20">Loading...</div>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-bold">Income</h1>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => router.push('/dashboard')}>
                Dashboard
              </Button>
              <Button variant="outline" onClick={() => router.push('/expense')}>
                Expense
              </Button>
            </div>
          </div>

          {/* Add Income Form */}
          <Card className="mb-6">
            <CardContent>
              <h2 className="text-lg font-semibold mb-4">Add Income</h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Amount"
                    type="number"
                    step="0.01"
                    value={formData.amount}
                    onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                    placeholder="0.00"
                    required
                  />
                  <Input
                    label="Category"
                    type="text"
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    placeholder="e.g., Salary, Freelance"
                    required
                  />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Date"
                    type="date"
                    value={formData.date}
                    onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                    required
                  />
                  <Input
                    label="Note (Optional)"
                    type="text"
                    value={formData.note}
                    onChange={(e) => setFormData({ ...formData, note: e.target.value })}
                    placeholder="Add a note"
                  />
                </div>
                <Button type="submit" disabled={submitting}>
                  {submitting ? 'Adding...' : 'Add Income'}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Income List */}
          <Card>
            <CardContent>
              <h2 className="text-lg font-semibold mb-4">All Income</h2>
              {transactions.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No income records yet. Add your first income above.
                </div>
              ) : (
                <div className="space-y-2">
                  {transactions.map((tx) => (
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
                        <div className="font-bold text-green-600">
                          +₹{Number(tx.amount).toLocaleString()}
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

