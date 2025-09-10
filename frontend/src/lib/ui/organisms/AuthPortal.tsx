/**
 * AuthPortal Component - Authentication Organism
 * Complete authentication portal with navigation between different auth flows
 */

import React, { useState, useEffect } from 'react';
import { AuthCard, cn } from '@/lib/ui/atoms';
import { 
  LoginForm, 
  RegisterForm, 
  ForgotPasswordForm, 
  EmailVerificationForm 
} from '@/lib/ui/molecules';
import { useAuth } from '@/lib/auth';
import type { ApiError } from '@/types/auth';

// Auth flow types
type AuthFlow = 
  | 'login' 
  | 'register' 
  | 'forgot-password' 
  | 'verify-email' 
  | 'reset-password';

// Auth portal props
export interface AuthPortalProps {
  initialFlow?: AuthFlow;
  showLogo?: boolean;
  logoSrc?: string;
  logoAlt?: string;
  onAuthSuccess?: () => void;
  onAuthError?: (error: ApiError) => void;
  className?: string;
  // Customization props
  allowRegistration?: boolean;
  allowPasswordReset?: boolean;
  showRememberMe?: boolean;
  requireEmailVerification?: boolean;
  requirePhoneNumber?: boolean;
  showPasswordStrength?: boolean;
}

// Flow configurations
const flowConfigs = {
  login: {
    title: 'Welcome back',
    description: 'Sign in to your account to continue',
  },
  register: {
    title: 'Create your account',
    description: 'Join us today and get started',
  },
  'forgot-password': {
    title: 'Reset your password',
    description: 'Enter your email to receive reset instructions',
  },
  'verify-email': {
    title: 'Verify your email',
    description: 'Check your inbox for the verification link',
  },
  'reset-password': {
    title: 'Set new password',
    description: 'Enter your new password below',
  },
};

