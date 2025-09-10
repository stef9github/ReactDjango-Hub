# Frontend Component Architecture Guide

## Overview

This guide defines the component architecture patterns, state management strategies, and best practices for the ReactDjango Hub frontend implementation.

## Component Organization Strategy

### Feature-Based Structure

```
src/
├── features/                   # Business domain features
│   ├── auth/                  # Authentication feature
│   │   ├── components/        # Feature-specific components
│   │   │   ├── LoginForm.tsx
│   │   │   ├── MFASetup.tsx
│   │   │   └── PasswordReset.tsx
│   │   ├── hooks/            # Feature-specific hooks
│   │   │   ├── useLogin.ts
│   │   │   └── useMFA.ts
│   │   ├── pages/            # Feature pages/routes
│   │   │   ├── LoginPage.tsx
│   │   │   └── RegisterPage.tsx
│   │   ├── services/         # API integration
│   │   │   └── auth.service.ts
│   │   ├── stores/           # Feature state
│   │   │   └── auth.store.ts
│   │   ├── types/            # TypeScript types
│   │   │   └── auth.types.ts
│   │   ├── utils/            # Feature utilities
│   │   │   └── validators.ts
│   │   └── index.ts          # Public API
│   │
│   ├── dashboard/            # Dashboard feature
│   ├── users/               # User management feature
│   └── settings/            # Settings feature
│
├── shared/                   # Truly shared, reusable code
│   ├── components/          # Generic UI components
│   │   ├── ui/             # Base UI components
│   │   │   ├── Button/
│   │   │   ├── Card/
│   │   │   ├── Modal/
│   │   │   └── Table/
│   │   ├── forms/          # Form components
│   │   │   ├── Input/
│   │   │   ├── Select/
│   │   │   └── FormField/
│   │   └── layout/         # Layout components
│   │       ├── Header/
│   │       ├── Sidebar/
│   │       └── PageLayout/
│   ├── hooks/              # Shared hooks
│   └── utils/              # Shared utilities
│
└── core/                    # Core application setup
    ├── router/             # Routing configuration
    ├── providers/          # Context providers
    └── config/             # App configuration
```

## Component Patterns

### 1. Base Component Pattern

```typescript
// shared/components/ui/Button/Button.tsx
import React, { forwardRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/shared/utils/cn';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, loading, children, disabled, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <svg
            className="mr-2 h-4 w-4 animate-spin"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';

export { Button, buttonVariants };
```

### 2. Feature Component Pattern

```typescript
// features/users/components/UserList.tsx
import React, { useState } from 'react';
import { useUsers } from '../hooks/useUsers';
import { DataTable } from '@/shared/components/ui/Table';
import { Button } from '@/shared/components/ui/Button';
import { UserFilters } from './UserFilters';
import { UserDetailsModal } from './UserDetailsModal';
import type { User } from '../types/user.types';

export function UserList() {
  const [filters, setFilters] = useState({});
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  
  const { data, isLoading, error } = useUsers(filters);
  
  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded">
        <p className="text-red-800">Failed to load users: {error.message}</p>
      </div>
    );
  }
  
  const columns = [
    {
      accessorKey: 'name',
      header: 'Name',
      cell: ({ row }) => (
        <button
          onClick={() => setSelectedUser(row.original)}
          className="text-blue-600 hover:underline"
        >
          {row.getValue('name')}
        </button>
      ),
    },
    {
      accessorKey: 'email',
      header: 'Email',
    },
    {
      accessorKey: 'role',
      header: 'Role',
      cell: ({ row }) => (
        <span className="px-2 py-1 text-xs bg-gray-100 rounded">
          {row.getValue('role')}
        </span>
      ),
    },
    {
      id: 'actions',
      cell: ({ row }) => (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => handleEdit(row.original)}
        >
          Edit
        </Button>
      ),
    },
  ];
  
  return (
    <div className="space-y-4">
      <UserFilters 
        filters={filters} 
        onChange={setFilters} 
      />
      
      <DataTable
        columns={columns}
        data={data?.users || []}
        loading={isLoading}
        pagination={{
          pageSize: 10,
          total: data?.total || 0,
        }}
      />
      
      {selectedUser && (
        <UserDetailsModal
          user={selectedUser}
          onClose={() => setSelectedUser(null)}
        />
      )}
    </div>
  );
}
```

### 3. Compound Component Pattern

