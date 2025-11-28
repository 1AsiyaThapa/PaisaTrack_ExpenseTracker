'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { SearchParamsWrapper } from '../../components/common/SearchParamsWrapper';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { Mail, Lock, User, ArrowRight, AlertCircle } from 'lucide-react';
import { AuthLayout } from '../../components/layout/AuthLayout';
import { FormInput } from '../../components/forms/FormInput';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { GoogleOAuthButton } from '../../components/auth/GoogleOAuthButton';
import { PageTransition } from '../../components/common/PageTransition';
import { useForm } from '../../hooks/useForm';
import { useAuth } from '../../contexts/AuthContext';
import { validateEmail, validatePassword, validateName } from '../../lib/utils';

// Component to handle search params without causing render issues
function SignupContent({ searchParams, onAuthError }: { 
  searchParams: URLSearchParams; 
  onAuthError: (error: string | null) => void;
}) {
  useEffect(() => {
    const error = searchParams.get('error');
    if (error === 'auth_failed') {
      onAuthError('Authentication failed. Please try again.');
    }
  }, [searchParams, onAuthError]);

  return null; // This component only handles side effects
}

export default function Signup() {
  const { signup, loading } = useAuth();
  const [authError, setAuthError] = useState<string | null>(null);
  
  const [formState, formActions] = useForm<{
    name: string;
    email: string;
    password: string;
    confirmPassword: string;
  }>({
    initialValues: { 
      name: '',
      email: '',
      password: '',
      confirmPassword: '',
    },
    validationRules: {
      name: [validateName],
      email: [validateEmail],
      password: [validatePassword],
      // confirmPassword handled manually
    },
  });
  
  const { values, errors } = formState;
  const { handleChange, handleSubmit, setFieldError } = formActions;

  // Manual validation for confirmPassword
  useEffect(() => {
    if (values.confirmPassword) {
      if (!values.confirmPassword) {
        setFieldError('confirmPassword', 'Please confirm your password');
      } else if (values.password && values.confirmPassword !== values.password) {
        setFieldError('confirmPassword', 'Passwords do not match');
      } else {
        setFieldError('confirmPassword', '');
      }
    }
  }, [values.password, values.confirmPassword, setFieldError]);


  const onSubmit = async (formValues: Record<string, string>) => {
    // Validate passwords match
    if (formValues.password !== formValues.confirmPassword) {
      setFieldError('confirmPassword', 'Passwords do not match');
      return;
    }

    try {
      await signup(
        formValues.name,
        formValues.email,
        formValues.password
      );
    } catch (error: unknown) {
      // Handle signup errors
      const errorMessage = error instanceof Error ? error.message : 'Signup failed. Please try again.';
      
      // Check if it's an "email already exists" error
      if (errorMessage.includes('already exists')) {
        setFieldError('email', 'An account with this email already exists. Please try logging in instead.');
      } else {
        setFieldError('email', errorMessage);
      }
    }
  };

  const handleGoogleSuccess = () => {
    // Google signup initiated successfully
  };

  const handleGoogleError = (error: string) => {
    setAuthError(error);
  };

  return (
    <PageTransition>
      <SearchParamsWrapper>
        {(searchParams) => (
          <>
            <SignupContent searchParams={searchParams} onAuthError={setAuthError} />
            <AuthLayout
              title="Create your account"
              subtitle="Join PaisaTrack and start your journey"
            >
              <Card className="backdrop-blur-sm bg-white/80 border border-gray-200 shadow-xl">
                <div className="p-8">
                  {/* Auth Error Display */}
                  {authError && (
                    <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-600 text-sm">
                      <AlertCircle className="h-4 w-4" />
                      {authError}
                    </div>
                  )}

                  {/* Google OAuth Button */}
                  <div className="mb-6">
                    <GoogleOAuthButton
                      onSuccess={handleGoogleSuccess}
                      onError={handleGoogleError}
                      disabled={loading}
                    />
                  </div>

                  {/* Divider */}
                  <div className="relative mb-6">
                    <div className="absolute inset-0 flex items-center">
                      <span className="w-full border-t" />
                    </div>
                    <div className="relative flex justify-center text-xs uppercase">
                      <span className="bg-white px-2 text-gray-500">
                        Or continue with email
                      </span>
                    </div>
                  </div>

                  {/* Signup Form */}
                  <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">

                    {/* Name Field */}
                    <div className="space-y-2">
                      <label htmlFor="name" className="text-sm font-medium text-gray-700">
                        Full Name
                      </label>
                      <FormInput
                        id="name"
                        type="text"
                        placeholder="Enter your full name"
                        value={values.name}
                        onChange={(e) => handleChange('name', e.target.value)}
                        error={errors.name}
                        icon={User}
                        disabled={loading}
                      />
                    </div>

                    {/* Email Field */}
                    <div className="space-y-2">
                      <label htmlFor="email" className="text-sm font-medium text-gray-700">
                        Email
                      </label>
                      <FormInput
                        id="email"
                        type="email"
                        placeholder="Enter your email"
                        value={values.email}
                        onChange={(e) => handleChange('email', e.target.value)}
                        error={errors.email}
                        icon={Mail}
                        disabled={loading}
                      />
                    </div>

                    {/* Password Field */}
                    <div className="space-y-2">
                      <label htmlFor="password" className="text-sm font-medium text-gray-700">
                        Password
                      </label>
                      <FormInput
                        id="password"
                        type="password"
                        placeholder="Create a password"
                        value={values.password}
                        onChange={(e) => handleChange('password', e.target.value)}
                        error={errors.password}
                        icon={Lock}
                        disabled={loading}
                      />
                    </div>

                    {/* Confirm Password Field */}
                    <div className="space-y-2">
                      <label htmlFor="confirmPassword" className="text-sm font-medium text-gray-700">
                        Confirm Password
                      </label>
                      <FormInput
                        id="confirmPassword"
                        type="password"
                        placeholder="Confirm your password"
                        value={values.confirmPassword}
                        onChange={(e) => handleChange('confirmPassword', e.target.value)}
                        error={errors.confirmPassword}
                        icon={Lock}
                        disabled={loading}
                      />
                    </div>

                    <Button
                      type="submit"
                      className="w-full"
                      disabled={loading}
                    >
                      {loading ? (
                        <LoadingSpinner size="sm" className="mr-2" />
                      ) : (
                        <ArrowRight className="mr-2 h-4 w-4" />
                      )}
                      {loading ? 'Creating account...' : 'Create Account'}
                    </Button>
                  </form>

                  {/* Sign In Link */}
                  <div className="mt-6 text-center">
                    <p className="text-sm text-gray-600">
                      Already have an account?{' '}
                      <Link
                        href="/login"
                        className="text-red-600 hover:text-red-500 font-medium transition-colors"
                      >
                        Sign in
                      </Link>
                    </p>
                  </div>

                  {/* Back to Home Link */}
                  <div className="mt-4 text-center">
                    <Link
                      href="/"
                      className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
                    >
                      ← Back to home
                    </Link>
                  </div>
                </div>
              </Card>
            </AuthLayout>
          </>
        )}
      </SearchParamsWrapper>
    </PageTransition>
  );
}