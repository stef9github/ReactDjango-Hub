/**
 * Authentication Hooks
 * Custom hooks for common auth-related functionality
 */

import { useState, useCallback, useEffect } from 'react';
import { useAuth } from './auth-context';
import type {
  UseFormReturn,
  FormError,
  ValidationResult,
  LoginRequest,
  RegisterRequest,
  VerifyEmailRequest,
  ForgotPasswordRequest,
  ResetPasswordRequest,
  ChangePasswordRequest,
} from '@/types/auth';

// Generic form hook
export function useForm<T extends Record<string, any>>(
  initialData: T,
  validator?: (data: T) => ValidationResult
): UseFormReturn<T> {
  const [data, setData] = useState<T>(initialData);
  const [errors, setErrors] = useState<FormError[]>([]);
  const [touched, setTouched] = useState<Record<keyof T, boolean>>(
    Object.keys(initialData).reduce((acc, key) => {
      acc[key as keyof T] = false;
      return acc;
    }, {} as Record<keyof T, boolean>)
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Validate a single field
  const validateField = useCallback(
    (field: keyof T, value: any): ValidationResult => {
      if (!validator) {
        return { isValid: true, errors: [] };
      }

      const testData = { ...data, [field]: value };
      const result = validator(testData);
      
      // Filter errors for this field only
      const fieldErrors = result.errors.filter(
        (error) => error.field === field || !error.field
      );

      return {
        isValid: fieldErrors.length === 0,
        errors: fieldErrors,
      };
    },
    [data, validator]
  );

  // Validate entire form
  const validateForm = useCallback((): ValidationResult => {
    if (!validator) {
      return { isValid: true, errors: [] };
    }
    return validator(data);
  }, [data, validator]);

  // Check if form is valid
  const isValid = errors.length === 0;

  // Update form data
  const setFormData = useCallback((newData: Partial<T>) => {
    setData((prev) => ({ ...prev, ...newData }));
  }, []);

  // Handle field change
  const handleChange = useCallback(
    (field: keyof T) => (value: any) => {
      setData((prev) => ({ ...prev, [field]: value }));
      
      // Clear field errors when value changes
      setErrors((prev) => prev.filter((error) => error.field !== field));
    },
    []
  );

  // Handle field blur
  const handleBlur = useCallback(
    (field: keyof T) => () => {
      setTouched((prev) => ({ ...prev, [field]: true }));
      
      // Validate field on blur if it's been touched
      if (validator && touched[field]) {
        const result = validateField(field, data[field]);
        if (!result.isValid) {
          setErrors((prev) => [
            ...prev.filter((error) => error.field !== field),
            ...result.errors,
          ]);
        }
      }
    },
    [data, touched, validateField, validator]
  );

  // Handle form submission
  const handleSubmit = useCallback(
    (onSubmit: (data: T) => Promise<void>) => 
      async (e: React.FormEvent) => {
        e.preventDefault();
        
        // Mark all fields as touched
        const allTouched = Object.keys(data).reduce((acc, key) => {
          acc[key as keyof T] = true;
          return acc;
        }, {} as Record<keyof T, boolean>);
        setTouched(allTouched);

        // Validate form
        const validation = validateForm();
        if (!validation.isValid) {
          setErrors(validation.errors);
          return;
        }

        setIsSubmitting(true);
        setErrors([]);

        try {
          await onSubmit(data);
        } catch (error: any) {
          // Handle submission errors
          const formError: FormError = {
            message: error.message || 'Submission failed',
          };
          setErrors([formError]);
        } finally {
          setIsSubmitting(false);
        }
      },
    [data, validateForm]
  );

  // Reset form
  const resetForm = useCallback((newData?: Partial<T>) => {
    const resetData = newData ? { ...initialData, ...newData } : initialData;
    setData(resetData);
    setErrors([]);
    setTouched(
      Object.keys(resetData).reduce((acc, key) => {
        acc[key as keyof T] = false;
        return acc;
      }, {} as Record<keyof T, boolean>)
    );
    setIsSubmitting(false);
  }, [initialData]);

  return {
    data,
    setData: setFormData,
    errors,
    setErrors,
    isSubmitting,
    setIsSubmitting,
    touched,
    setTouched: (field: keyof T, isTouched = true) => {
      setTouched((prev) => ({ ...prev, [field]: isTouched }));
    },
    isValid,
    handleSubmit,
    handleChange,
    handleBlur,
    resetForm,
    validateField,
    validateForm,
  };
}

// Login form hook
export function useLoginForm() {
  const { login } = useAuth();
  
  const validator = (data: LoginRequest): ValidationResult => {
    const errors: FormError[] = [];
    
    if (!data.email) {
      errors.push({ field: 'email', message: 'Email is required' });
    } else if (!/\S+@\S+\.\S+/.test(data.email)) {
      errors.push({ field: 'email', message: 'Email is invalid' });
    }
    
    if (!data.password) {
      errors.push({ field: 'password', message: 'Password is required' });
    }
    
    return { isValid: errors.length === 0, errors };
  };

  const form = useForm<LoginRequest>(
    { email: '', password: '' },
    validator
  );

  const handleLogin = useCallback(
    async (data: LoginRequest) => {
      await login(data);
    },
    [login]
  );

  return {
    ...form,
    handleLogin: form.handleSubmit(handleLogin),
  };
}

// Registration form hook
export function useRegisterForm() {
  const { register, checkPasswordStrength } = useAuth();
  
  const validator = (data: RegisterRequest & { password_confirm?: string }): ValidationResult => {
    const errors: FormError[] = [];
    
    if (!data.email) {
      errors.push({ field: 'email', message: 'Email is required' });
    } else if (!/\S+@\S+\.\S+/.test(data.email)) {
      errors.push({ field: 'email', message: 'Email is invalid' });
    }
    
    if (!data.password) {
      errors.push({ field: 'password', message: 'Password is required' });
    } else {
      const strength = checkPasswordStrength(data.password);
      if (strength.score < 2) {
        errors.push({ field: 'password', message: 'Password is too weak' });
      }
    }
    
    if (data.password_confirm !== undefined && data.password !== data.password_confirm) {
      errors.push({ field: 'password_confirm', message: 'Passwords do not match' });
    }
    
    if (!data.first_name?.trim()) {
      errors.push({ field: 'first_name', message: 'First name is required' });
    }
    
    if (!data.last_name?.trim()) {
      errors.push({ field: 'last_name', message: 'Last name is required' });
    }
    
    return { isValid: errors.length === 0, errors };
  };

  const form = useForm<RegisterRequest & { password_confirm: string }>(
    {
      email: '',
      password: '',
      password_confirm: '',
      first_name: '',
      last_name: '',
      phone_number: '',
    },
    validator
  );

  const handleRegister = useCallback(
    async (data: RegisterRequest & { password_confirm: string }) => {
      const { password_confirm, ...registerData } = data;
      await register(registerData);
    },
    [register]
  );

  return {
    ...form,
    handleRegister: form.handleSubmit(handleRegister),
  };
}

// Email verification hook
export function useEmailVerification() {
  const { verifyEmail, resendVerification } = useAuth();
  const [isResending, setIsResending] = useState(false);

  const handleVerifyEmail = useCallback(
    async (token: string) => {
      return await verifyEmail(token);
    },
    [verifyEmail]
  );

  const handleResendVerification = useCallback(
    async (email: string) => {
      setIsResending(true);
      try {
        return await resendVerification(email);
      } finally {
        setIsResending(false);
      }
    },
    [resendVerification]
  );

  return {
    verifyEmail: handleVerifyEmail,
    resendVerification: handleResendVerification,
    isResending,
  };
}

// Forgot password hook
export function useForgotPassword() {
  const { forgotPassword } = useAuth();
  
  const validator = (data: ForgotPasswordRequest): ValidationResult => {
    const errors: FormError[] = [];
    
    if (!data.email) {
      errors.push({ field: 'email', message: 'Email is required' });
    } else if (!/\S+@\S+\.\S+/.test(data.email)) {
      errors.push({ field: 'email', message: 'Email is invalid' });
    }
    
    return { isValid: errors.length === 0, errors };
  };

  const form = useForm<ForgotPasswordRequest>(
    { email: '' },
    validator
  );

  const handleForgotPassword = useCallback(
    async (data: ForgotPasswordRequest) => {
      await forgotPassword(data.email);
    },
    [forgotPassword]
  );

  return {
    ...form,
    handleForgotPassword: form.handleSubmit(handleForgotPassword),
  };
}

// Reset password hook
export function useResetPassword(token: string) {
  const { resetPassword, checkPasswordStrength } = useAuth();
  
  const validator = (data: ResetPasswordRequest): ValidationResult => {
    const errors: FormError[] = [];
    
    if (!data.password) {
      errors.push({ field: 'password', message: 'Password is required' });
    } else {
      const strength = checkPasswordStrength(data.password);
      if (strength.score < 2) {
        errors.push({ field: 'password', message: 'Password is too weak' });
      }
    }
    
    if (!data.password_confirm) {
      errors.push({ field: 'password_confirm', message: 'Password confirmation is required' });
    } else if (data.password !== data.password_confirm) {
      errors.push({ field: 'password_confirm', message: 'Passwords do not match' });
    }
    
    return { isValid: errors.length === 0, errors };
  };

  const form = useForm<ResetPasswordRequest>(
    { token, password: '', password_confirm: '' },
    validator
  );

  const handleResetPassword = useCallback(
    async (data: ResetPasswordRequest) => {
      await resetPassword(data);
    },
    [resetPassword]
  );

  return {
    ...form,
    handleResetPassword: form.handleSubmit(handleResetPassword),
  };
}

// Change password hook
export function useChangePassword() {
  const { changePassword, checkPasswordStrength } = useAuth();
  
  const validator = (data: ChangePasswordRequest): ValidationResult => {
    const errors: FormError[] = [];
    
    if (!data.current_password) {
      errors.push({ field: 'current_password', message: 'Current password is required' });
    }
    
    if (!data.new_password) {
      errors.push({ field: 'new_password', message: 'New password is required' });
    } else {
      const strength = checkPasswordStrength(data.new_password);
      if (strength.score < 2) {
        errors.push({ field: 'new_password', message: 'New password is too weak' });
      }
    }
    
    if (!data.password_confirm) {
      errors.push({ field: 'password_confirm', message: 'Password confirmation is required' });
    } else if (data.new_password !== data.password_confirm) {
      errors.push({ field: 'password_confirm', message: 'Passwords do not match' });
    }
    
    return { isValid: errors.length === 0, errors };
  };

  const form = useForm<ChangePasswordRequest>(
    { current_password: '', new_password: '', password_confirm: '' },
    validator
  );

  const handleChangePassword = useCallback(
    async (data: ChangePasswordRequest) => {
      await changePassword(data);
    },
    [changePassword]
  );

  return {
    ...form,
    handleChangePassword: form.handleSubmit(handleChangePassword),
  };
}

// Password strength hook
export function usePasswordStrength(password: string) {
  const { checkPasswordStrength } = useAuth();
  const [strength, setStrength] = useState(checkPasswordStrength(password));

  useEffect(() => {
    setStrength(checkPasswordStrength(password));
  }, [password, checkPasswordStrength]);

  return strength;
}

// Auto-logout hook (for session timeout)
export function useAutoLogout(timeoutMinutes: number = 30) {
  const { logout, isAuthenticated } = useAuth();
  
  useEffect(() => {
    if (!isAuthenticated) return;

    let timeoutId: NodeJS.Timeout;

    const resetTimeout = () => {
      if (timeoutId) clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        logout();
      }, timeoutMinutes * 60 * 1000);
    };

    const handleActivity = () => {
      resetTimeout();
    };

    // Set initial timeout
    resetTimeout();

    // Listen for user activity
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
    events.forEach(event => {
      document.addEventListener(event, handleActivity, true);
    });

    return () => {
      if (timeoutId) clearTimeout(timeoutId);
      events.forEach(event => {
        document.removeEventListener(event, handleActivity, true);
      });
    };
  }, [logout, isAuthenticated, timeoutMinutes]);
}

// Local storage sync hook
export function useLocalStorageSync() {
  const { user, isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated && user) {
      localStorage.setItem('user_data', JSON.stringify(user));
    } else {
      localStorage.removeItem('user_data');
    }
  }, [user, isAuthenticated]);
}