```typescript
// shared/components/ui/Card/index.tsx
import React from 'react';
import { cn } from '@/shared/utils/cn';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'rounded-lg border bg-card text-card-foreground shadow-sm',
        className
      )}
      {...props}
    />
  )
);
Card.displayName = 'Card';

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex flex-col space-y-1.5 p-6', className)}
    {...props}
  />
));
CardHeader.displayName = 'CardHeader';

const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      'text-2xl font-semibold leading-none tracking-tight',
      className
    )}
    {...props}
  />
));
CardTitle.displayName = 'CardTitle';

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn('text-sm text-muted-foreground', className)}
    {...props}
  />
));
CardDescription.displayName = 'CardDescription';

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('p-6 pt-0', className)} {...props} />
));
CardContent.displayName = 'CardContent';

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex items-center p-6 pt-0', className)}
    {...props}
  />
));
CardFooter.displayName = 'CardFooter';

export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
};

// Usage example:
// <Card>
//   <CardHeader>
//     <CardTitle>User Profile</CardTitle>
//     <CardDescription>Manage your account settings</CardDescription>
//   </CardHeader>
//   <CardContent>
//     {/* Content here */}
//   </CardContent>
//   <CardFooter>
//     <Button>Save Changes</Button>
//   </CardFooter>
// </Card>
```

## State Management Architecture

### 1. Global State with Zustand

```typescript
// stores/app.store.ts
import { create } from 'zustand';
import { devtools, persist, subscribeWithSelector } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

interface AppState {
  // UI State
  sidebarOpen: boolean;
  theme: 'light' | 'dark' | 'system';
  
  // User Preferences
  preferences: {
    language: string;
    timezone: string;
    notifications: boolean;
  };
  
  // Actions
  toggleSidebar: () => void;
  setTheme: (theme: AppState['theme']) => void;
  updatePreferences: (preferences: Partial<AppState['preferences']>) => void;
}

export const useAppStore = create<AppState>()(
  devtools(
    persist(
      immer((set) => ({
        // Initial state
        sidebarOpen: true,
        theme: 'system',
        preferences: {
          language: 'en',
          timezone: 'UTC',
          notifications: true,
        },
        
        // Actions
        toggleSidebar: () =>
          set((state) => {
            state.sidebarOpen = !state.sidebarOpen;
          }),
          
        setTheme: (theme) =>
          set((state) => {
            state.theme = theme;
          }),
          
        updatePreferences: (preferences) =>
          set((state) => {
            state.preferences = { ...state.preferences, ...preferences };
          }),
      })),
      {
        name: 'app-store',
        partialize: (state) => ({
          theme: state.theme,
          preferences: state.preferences,
        }),
      }
    ),
    {
      name: 'AppStore',
    }
  )
);

// Selectors
export const selectSidebarOpen = (state: AppState) => state.sidebarOpen;
export const selectTheme = (state: AppState) => state.theme;
export const selectPreferences = (state: AppState) => state.preferences;
```

### 2. Server State with TanStack Query

```typescript
// core/providers/QueryProvider.tsx
import React from 'react';
import {
  QueryClient,
  QueryClientProvider,
  QueryCache,
  MutationCache,
} from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { toast } from '@/shared/components/ui/Toast';

function handleError(error: unknown): void {
  const message = error instanceof Error 
    ? error.message 
    : 'An unexpected error occurred';
  
  toast.error(message);
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000,   // 10 minutes
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors
        if (error instanceof Error && error.message.includes('4')) {
          return false;
        }
        return failureCount < 3;
      },
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: false,
    },
  },
  queryCache: new QueryCache({
    onError: handleError,
  }),
  mutationCache: new MutationCache({
    onError: handleError,
  }),
});

export function QueryProvider({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {import.meta.env.DEV && <ReactQueryDevtools />}
    </QueryClientProvider>
  );
}
```

### 3. Form State with React Hook Form

