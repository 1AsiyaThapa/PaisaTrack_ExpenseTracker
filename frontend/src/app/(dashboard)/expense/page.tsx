'use client';

import { transactionService } from '@/services/api';
import { Transaction, ReceiptItem } from '@/types';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useEffect, useState, useRef } from 'react';
import { format } from 'date-fns';
import { Upload, Sparkles, X, CheckCircle2 } from 'lucide-react';
import Image from 'next/image';

import { ConfirmationModal } from '@/components/ui/ConfirmationModal';
import { CategorySelect } from '@/components/ui/CategorySelect';
import { ExpenseBarChart } from '@/components/charts/ExpenseBarChart';

export default function ExpensePage() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [chartData, setChartData] = useState<Array<{ category: string; total: number }>>([]);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    amount: '',
    category: '',
    note: '',
    date: format(new Date(), 'yyyy-MM-dd'),
  });
  const [submitting, setSubmitting] = useState(false);
  const [receiptUrl, setReceiptUrl] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);
  const [scanError, setScanError] = useState<string | null>(null);

  // Delete Confirmation State
  const [deleteId, setDeleteId] = useState<string | null>(null);

  // Multi-Item Receipt State
  const [suggestedTransactions, setSuggestedTransactions] = useState<ReceiptItem[]>([]);
  const [receiptDate, setReceiptDate] = useState<string>('');
  const [editingIndex, setEditingIndex] = useState<number | null>(null);

  const updateSuggestedItem = (index: number, field: keyof ReceiptItem, value: string | number) => {
    setSuggestedTransactions((prev) => {
      const newItems = [...prev];
      newItems[index] = { ...newItems[index], [field]: value };
      return newItems;
    });
  };

  useEffect(() => {
    loadTransactions();
    loadChartData();
  }, []);

  const loadTransactions = async () => {
    try {
      const data = await transactionService.getTransactions('expense');
      setTransactions(data);
    } catch (error) {
      console.error('Error loading transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadChartData = async () => {
    try {
      const response = await transactionService.getCategoryProportions('expense');
      setChartData(response.data);
    } catch (error) {
      console.error('Error loading chart data:', error);
    }
  };

  const handleFileSelect = (file: File) => {
    if (!file.type.startsWith('image/')) {
      setScanError('Please select an image file');
      return;
    }

    setSelectedFile(file);
    setScanError(null);

    const reader = new FileReader();
    reader.onloadend = () => {
      setPreviewUrl(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleScan = async () => {
    if (!selectedFile) return;

    setScanning(true);
    setScanError(null);

    try {
      const result = await transactionService.scanReceipt(selectedFile);
      setReceiptUrl(result.receipt_url);
      setReceiptDate(result.date);

      // Instead of setting one form, we set the list of suggestions
      setSuggestedTransactions(result.suggested_transactions);
    } catch (err) {
      setScanError(err instanceof Error ? err.message : 'Failed to scan receipt');
    } finally {
      setScanning(false);
    }
  };

  const handleResetReceipt = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setReceiptUrl(null);
    setScanError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
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
        type: 'expense',
        category: formData.category,
        note: formData.note || undefined,
        date: new Date(formData.date).toISOString(),
        receipt_url: receiptUrl || undefined,
      });
      setFormData({ amount: '', category: '', note: '', date: format(new Date(), 'yyyy-MM-dd') });
      setReceiptUrl(null);
      setSelectedFile(null);
      setPreviewUrl(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      loadTransactions();
      loadChartData();
    } catch (error) {
      console.error('Error creating transaction:', error);
      alert('Failed to add expense');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSaveAllSuggestions = async () => {
    setSubmitting(true);
    try {
      // Loop through all suggestions and create transactions
      await Promise.all(
        suggestedTransactions.map(item =>
          transactionService.createTransaction({
            amount: item.amount,
            type: 'expense',
            category: item.category,
            note: item.item_name + (item.note ? ` (${item.note})` : ''),
            date: new Date(receiptDate).toISOString(),
            receipt_url: receiptUrl || undefined,
          })
        )
      );

      // Clear everything on success
      setSuggestedTransactions([]);
      handleResetReceipt();
      loadTransactions();
      loadChartData();
      alert('All items saved successfully!');
    } catch (error) {
      console.error('Error saving suggestions:', error);
      alert('Failed to save some items');
    } finally {
      setSubmitting(false);
    }
  };

  const confirmDelete = async () => {
    if (!deleteId) return;
    try {
      await transactionService.deleteTransaction(deleteId);
      loadTransactions();
      loadChartData();
    } catch (error) {
      console.error('Error deleting transaction:', error);
    } finally {
      setDeleteId(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center py-20">Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Expenses</h1>
        <p className="text-gray-500 mt-1">Track your spending habits</p>
      </div>

      {/* Receipt Scanner Section */}
      <Card className="mb-6">
        <CardContent>
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <div className="p-2 bg-purple-50 rounded-lg">
              <Sparkles className="w-5 h-5 text-purple-600" />
            </div>
            Receipt Scanner
          </h2>

          {!previewUrl ? (
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-red-400 transition-colors bg-gray-50/50">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="flex flex-col items-center gap-3 mx-auto"
              >
                <div className="p-4 bg-blue-50 rounded-lg">
                  <Upload className="w-8 h-8 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700">Upload Receipt Image</p>
                  <p className="text-xs text-gray-500 mt-1">Click to select an image file</p>
                </div>
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="relative rounded-lg overflow-hidden border border-gray-200 bg-gray-50">
                <Image
                  src={previewUrl}
                  alt="Receipt preview"
                  width={500}
                  height={500}
                  className="w-full h-auto max-h-64 object-contain"
                />
                {receiptUrl && (
                  <div className="absolute top-2 right-2 bg-green-500 text-white px-2 py-1 rounded-md text-xs flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    Ready
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleResetReceipt}
                  className="flex-1"
                >
                  <X className="w-4 h-4 mr-2" />
                  Remove Image
                </Button>
                {!receiptUrl && (
                  <Button
                    type="button"
                    onClick={handleScan}
                    disabled={scanning}
                    className="flex-1"
                  >
                    {scanning ? (
                      <>
                        <LoadingSpinner size="sm" className="mr-2" />
                        Scanning...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 mr-2" />
                        Scan Receipt
                      </>
                    )}
                  </Button>
                )}
              </div>
              {scanning && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center gap-2">
                    <LoadingSpinner size="sm" />
                    <p className="text-sm text-blue-900">AI is reading your receipt...</p>
                  </div>
                </div>
              )}
              {scanError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-800">{scanError}</p>
                </div>
              )}
            </div>
          )}

          {suggestedTransactions.length > 0 && (
            <div className="mt-6 space-y-4 animate-in fade-in slide-in-from-top-4">
              <div className="flex items-center justify-between">
                <h3 className="text-md font-bold text-gray-800">Review Detected Items</h3>
                <span className="text-xs bg-gray-100 px-2 py-1 rounded text-gray-500">
                  Date: {receiptDate}
                </span>
              </div>

              <div className="grid gap-3">
                {suggestedTransactions.map((item, idx) => (
                  <div
                    key={idx}
                    className={`bg-white border border-gray-200 rounded-xl shadow-sm transition-all ${editingIndex === idx ? 'relative z-30 ring-2 ring-blue-100' : 'relative z-10'
                      }`}
                  >
                    {editingIndex === idx ? (
                      /* --- EDIT MODE --- */
                      <div className="p-4 bg-blue-50/50 space-y-4 rounded-xl">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <Input
                            label="Item Name"
                            value={item.item_name}
                            onChange={(e) => updateSuggestedItem(idx, 'item_name', e.target.value)}
                          />
                          <Input
                            label="Amount"
                            type="number"
                            value={item.amount}
                            onChange={(e) => updateSuggestedItem(idx, 'amount', Number(e.target.value))}
                          />
                          <CategorySelect
                            type="expense"
                            value={item.category}
                            onChange={(val) => updateSuggestedItem(idx, 'category', val)}
                          />
                          <Input
                            label="Note (Optional)"
                            value={item.note || ''}
                            onChange={(e) => updateSuggestedItem(idx, 'note', e.target.value)}
                            placeholder="Add a note"
                          />
                        </div>
                        <div className="flex justify-end gap-2">
                          <Button size="sm" variant="ghost" onClick={() => setEditingIndex(null)}>
                            Done
                          </Button>
                        </div>
                      </div>
                    ) : (
                      /* --- DISPLAY MODE --- */
                      <div className="p-4 flex items-center justify-between group">
                        <div className="flex items-center gap-4">
                          <div className="p-2 bg-purple-100 rounded-lg text-purple-700 text-xs font-bold min-w-[80px] text-center">
                            {item.category}
                          </div>
                          <div>
                            <p className="text-sm font-semibold text-gray-900">{item.item_name}</p>
                            {item.note && <p className="text-xs text-gray-500">{item.note}</p>}
                          </div>
                        </div>

                        <div className="flex items-center gap-6">
                          <div className="text-right">
                            <p className="font-bold text-red-600 text-lg">₹{item.amount}</p>
                          </div>
                          <div className="flex flex-col gap-1">
                            <button
                              onClick={() => setEditingIndex(idx)}
                              className="text-xs text-blue-600 hover:underline flex items-center gap-1"
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => setSuggestedTransactions((prev) => prev.filter((_, i) => i !== idx))}
                              className="text-xs text-gray-400 hover:text-red-500 underline"
                            >
                              Remove
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  className="flex-1 bg-green-600 hover:bg-green-700 shadow-md"
                  onClick={handleSaveAllSuggestions}
                  disabled={submitting || editingIndex !== null}
                >
                  {submitting ? 'Saving...' : `Confirm & Save ${suggestedTransactions.length} Expenses`}
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => setSuggestedTransactions([])}
                  className="text-gray-500"
                >
                  Discard All
                </Button>
              </div>
              {editingIndex !== null && (
                <p className="text-xs text-amber-600 text-center">
                  Finish editing the item above to confirm all.
                </p>
              )}
            </div>
          )}

          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileInputChange}
            className="hidden"
          />
        </CardContent>
      </Card>

      {/* Add Expense Form */}
      <Card className="mb-6">
        <CardContent>
          <h2 className="text-lg font-semibold mb-4">Add Expense</h2>
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
              <CategorySelect
                value={formData.category}
                onChange={(value) => setFormData({ ...formData, category: value })}
                type="expense"
                placeholder="Select category"
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
              {submitting ? 'Adding...' : 'Add Expense'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Category Ranking Chart */}
      <Card className="mb-6">
        <CardContent>
          <h2 className="text-lg font-semibold mb-2">Category Ranking</h2>
          <p className="text-sm text-gray-500 mb-6">
            See which categories are eating your budget the most. Sorted from highest to lowest.
          </p>
          <ExpenseBarChart data={chartData} />
        </CardContent>
      </Card>

      {/* Expense List */}
      <Card>
        <CardContent>
          <h2 className="text-lg font-semibold mb-4">All Expenses</h2>
          {transactions.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No expense records yet. Add your first expense above.
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
                    <div className="font-bold text-red-600">
                      -₹{Number(tx.amount).toLocaleString()}
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setDeleteId(tx.id)}
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

      <ConfirmationModal
        isOpen={!!deleteId}
        onClose={() => setDeleteId(null)}
        onConfirm={confirmDelete}
        title="Delete Expense"
        message="Are you sure you want to delete this expense? This action cannot be undone."
        confirmText="Delete"
        variant="danger"
      />
    </div>
  );
}

