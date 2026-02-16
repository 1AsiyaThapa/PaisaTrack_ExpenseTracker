'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { userService, categoryService } from '@/services/api';
import { Category, CategoryCreate } from '@/types';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { IconPicker, ICON_MAP } from '@/components/ui/IconPicker';
import { Trash2, Edit2, Plus, Save, X } from 'lucide-react';

import { ConfirmationModal } from '@/components/ui/ConfirmationModal';

export default function ProfilePage() {
    const { user } = useAuth(); // Re-login might be needed to update context if name changes
    const [activeTab, setActiveTab] = useState<'account' | 'categories'>('account');

    // Account State
    const [profileData, setProfileData] = useState({
        name: user?.name || '',
        password: '',
        new_password: '',
    });
    const [profileLoading, setProfileLoading] = useState(false);

    // Categories State
    const [categories, setCategories] = useState<Category[]>([]);
    const [categoryLoading, setCategoryLoading] = useState(true);
    const [editingCategory, setEditingCategory] = useState<Category | null>(null);
    const [isAddingCategory, setIsAddingCategory] = useState(false);
    const [newCategory, setNewCategory] = useState<CategoryCreate>({
        name: '',
        type: 'expense',
        icon: 'Wallet',
        color: '#000000'
    });

    // Delete Confirmation State
    const [deleteId, setDeleteId] = useState<string | null>(null);

    useEffect(() => {
        if (activeTab === 'categories') {
            loadCategories();
        }
    }, [activeTab]);

    const loadCategories = async () => {
        try {
            setCategoryLoading(true);
            const data = await categoryService.getCategories();
            setCategories(data);
        } catch (error) {
            console.error('Failed to load categories', error);
        } finally {
            setCategoryLoading(false);
        }
    };

    const handleProfileUpdate = async (e: React.FormEvent) => {
        e.preventDefault();
        setProfileLoading(true);
        try {
            await userService.updateProfile({
                name: profileData.name,
                password: profileData.password || undefined,
                new_password: profileData.new_password || undefined,
            });
            alert('Profile updated successfully');
            window.location.reload();
        } catch (error) {
            console.error('Profile update failed', error);
            alert('Failed to update profile');
        } finally {
            setProfileLoading(false);
        }
    };

    const handleCreateCategory = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await categoryService.createCategory(newCategory);
            setIsAddingCategory(false);
            setNewCategory({ name: '', type: 'expense', icon: 'Wallet', color: '#000000' });
            loadCategories();
        } catch (error) {
            console.error('Failed to create category', error);
            alert('Failed to create category');
        }
    };

    const handleUpdateCategory = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!editingCategory) return;
        try {
            await categoryService.updateCategory(editingCategory.id, {
                name: editingCategory.name,
                type: editingCategory.type,
                icon: editingCategory.icon,
                color: editingCategory.color
            });
            setEditingCategory(null);
            loadCategories();
        } catch (error) {
            console.error('Failed to update category', error);
            alert('Failed to update category');
        }
    };

    const confirmDeleteCategory = async () => {
        if (!deleteId) return;
        try {
            await categoryService.deleteCategory(deleteId);
            loadCategories();
        } catch (error) {
            console.error('Failed to delete category', error);
        } finally {
            setDeleteId(null);
        }
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">Profile & Settings</h1>
                <p className="text-gray-500 mt-1">Manage your account and preferences</p>
            </div>

            {/* Tabs */}
            <div className="flex gap-4 border-b border-gray-200 pb-1">
                <button
                    className={`pb-3 px-4 font-medium transition-colors ${activeTab === 'account'
                        ? 'border-b-2 border-red-600 text-red-600'
                        : 'text-gray-500 hover:text-gray-700'
                        }`}
                    onClick={() => setActiveTab('account')}
                >
                    Account Settings
                </button>
                <button
                    className={`pb-3 px-4 font-medium transition-colors ${activeTab === 'categories'
                        ? 'border-b-2 border-red-600 text-red-600'
                        : 'text-gray-500 hover:text-gray-700'
                        }`}
                    onClick={() => setActiveTab('categories')}
                >
                    Categories
                </button>
            </div>

            {/* Account Settings Tab */}
            {activeTab === 'account' && (
                <Card>
                    <CardContent className="p-6">
                        <form onSubmit={handleProfileUpdate} className="space-y-6 max-w-md">
                            <div className="space-y-4">
                                <Input
                                    label="Full Name"
                                    value={profileData.name}
                                    onChange={(e) => setProfileData({ ...profileData, name: e.target.value })}
                                />
                            </div>

                            <div className="pt-6 border-t border-gray-200 space-y-4">
                                <h3 className="text-sm font-semibold text-gray-900">Change Password</h3>
                                <div className="space-y-4">
                                    <Input
                                        label="Current Password"
                                        type="password"
                                        value={profileData.password}
                                        onChange={(e) => setProfileData({ ...profileData, password: e.target.value })}
                                        placeholder="Leave blank to keep current"
                                    />
                                    <Input
                                        label="New Password"
                                        type="password"
                                        value={profileData.new_password}
                                        onChange={(e) => setProfileData({ ...profileData, new_password: e.target.value })}
                                        placeholder="Leave blank to keep current"
                                    />
                                </div>
                            </div>

                            <div className="pt-2">
                                <Button type="submit" disabled={profileLoading}>
                                    {profileLoading ? 'Saving...' : 'Save Changes'}
                                </Button>
                            </div>
                        </form>
                    </CardContent>
                </Card>
            )}

            {/* Categories Tab */}
            {activeTab === 'categories' && (
                <div className="space-y-6">
                    <div className="flex justify-between items-center">
                        <h2 className="text-lg font-semibold text-gray-900">Manage Categories</h2>
                        <Button onClick={() => setIsAddingCategory(true)} size="sm">
                            <Plus className="w-4 h-4 mr-2" /> Add Category
                        </Button>
                    </div>

                    {/* Add Category Form */}
                    {isAddingCategory && (
                        <Card className="bg-gray-50/50 border-dashed border-gray-300">
                            <CardContent className="p-6">
                                <form onSubmit={handleCreateCategory} className="space-y-4">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <Input
                                            label="Category Name"
                                            value={newCategory.name}
                                            onChange={(e) => setNewCategory({ ...newCategory, name: e.target.value })}
                                            required
                                        />
                                        <div className="space-y-1">
                                            <label className="block text-sm font-medium text-gray-700">Type</label>
                                            <select
                                                className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                                                value={newCategory.type}
                                                onChange={(e) => setNewCategory({ ...newCategory, type: e.target.value as 'income' | 'expense' })}
                                            >
                                                <option value="income">Income</option>
                                                <option value="expense">Expense</option>
                                            </select>
                                        </div>
                                        <div className="space-y-1">
                                            <label className="block text-sm font-medium text-gray-700">Icon</label>
                                            <IconPicker
                                                selectedIcon={newCategory.icon}
                                                onSelect={(icon) => setNewCategory({ ...newCategory, icon })}
                                            />
                                        </div>
                                    </div>
                                    <div className="flex gap-3 pt-2">
                                        <Button type="submit" size="sm">Create</Button>
                                        <Button type="button" variant="ghost" size="sm" onClick={() => setIsAddingCategory(false)}>
                                            Cancel
                                        </Button>
                                    </div>
                                </form>
                            </CardContent>
                        </Card>
                    )}

                    {/* Categories List */}
                    {categoryLoading ? (
                        <Card>
                            <CardContent className="p-6">
                                <div className="text-center py-12 text-gray-500">Loading categories...</div>
                            </CardContent>
                        </Card>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Income Categories */}
                            <Card>
                                <CardContent className="p-6">
                                    <h3 className="font-semibold text-green-600 mb-6 flex items-center gap-2">
                                        Income Categories
                                    </h3>
                                    {categories.filter(c => c.type === 'income').length === 0 ? (
                                        <div className="text-center py-8 text-gray-500 text-sm">
                                            No income categories yet. Add one above.
                                        </div>
                                    ) : (
                                        <div className="space-y-2">
                                            {categories.filter(c => c.type === 'income').map(category => (
                                                <div key={category.id} className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg group transition-colors">
                                                    {editingCategory?.id === category.id ? (
                                                        <form onSubmit={handleUpdateCategory} className="flex-1 flex gap-2 items-center">
                                                            <Input
                                                                value={editingCategory.name}
                                                                onChange={(e) => setEditingCategory({ ...editingCategory, name: e.target.value })}
                                                                className="h-9 flex-1"
                                                            />
                                                            <IconPicker
                                                                selectedIcon={editingCategory.icon}
                                                                onSelect={(icon) => setEditingCategory({ ...editingCategory, icon })}
                                                                className="w-32"
                                                            />
                                                            <Button type="submit" size="sm" variant="ghost">
                                                                <Save className="w-4 h-4" />
                                                            </Button>
                                                            <Button type="button" size="sm" variant="ghost" onClick={() => setEditingCategory(null)}>
                                                                <X className="w-4 h-4" />
                                                            </Button>
                                                        </form>
                                                    ) : (
                                                        <>
                                                            <div className="flex items-center gap-3">
                                                                <div className="p-2 bg-green-50 rounded-lg text-green-600">
                                                                    {(() => {
                                                                        const Icon = ICON_MAP[category.icon] || ICON_MAP['Wallet'];
                                                                        return <Icon className="w-4 h-4" />;
                                                                    })()}
                                                                </div>
                                                                <span className="font-medium text-gray-900">{category.name}</span>
                                                            </div>
                                                            <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                <Button size="sm" variant="ghost" onClick={() => setEditingCategory(category)}>
                                                                    <Edit2 className="w-4 h-4 text-gray-500" />
                                                                </Button>
                                                                <Button size="sm" variant="ghost" onClick={() => setDeleteId(category.id)}>
                                                                    <Trash2 className="w-4 h-4 text-red-500" />
                                                                </Button>
                                                            </div>
                                                        </>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </CardContent>
                            </Card>

                            {/* Expense Categories */}
                            <Card>
                                <CardContent className="p-6">
                                    <h3 className="font-semibold text-red-600 mb-6 flex items-center gap-2">
                                        Expense Categories
                                    </h3>
                                    {categories.filter(c => c.type === 'expense').length === 0 ? (
                                        <div className="text-center py-8 text-gray-500 text-sm">
                                            No expense categories yet. Add one above.
                                        </div>
                                    ) : (
                                        <div className="space-y-2">
                                            {categories.filter(c => c.type === 'expense').map(category => (
                                                <div key={category.id} className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg group transition-colors">
                                                    {editingCategory?.id === category.id ? (
                                                        <form onSubmit={handleUpdateCategory} className="flex-1 flex gap-2 items-center">
                                                            <Input
                                                                value={editingCategory.name}
                                                                onChange={(e) => setEditingCategory({ ...editingCategory, name: e.target.value })}
                                                                className="h-9 flex-1"
                                                            />
                                                            <IconPicker
                                                                selectedIcon={editingCategory.icon}
                                                                onSelect={(icon) => setEditingCategory({ ...editingCategory, icon })}
                                                                className="w-32"
                                                            />
                                                            <Button type="submit" size="sm" variant="ghost">
                                                                <Save className="w-4 h-4" />
                                                            </Button>
                                                            <Button type="button" size="sm" variant="ghost" onClick={() => setEditingCategory(null)}>
                                                                <X className="w-4 h-4" />
                                                            </Button>
                                                        </form>
                                                    ) : (
                                                        <>
                                                            <div className="flex items-center gap-3">
                                                                <div className="p-2 bg-red-50 rounded-lg text-red-600">
                                                                    {(() => {
                                                                        const Icon = ICON_MAP[category.icon] || ICON_MAP['CreditCard'];
                                                                        return <Icon className="w-4 h-4" />;
                                                                    })()}
                                                                </div>
                                                                <span className="font-medium text-gray-900">{category.name}</span>
                                                            </div>
                                                            <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                <Button size="sm" variant="ghost" onClick={() => setEditingCategory(category)}>
                                                                    <Edit2 className="w-4 h-4 text-gray-500" />
                                                                </Button>
                                                                <Button size="sm" variant="ghost" onClick={() => setDeleteId(category.id)}>
                                                                    <Trash2 className="w-4 h-4 text-red-500" />
                                                                </Button>
                                                            </div>
                                                        </>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </div>
                    )}
                </div>
            )}

            <ConfirmationModal
                isOpen={!!deleteId}
                onClose={() => setDeleteId(null)}
                onConfirm={confirmDeleteCategory}
                title="Delete Category"
                message="Are you sure you want to delete this category? This might affect your reports."
                confirmText="Delete"
                variant="danger"
            />
        </div>
    );
}