```typescript
// features/users/components/UserForm.tsx
import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useCreateUser, useUpdateUser } from '../hooks/useUsers';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/forms/Input';
import { Select } from '@/shared/components/forms/Select';
import type { User } from '../types/user.types';

const userSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Invalid email address'),
  role: z.enum(['admin', 'user', 'viewer']),
  organizationId: z.string().uuid('Invalid organization'),
});

type UserFormData = z.infer<typeof userSchema>;

interface UserFormProps {
  user?: User;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function UserForm({ user, onSuccess, onCancel }: UserFormProps) {
  const createUser = useCreateUser();
  const updateUser = useUpdateUser();
  
  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isSubmitting },
  } = useForm<UserFormData>({
    resolver: zodResolver(userSchema),
    defaultValues: user || {
      name: '',
      email: '',
      role: 'user',
      organizationId: '',
    },
  });
  
  const onSubmit = async (data: UserFormData) => {
    try {
      if (user) {
        await updateUser.mutateAsync({ id: user.id, ...data });
      } else {
        await createUser.mutateAsync(data);
      }
      onSuccess?.();
    } catch (error) {
      // Error is handled by mutation error handler
    }
  };
  
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Input
        label="Name"
        {...register('name')}
        error={errors.name?.message}
      />
      
      <Input
        label="Email"
        type="email"
        {...register('email')}
        error={errors.email?.message}
      />
      
      <Select
        label="Role"
        control={control}
        name="role"
        options={[
          { value: 'admin', label: 'Administrator' },
          { value: 'user', label: 'User' },
          { value: 'viewer', label: 'Viewer' },
        ]}
        error={errors.role?.message}
      />
      
      <div className="flex gap-2">
        <Button type="submit" loading={isSubmitting}>
          {user ? 'Update' : 'Create'} User
        </Button>
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        )}
      </div>
    </form>
  );
}
```

## Custom Hooks Patterns

### 1. Data Fetching Hook

```typescript
// features/dashboard/hooks/useDashboardMetrics.ts
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';
import { dashboardService } from '../services/dashboard.service';

export function useDashboardMetrics(refreshInterval?: number) {
  const queryClient = useQueryClient();
  
  const query = useQuery({
    queryKey: ['dashboard', 'metrics'],
    queryFn: dashboardService.getMetrics,
    staleTime: refreshInterval || 60000, // Default 1 minute
  });
  
  // Set up auto-refresh if specified
  useEffect(() => {
    if (!refreshInterval) return;
    
    const interval = setInterval(() => {
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'metrics'] });
    }, refreshInterval);
    
    return () => clearInterval(interval);
  }, [refreshInterval, queryClient]);
  
  return {
    metrics: query.data,
    isLoading: query.isLoading,
    error: query.error,
    refresh: () => query.refetch(),
  };
}
```

### 2. Debounced Search Hook

```typescript
// shared/hooks/useDebouncedSearch.ts
import { useState, useEffect, useCallback } from 'react';
import { useDebounce } from './useDebounce';

export function useDebouncedSearch<T>(
  searchFn: (query: string) => Promise<T[]>,
  delay = 300
) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<T[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const debouncedQuery = useDebounce(query, delay);
  
  useEffect(() => {
    if (!debouncedQuery) {
      setResults([]);
      return;
    }
    
    let cancelled = false;
    
    (async () => {
      setIsSearching(true);
      setError(null);
      
      try {
        const data = await searchFn(debouncedQuery);
        if (!cancelled) {
          setResults(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err as Error);
        }
      } finally {
        if (!cancelled) {
          setIsSearching(false);
        }
      }
    })();
    
    return () => {
      cancelled = true;
    };
  }, [debouncedQuery, searchFn]);
  
  const search = useCallback((newQuery: string) => {
    setQuery(newQuery);
  }, []);
  
  const clear = useCallback(() => {
    setQuery('');
    setResults([]);
  }, []);
  
  return {
    query,
    results,
    isSearching,
    error,
    search,
    clear,
  };
}
```

### 3. Permission Hook

```typescript
// features/auth/hooks/usePermission.ts
import { useAuthStore } from '../stores/auth.store';

export function usePermission() {
  const user = useAuthStore((state) => state.user);
  
  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    return user.permissions.includes(permission);
  };
  
  const hasRole = (role: string): boolean => {
    if (!user) return false;
    return user.roles.some((r) => r.name === role);
  };
  
  const hasAnyPermission = (permissions: string[]): boolean => {
    if (!user) return false;
    return permissions.some((p) => user.permissions.includes(p));
  };
  
  const hasAllPermissions = (permissions: string[]): boolean => {
    if (!user) return false;
    return permissions.every((p) => user.permissions.includes(p));
  };
  
  return {
    hasPermission,
    hasRole,
    hasAnyPermission,
    hasAllPermissions,
    permissions: user?.permissions || [],
    roles: user?.roles || [],
  };
}

// Usage in components
export function AdminPanel() {
  const { hasRole, hasPermission } = usePermission();
  
  if (!hasRole('admin')) {
    return <div>Access denied</div>;
  }
  
  return (
    <div>
      {hasPermission('users.create') && (
        <Button>Create User</Button>
      )}
    </div>
  );
}
```

## Performance Optimization Patterns

### 1. Code Splitting

