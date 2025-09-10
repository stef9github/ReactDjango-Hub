/**
 * Authentication Context and Provider
 * Centralized auth state management with React Context
 */

import React, { createContext, useContext, useEffect, useReducer, ReactNode } from 'react';
import { apiClient, isApiException, getErrorMessage } from '@/lib/api';
import type {
  AuthState,
  AuthContextType,
  User,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  RegisterResponse,
  MessageResponse,
  PasswordStrength,
} from '@/types/auth';

// Auth action types
type AuthAction =
  | { type: 'AUTH_START' }
  | { type: 'AUTH_SUCCESS'; payload: { user: User; token: string; refreshToken: string } }
  | { type: 'AUTH_ERROR'; payload: string }
  | { type: 'AUTH_LOGOUT' }
  | { type: 'AUTH_CLEAR_ERROR' }
  | { type: 'AUTH_SET_USER'; payload: User }
  | { type: 'AUTH_SET_INITIALIZED'; payload: boolean };

// Initial auth state
const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  token: null,
  refreshToken: null,
  isInitialized: false,
};

// Auth reducer
function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'AUTH_START':
      return {
        ...state,
        isLoading: true,
        error: null,
      };

    case 'AUTH_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        refreshToken: action.payload.refreshToken,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };

    case 'AUTH_ERROR':
      return {
        ...state,
        user: null,
        token: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload,
      };

    case 'AUTH_LOGOUT':
      return {
        ...state,
        user: null,
        token: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      };

    case 'AUTH_CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };

    case 'AUTH_SET_USER':
      return {
        ...state,
        user: action.payload,
      };

    case 'AUTH_SET_INITIALIZED':
      return {
        ...state,
        isInitialized: action.payload,
      };

    default:
      return state;
  }
}

// Password strength checker
function checkPasswordStrength(password: string): PasswordStrength {
  const feedback: string[] = [];
  let score: PasswordStrength['score'] = 0;

  const hasMinLength = password.length >= 8;
  const hasUppercase = /[A-Z]/.test(password);
  const hasLowercase = /[a-z]/.test(password);
  const hasNumbers = /\d/.test(password);
  const hasSpecialChars = /[^A-Za-z0-9]/.test(password);

  // Calculate score
  if (hasMinLength) score++;
  if (hasUppercase) score++;
  if (hasLowercase) score++;
  if (hasNumbers) score++;
  if (hasSpecialChars) score++;

  // Generate feedback
  if (!hasMinLength) feedback.push('Use at least 8 characters');
  if (!hasUppercase) feedback.push('Add uppercase letters');
  if (!hasLowercase) feedback.push('Add lowercase letters');
  if (!hasNumbers) feedback.push('Add numbers');
  if (!hasSpecialChars) feedback.push('Add special characters');

  // Adjust score based on additional criteria
  if (password.length >= 12) score = Math.min(score + 1, 4);
  if (score === 5 && password.length >= 12) score = 4;

  return {
    score: Math.min(score, 4) as PasswordStrength['score'],
    feedback,
    hasMinLength,
    hasUppercase,
    hasLowercase,
    hasNumbers,
    hasSpecialChars,
  };
}

// Auth context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auth provider props
export interface AuthProviderProps {
  children: ReactNode;
  autoInitialize?: boolean;
}