export const AuthPortal: React.FC<AuthPortalProps> = ({
  initialFlow = 'login',
  showLogo = true,
  logoSrc,
  logoAlt = 'Logo',
  onAuthSuccess,
  onAuthError,
  className,
  allowRegistration = true,
  allowPasswordReset = true,
  showRememberMe = true,
  requireEmailVerification = true,
  requirePhoneNumber = false,
  showPasswordStrength = true,
}) => {
  const [currentFlow, setCurrentFlow] = useState<AuthFlow>(initialFlow);
  const [pendingEmail, setPendingEmail] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const { error, clearError, isAuthenticated } = useAuth();

  // Handle successful authentication
  useEffect(() => {
    if (isAuthenticated && onAuthSuccess) {
      onAuthSuccess();
    }
  }, [isAuthenticated, onAuthSuccess]);

  // Clear errors when flow changes
  useEffect(() => {
    clearError();
  }, [currentFlow, clearError]);

  const handleSuccess = async (data: any) => {
    setIsLoading(false);
    
    // Handle different success scenarios based on the current flow
    switch (currentFlow) {
      case 'login':
        // User is now authenticated, will trigger useEffect above
        break;
        
      case 'register':
        if (requireEmailVerification && data.verification_required) {
          setPendingEmail(data.email);
          setCurrentFlow('verify-email');
        } else {
          // Registration complete without verification
          onAuthSuccess?.();
        }
        break;
        
      case 'forgot-password':
        // Stay on the same screen, form will show success state
        break;
        
      case 'verify-email':
        // Email verified, can now login
        setCurrentFlow('login');
        break;
        
      default:
        break;
    }
  };

  const handleError = (error: ApiError) => {
    setIsLoading(false);
    onAuthError?.(error);
  };

  const handleFlowNavigation = (flow: AuthFlow) => {
    setCurrentFlow(flow);
    clearError();
  };

  const renderContent = () => {
    switch (currentFlow) {
      case 'login':
        return (
          <LoginForm
            onSuccess={handleSuccess}
            onError={handleError}
            isLoading={isLoading}
            showRememberMe={showRememberMe}
            showForgotPassword={allowPasswordReset}
            onForgotPassword={() => handleFlowNavigation('forgot-password')}
            onRegister={allowRegistration ? () => handleFlowNavigation('register') : undefined}
          />
        );

      case 'register':
        return (
          <RegisterForm
            onSuccess={handleSuccess}
            onError={handleError}
            isLoading={isLoading}
            onLogin={() => handleFlowNavigation('login')}
            requirePhoneNumber={requirePhoneNumber}
            showPasswordStrength={showPasswordStrength}
          />
        );

      case 'forgot-password':
        return (
          <ForgotPasswordForm
            onSuccess={handleSuccess}
            onError={handleError}
            isLoading={isLoading}
            onBackToLogin={() => handleFlowNavigation('login')}
          />
        );

      case 'verify-email':
        return (
          <EmailVerificationForm
            email={pendingEmail}
            onSuccess={handleSuccess}
            onError={handleError}
            isLoading={isLoading}
          />
        );

      default:
        return null;
    }
  };

  const config = flowConfigs[currentFlow];

  return (
    <div className={cn('w-full max-w-md mx-auto', className)}>
      <AuthCard
        title={config.title}
        description={config.description}
        showLogo={showLogo}
        logoSrc={logoSrc}
        logoAlt={logoAlt}
        className="animate-fade-in"
      >
        {renderContent()}
      </AuthCard>

      {/* Footer Links */}
      <div className="mt-8 text-center space-y-4">
        {/* Flow Navigation */}
        <div className="flex items-center justify-center gap-4 text-sm">
          {currentFlow !== 'login' && (
            <button
              onClick={() => handleFlowNavigation('login')}
              className="text-text-on-surface-variant hover:text-text-on-surface transition-colors"
              disabled={isLoading}
            >
              Sign In
            </button>
          )}
          
          {currentFlow !== 'register' && allowRegistration && (
            <button
              onClick={() => handleFlowNavigation('register')}
              className="text-text-on-surface-variant hover:text-text-on-surface transition-colors"
              disabled={isLoading}
            >
              Sign Up
            </button>
          )}
        </div>

        {/* Help Links */}
        <div className="text-xs text-text-on-surface-variant space-y-2">
          <div className="flex items-center justify-center gap-4">
            <a 
              href="/help" 
              className="hover:text-text-on-surface transition-colors"
              target="_blank"
              rel="noopener noreferrer"
            >
              Help Center
            </a>
            <span>•</span>
            <a 
              href="/contact" 
              className="hover:text-text-on-surface transition-colors"
              target="_blank"
              rel="noopener noreferrer"
            >
              Contact Support
            </a>
          </div>
          
          <div className="flex items-center justify-center gap-4">
            <a 
              href="/privacy" 
              className="hover:text-text-on-surface transition-colors"
              target="_blank"
              rel="noopener noreferrer"
            >
              Privacy Policy
            </a>
            <span>•</span>
            <a 
              href="/terms" 
              className="hover:text-text-on-surface transition-colors"
              target="_blank"
              rel="noopener noreferrer"
            >
              Terms of Service
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

// Preset configurations for different use cases
export const AuthPortalPresets = {
  // Medical/Healthcare application
  medical: {
    showLogo: true,
    allowRegistration: false, // Often restricted in medical settings
    requireEmailVerification: true,
    requirePhoneNumber: true,
    showPasswordStrength: true,
    showRememberMe: false, // Security requirement
  },

  // Standard business application
  business: {
    showLogo: true,
    allowRegistration: true,
    requireEmailVerification: true,
    requirePhoneNumber: false,
    showPasswordStrength: true,
    showRememberMe: true,
  },

  // Consumer application
  consumer: {
    showLogo: true,
    allowRegistration: true,
    requireEmailVerification: false,
    requirePhoneNumber: false,
    showPasswordStrength: false,
    showRememberMe: true,
  },

  // High-security application
  security: {
    showLogo: true,
    allowRegistration: false,
    requireEmailVerification: true,
    requirePhoneNumber: true,
    showPasswordStrength: true,
    showRememberMe: false,
  },
} as const;

// Convenience components for common use cases
export const MedicalAuthPortal: React.FC<Omit<AuthPortalProps, keyof typeof AuthPortalPresets.medical>> = (props) => (
  <AuthPortal {...AuthPortalPresets.medical} {...props} />
);

export const BusinessAuthPortal: React.FC<Omit<AuthPortalProps, keyof typeof AuthPortalPresets.business>> = (props) => (
  <AuthPortal {...AuthPortalPresets.business} {...props} />
);

export const ConsumerAuthPortal: React.FC<Omit<AuthPortalProps, keyof typeof AuthPortalPresets.consumer>> = (props) => (
  <AuthPortal {...AuthPortalPresets.consumer} {...props} />
);

export const SecurityAuthPortal: React.FC<Omit<AuthPortalProps, keyof typeof AuthPortalPresets.security>> = (props) => (
  <AuthPortal {...AuthPortalPresets.security} {...props} />
);