```typescript
// core/router/Router.tsx
import React, { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import { LoadingSpinner } from '@/shared/components/ui/LoadingSpinner';

// Lazy load feature modules
const AuthModule = lazy(() => import('@/features/auth'));
const DashboardModule = lazy(() => import('@/features/dashboard'));
const UsersModule = lazy(() => import('@/features/users'));
const SettingsModule = lazy(() => import('@/features/settings'));

function AppRouter() {
  return (
    <Suspense fallback={<LoadingSpinner fullScreen />}>
      <Routes>
        <Route path="/auth/*" element={<AuthModule />} />
        <Route path="/dashboard/*" element={<DashboardModule />} />
        <Route path="/users/*" element={<UsersModule />} />
        <Route path="/settings/*" element={<SettingsModule />} />
      </Routes>
    </Suspense>
  );
}
```

### 2. Memoization

```typescript
// features/dashboard/components/MetricCard.tsx
import React, { memo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: number | string;
  change?: number;
  format?: (value: number | string) => string;
}

export const MetricCard = memo(function MetricCard({
  title,
  value,
  change,
  format = (v) => String(v),
}: MetricCardProps) {
  const getTrendIcon = () => {
    if (!change) return <Minus className="h-4 w-4 text-gray-400" />;
    if (change > 0) return <TrendingUp className="h-4 w-4 text-green-500" />;
    return <TrendingDown className="h-4 w-4 text-red-500" />;
  };
  
  const getTrendColor = () => {
    if (!change) return 'text-gray-600';
    return change > 0 ? 'text-green-600' : 'text-red-600';
  };
  
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {getTrendIcon()}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{format(value)}</div>
        {change !== undefined && (
          <p className={`text-xs ${getTrendColor()}`}>
            {change > 0 ? '+' : ''}{change}% from last month
          </p>
        )}
      </CardContent>
    </Card>
  );
});
```

### 3. Virtual Lists

```typescript
// shared/components/ui/VirtualList.tsx
import React from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';

interface VirtualListProps<T> {
  items: T[];
  height: number;
  itemHeight: number;
  renderItem: (item: T, index: number) => React.ReactNode;
  overscan?: number;
}

export function VirtualList<T>({
  items,
  height,
  itemHeight,
  renderItem,
  overscan = 5,
}: VirtualListProps<T>) {
  const parentRef = React.useRef<HTMLDivElement>(null);
  
  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => itemHeight,
    overscan,
  });
  
  return (
    <div
      ref={parentRef}
      style={{ height, overflow: 'auto' }}
      className="relative"
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualItem.size}px`,
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            {renderItem(items[virtualItem.index], virtualItem.index)}
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Testing Patterns

### 1. Component Testing

```typescript
// features/users/components/__tests__/UserList.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import { UserList } from '../UserList';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('UserList', () => {
  it('renders loading state', () => {
    render(<UserList />, { wrapper: createWrapper() });
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });
  
  it('renders users when loaded', async () => {
    const mockUsers = [
      { id: '1', name: 'John Doe', email: 'john@example.com' },
      { id: '2', name: 'Jane Smith', email: 'jane@example.com' },
    ];
    
    vi.mock('../hooks/useUsers', () => ({
      useUsers: () => ({
        data: { users: mockUsers, total: 2 },
        isLoading: false,
        error: null,
      }),
    }));
    
    render(<UserList />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    });
  });
  
  it('handles user selection', async () => {
    const user = userEvent.setup();
    render(<UserList />, { wrapper: createWrapper() });
    
    const firstUser = await screen.findByText('John Doe');
    await user.click(firstUser);
    
    expect(screen.getByTestId('user-details-modal')).toBeInTheDocument();
  });
});
```

### 2. Hook Testing

```typescript
// features/auth/hooks/__tests__/usePermission.test.ts
import { renderHook } from '@testing-library/react';
import { usePermission } from '../usePermission';
import { useAuthStore } from '../../stores/auth.store';

vi.mock('../../stores/auth.store');

describe('usePermission', () => {
  it('returns false when user is not authenticated', () => {
    vi.mocked(useAuthStore).mockReturnValue({ user: null });
    
    const { result } = renderHook(() => usePermission());
    
    expect(result.current.hasPermission('users.create')).toBe(false);
    expect(result.current.hasRole('admin')).toBe(false);
  });
  
  it('checks permissions correctly', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: {
        id: '1',
        email: 'test@example.com',
        permissions: ['users.read', 'users.create'],
        roles: [{ name: 'admin', permissions: [] }],
      },
    });
    
    const { result } = renderHook(() => usePermission());
    
    expect(result.current.hasPermission('users.create')).toBe(true);
    expect(result.current.hasPermission('users.delete')).toBe(false);
    expect(result.current.hasRole('admin')).toBe(true);
    expect(result.current.hasRole('user')).toBe(false);
  });
});
```