// Auth provider component
export function AuthProvider({ children, autoInitialize = true }: AuthProviderProps) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Initialize auth state on mount
  useEffect(() => {
    if (autoInitialize && !state.isInitialized) {
      initializeAuth();
    }
  }, [autoInitialize, state.isInitialized]);

  // Listen for auth errors from API client
  useEffect(() => {
    const handleAuthError = () => {
      dispatch({ type: 'AUTH_LOGOUT' });
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('auth:error', handleAuthError);
      return () => window.removeEventListener('auth:error', handleAuthError);
    }
  }, []);

  // Initialize auth state from stored tokens
  const initializeAuth = async (): Promise<void> => {
    try {
      // Try to get current user with stored token
      const user = await apiClient.getCurrentUser();
      const token = localStorage.getItem('auth_access_token');
      const refreshToken = localStorage.getItem('auth_refresh_token');

      if (user && token && refreshToken) {
        dispatch({
          type: 'AUTH_SUCCESS',
          payload: { user, token, refreshToken },
        });
      }
    } catch (error) {
      // Token is invalid or expired, clear storage
      localStorage.removeItem('auth_access_token');
      localStorage.removeItem('auth_refresh_token');
    } finally {
      dispatch({ type: 'AUTH_SET_INITIALIZED', payload: true });
    }
  };

  // Login function
  const login = async (credentials: LoginRequest): Promise<TokenResponse> => {
    dispatch({ type: 'AUTH_START' });

    try {
      const response = await apiClient.login(credentials);
      
      dispatch({
        type: 'AUTH_SUCCESS',
        payload: {
          user: response.user,
          token: response.access_token,
          refreshToken: response.refresh_token,
        },
      });

      return response;
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      dispatch({ type: 'AUTH_ERROR', payload: errorMessage });
      throw error;
    }
  };

  // Register function
  const register = async (userData: RegisterRequest): Promise<RegisterResponse> => {
    dispatch({ type: 'AUTH_START' });

    try {
      const response = await apiClient.register(userData);
      
      // Registration successful but may need verification
      dispatch({ type: 'AUTH_CLEAR_ERROR' });
      
      return response;
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      dispatch({ type: 'AUTH_ERROR', payload: errorMessage });
      throw error;
    }
  };

  // Logout function
  const logout = async (): Promise<void> => {
    dispatch({ type: 'AUTH_START' });

    try {
      await apiClient.logout();
    } catch (error) {
      // Ignore errors during logout
      console.warn('Error during logout:', error);
    } finally {
      dispatch({ type: 'AUTH_LOGOUT' });
    }
  };

  // Verify email function
  const verifyEmail = async (token: string): Promise<MessageResponse> => {
    dispatch({ type: 'AUTH_START' });

    try {
      const response = await apiClient.verifyEmail(token);
      dispatch({ type: 'AUTH_CLEAR_ERROR' });
      return response;
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      dispatch({ type: 'AUTH_ERROR', payload: errorMessage });
      throw error;
    }
  };

  // Resend verification function
  const resendVerification = async (email: string): Promise<MessageResponse> => {
    dispatch({ type: 'AUTH_START' });

    try {
      const response = await apiClient.resendVerification(email);
      dispatch({ type: 'AUTH_CLEAR_ERROR' });
      return response;
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      dispatch({ type: 'AUTH_ERROR', payload: errorMessage });
      throw error;
    }
  };

  // Forgot password function
  const forgotPassword = async (email: string): Promise<MessageResponse> => {
    dispatch({ type: 'AUTH_START' });

    try {
      const response = await apiClient.forgotPassword(email);
      dispatch({ type: 'AUTH_CLEAR_ERROR' });
      return response;
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      dispatch({ type: 'AUTH_ERROR', payload: errorMessage });
      throw error;
    }
  };

  // Reset password function
  const resetPassword = async (data: {
    token: string;
    password: string;
    password_confirm: string;
  }): Promise<MessageResponse> => {
    dispatch({ type: 'AUTH_START' });

    try {
      const response = await apiClient.resetPassword(data);
      dispatch({ type: 'AUTH_CLEAR_ERROR' });
      return response;
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      dispatch({ type: 'AUTH_ERROR', payload: errorMessage });
      throw error;
    }
  };

  // Change password function
  const changePassword = async (data: {
    current_password: string;
    new_password: string;
    password_confirm: string;
  }): Promise<MessageResponse> => {
    dispatch({ type: 'AUTH_START' });

    try {
      const response = await apiClient.changePassword(data);
      dispatch({ type: 'AUTH_CLEAR_ERROR' });
      return response;
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      dispatch({ type: 'AUTH_ERROR', payload: errorMessage });
      throw error;
    }
  };

  // Refresh tokens function
  const refreshTokens = async (): Promise<TokenResponse> => {
    if (!state.refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await apiClient.refreshToken(state.refreshToken);
      
      dispatch({
        type: 'AUTH_SUCCESS',
        payload: {
          user: response.user,
          token: response.access_token,
          refreshToken: response.refresh_token,
        },
      });

      return response;
    } catch (error) {
      dispatch({ type: 'AUTH_LOGOUT' });
      throw error;
    }
  };

  // Get current user function
  const getCurrentUser = async (): Promise<User> => {
    try {
      const user = await apiClient.getCurrentUser();
      dispatch({ type: 'AUTH_SET_USER', payload: user });
      return user;
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      dispatch({ type: 'AUTH_ERROR', payload: errorMessage });
      throw error;
    }
  };

  // Update profile function
  const updateProfile = async (data: Partial<User>): Promise<User> => {
    dispatch({ type: 'AUTH_START' });

    try {
      const user = await apiClient.updateProfile(data);
      dispatch({ type: 'AUTH_SET_USER', payload: user });
      return user;
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      dispatch({ type: 'AUTH_ERROR', payload: errorMessage });
      throw error;
    }
  };

  // Clear error function
  const clearError = (): void => {
    dispatch({ type: 'AUTH_CLEAR_ERROR' });
  };

  // Context value
  const contextValue: AuthContextType = {
    // State
    ...state,

    // Actions
    login,
    register,
    logout,
    verifyEmail,
    resendVerification,
    forgotPassword,
    resetPassword,
    changePassword,
    refreshTokens,
    getCurrentUser,
    updateProfile,

    // Utilities
    clearError,
    checkPasswordStrength,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

// Hook to use auth context
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
}

// Hook for protected routes
export function useRequireAuth(): AuthContextType {
  const auth = useAuth();
  
  useEffect(() => {
    if (auth.isInitialized && !auth.isAuthenticated && !auth.isLoading) {
      // Redirect to login or show error
      console.warn('Authentication required but user is not authenticated');
    }
  }, [auth.isInitialized, auth.isAuthenticated, auth.isLoading]);
  
  return auth;
}

// Hook for guest-only routes (redirect authenticated users)
export function useGuestOnly(): AuthContextType {
  const auth = useAuth();
  
  useEffect(() => {
    if (auth.isInitialized && auth.isAuthenticated) {
      // Redirect authenticated users away from guest-only pages
      console.warn('Authenticated user accessing guest-only route');
    }
  }, [auth.isInitialized, auth.isAuthenticated]);
  
  return auth;
}