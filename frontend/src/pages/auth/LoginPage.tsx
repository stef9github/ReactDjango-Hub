/**
 * LoginPage - Authentication Page
 * Complete login page with responsive design and error handling
 */

import React, { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AuthPortal } from '@/lib/ui/organisms/AuthPortal';
import { useAuth, useGuestOnly } from '@/lib/auth';
import { Alert } from '@/lib/ui/atoms';
import type { ApiError } from '@/types/auth';

export const LoginPage: React.FC = () => {
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
    console.error('Authentication error:', error);
  };

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-surface-background">
      {/* Background Pattern */}
      <div className="absolute inset-0 bg-grid-pattern opacity-5 pointer-events-none" />
      
      <div className="relative z-10">
        {/* Header */}
        <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-8">
          <h1 className="text-3xl font-bold text-text-on-background">
            ReactDjango Hub
          </h1>
          <p className="mt-2 text-text-on-surface-variant">
            Secure authentication portal
          </p>
        </div>

        {/* Global Error Alert */}
        {error && (
          <div className="max-w-md mx-auto mb-6 px-4">
            <Alert
              variant="error"
              title="Authentication Error"
              description={error}
              closeable
              onClose={() => {/* Clear error */}}
            />
          </div>
        )}

        {/* Auth Portal */}
        <div className="px-4">
          <AuthPortal
            initialFlow="login"
            onAuthSuccess={handleAuthSuccess}
            onAuthError={handleAuthError}
            showLogo={false} // We show logo in header instead
            allowRegistration={true}
            allowPasswordReset={true}
            showRememberMe={true}
          />
        </div>

        {/* Footer */}
        <footer className="mt-12 text-center text-xs text-text-on-surface-variant">
          <div className="max-w-md mx-auto px-4">
            <p>
              © {new Date().getFullYear()} ReactDjango Hub. All rights reserved.
            </p>
            <p className="mt-2">
              Secure authentication powered by modern web standards.
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default LoginPage;