## Accessibility Patterns

### 1. Accessible Form

```typescript
// shared/components/forms/FormField.tsx
import React from 'react';
import { useId } from 'react';

interface FormFieldProps {
  label: string;
  error?: string;
  required?: boolean;
  children: (props: {
    id: string;
    'aria-invalid': boolean;
    'aria-describedby': string | undefined;
    'aria-required': boolean;
  }) => React.ReactNode;
}

export function FormField({
  label,
  error,
  required = false,
  children,
}: FormFieldProps) {
  const id = useId();
  const errorId = `${id}-error`;
  const descriptionId = `${id}-description`;
  
  return (
    <div className="space-y-2">
      <label htmlFor={id} className="block text-sm font-medium">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      
      {children({
        id,
        'aria-invalid': !!error,
        'aria-describedby': error ? errorId : undefined,
        'aria-required': required,
      })}
      
      {error && (
        <p id={errorId} className="text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

// Usage:
// <FormField label="Email" error={errors.email} required>
//   {(props) => (
//     <input
//       type="email"
//       className="..."
//       {...props}
//       {...register('email')}
//     />
//   )}
// </FormField>
```

### 2. Keyboard Navigation

```typescript
// shared/components/ui/Dialog.tsx
import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { useFocusTrap } from '@/shared/hooks/useFocusTrap';

interface DialogProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export function Dialog({ isOpen, onClose, title, children }: DialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  useFocusTrap(dialogRef, isOpen);
  
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);
  
  if (!isOpen) return null;
  
  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="dialog-title"
    >
      <div
        className="fixed inset-0 bg-black/50"
        onClick={onClose}
        aria-hidden="true"
      />
      
      <div
        ref={dialogRef}
        className="relative bg-white rounded-lg shadow-xl max-w-md w-full mx-4"
      >
        <div className="p-6">
          <h2 id="dialog-title" className="text-lg font-semibold mb-4">
            {title}
          </h2>
          
          {children}
          
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-1 hover:bg-gray-100 rounded"
            aria-label="Close dialog"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
```

## Related Architecture Documents

### Essential Companion Guides
1. **[Multi-App Style Guide](./multi-app-style-guide.md)** - Design system and theming across microservices
2. **[i18n Architecture](./i18n-architecture.md)** - Internationalization framework and translation management
3. **[l10n Implementation](./l10n-implementation.md)** - Practical localization patterns and regional adaptations
4. **[API Integration Guide](./api-integration-guide.md)** - Service communication patterns

## Best Practices Summary

### Component Design
1. **Single Responsibility**: Each component should do one thing well
2. **Composition over Inheritance**: Use component composition patterns
3. **Props Interface**: Define clear TypeScript interfaces for all props
4. **Default Props**: Provide sensible defaults where appropriate
5. **Error Boundaries**: Wrap features in error boundaries
6. **i18n Ready**: All text should use translation keys
7. **RTL Support**: Use logical CSS properties for layout

### State Management
1. **Server vs Client State**: Use TanStack Query for server state, Zustand for client state
2. **Minimize Global State**: Keep state as local as possible
3. **Derived State**: Calculate derived values instead of storing them
4. **Optimistic Updates**: Improve UX with optimistic updates
5. **State Normalization**: Normalize complex nested data

### Performance
1. **Code Splitting**: Split by route and feature
2. **Lazy Loading**: Load components only when needed
3. **Memoization**: Use React.memo and useMemo appropriately
4. **Virtual Scrolling**: For large lists
5. **Bundle Size**: Monitor and optimize bundle size

### Testing
1. **Test User Behavior**: Focus on user interactions, not implementation
2. **Integration Tests**: Prioritize integration over unit tests
3. **Accessibility Testing**: Include a11y in test suite
4. **Visual Regression**: For critical UI components
5. **Performance Testing**: Monitor render performance

### Accessibility
1. **Semantic HTML**: Use proper HTML elements
2. **ARIA Labels**: Provide context for screen readers
3. **Keyboard Navigation**: Ensure full keyboard accessibility
4. **Focus Management**: Manage focus properly in SPAs
5. **Color Contrast**: Meet WCAG guidelines

---

**Document maintained by**: Technical Lead Agent  
**For**: Frontend Agent  
**Last updated**: December 10, 2024  
**Next review**: January 10, 2025