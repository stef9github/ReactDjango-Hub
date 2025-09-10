/**
 * RegisterPage - Authentication Page
 * Complete registration page with responsive design
 */

import React, { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AuthPortal } from '@/lib/ui/organisms/AuthPortal';
import { useAuth, useGuestOnly } from '@/lib/auth';
import { Alert } from '@/lib/ui/atoms';
import type { ApiError } from '@/types/auth';

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, error } = useGuestOnly();
  
  // Get redirect path from location state or default to dashboard
  const redirectPath = (location.state as any)?.from?.pathname || '/dashboard';
  
  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate(redirectPath, { replace: true });
    }
  }, [isAuthenticated, navigate, redirectPath]);

  const handleAuthSuccess = () => {
    navigate(redirectPath, { replace: true });
  };

  const handleAuthError = (error: ApiError) => {
    console.error('Registration error:', error);
  };

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-surface-background">
      {/* Background Pattern */}
      <div className="absolute inset-0 bg-grid-pattern opacity-5 pointer-events-none" />
      
      <div className="relative z-10">
        {/* Header */}
        <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-8">
          <h1 className="text-3xl font-bold text-text-on-background">
            Join ReactDjango Hub
          </h1>
          <p className="mt-2 text-text-on-surface-variant">
            Create your account to get started
          </p>
        </div>

        {/* Global Error Alert */}
        {error && (
          <div className="max-w-md mx-auto mb-6 px-4">
            <Alert
              variant="error"
              title="Registration Error"
              description={error}
              closeable
              onClose={() => {/* Clear error */}}
            />
          </div>
        )}

        {/* Auth Portal */}
        <div className="px-4">
          <AuthPortal
            initialFlow="register"
            onAuthSuccess={handleAuthSuccess}
            onAuthError={handleAuthError}
            showLogo={false} // We show logo in header instead
            allowRegistration={true}
            requireEmailVerification={true}
            requirePhoneNumber={false}
            showPasswordStrength={true}
          />
        </div>

        {/* Registration Benefits */}
        <div className="mt-12 max-w-md mx-auto px-4">
          <div className="bg-surface-surface-variant rounded-theme-lg p-6">
            <h3 className="font-semibold text-text-on-surface mb-4">
              Why join us?
            </h3>
            <ul className="space-y-3 text-sm text-text-on-surface-variant">
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-semantic-success-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>Secure authentication with enterprise-grade security</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-semantic-success-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>Access to powerful tools and integrations</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-semantic-success-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>24/7 support and comprehensive documentation</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-semantic-success-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>Free to start, scale as you grow</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-12 text-center text-xs text-text-on-surface-variant">
          <div className="max-w-md mx-auto px-4">
            <p>
              © {new Date().getFullYear()} ReactDjango Hub. All rights reserved.
            </p>
            <p className="mt-2">
              By registering, you agree to our Terms of Service and Privacy Policy.
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default RegisterPage;