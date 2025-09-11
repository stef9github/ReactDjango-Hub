# Frontend Component Library
## Multi-Vertical React Architecture

**Version**: 1.0  
**Date**: January 2025  
**Status**: Active  
**Purpose**: Define frontend architecture supporting multiple verticals with shared component library

---

## Overview

This document outlines the React frontend architecture that supports multiple industry verticals while maintaining a shared component library. It covers component organization, theming, state management, build configuration, and patterns for extending common components for vertical-specific needs.

---

## Project Structure

### Directory Organization

```
frontend/
├── public/                           # Static assets
│   ├── medical/                     # Medical-specific assets
│   └── public/                      # Public Hub assets
│
├── src/
│   ├── components/                  # Shared component library
│   │   ├── common/                 # Universal components
│   │   │   ├── Button/
│   │   │   ├── Card/
│   │   │   ├── DataTable/
│   │   │   ├── Form/
│   │   │   ├── Layout/
│   │   │   ├── Modal/
│   │   │   └── Navigation/
│   │   ├── charts/                 # Data visualization
│   │   ├── feedback/               # Notifications, alerts
│   │   └── patterns/               # Complex UI patterns
│   │
│   ├── verticals/                  # Vertical-specific code
│   │   ├── medical/
│   │   │   ├── components/        # Medical-only components
│   │   │   ├── pages/            # Medical pages
│   │   │   ├── hooks/            # Medical hooks
│   │   │   ├── api/              # Medical API clients
│   │   │   ├── store/            # Medical state
│   │   │   └── theme/            # Medical theming
│   │   │
│   │   └── public/
│   │       ├── components/        # Public-only components
│   │       ├── pages/            # Public pages
│   │       ├── hooks/            # Public hooks
│   │       ├── api/              # Public API clients
│   │       ├── store/            # Public state
│   │       └── theme/            # Public theming
│   │
│   ├── core/                       # Core functionality
│   │   ├── api/                  # Base API clients
│   │   ├── auth/                 # Authentication
│   │   ├── config/               # App configuration
│   │   ├── hooks/                # Shared hooks
│   │   ├── i18n/                 # Internationalization
│   │   ├── router/               # Routing configuration
│   │   ├── store/                # Global state
│   │   ├── types/                # TypeScript types
│   │   └── utils/                # Utilities
│   │
│   ├── styles/                     # Global styles
│   │   ├── base/                 # Base styles
│   │   ├── themes/               # Theme definitions
│   │   └── utilities/            # Utility classes
│   │
│   ├── App.tsx                     # Root component
│   ├── main.tsx                    # Entry point
│   └── vite-env.d.ts              # Vite types
│
├── .env.medical                     # Medical environment
├── .env.public                      # Public environment
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

---

## Common Component Library

### 1. Base Components

#### Button Component
```typescript
// components/common/Button/Button.tsx
import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/utils/cn';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        primary: 'bg-primary text-primary-foreground hover:bg-primary/90',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline: 'border border-input hover:bg-accent hover:text-accent-foreground',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        sm: 'h-8 px-3 text-xs',
        md: 'h-10 px-4 py-2',
        lg: 'h-12 px-8',
        icon: 'h-10 w-10',
      },
      vertical: {
        medical: 'shadow-medical',
        public: 'shadow-public',
        default: '',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
      vertical: 'default',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ 
    className, 
    variant, 
    size, 
    vertical,
    isLoading, 
    leftIcon, 
    rightIcon, 
    children, 
    disabled,
    ...props 
  }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, vertical, className }))}
        ref={ref}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && <Spinner className="mr-2 h-4 w-4 animate-spin" />}
        {!isLoading && leftIcon && <span className="mr-2">{leftIcon}</span>}
        {children}
        {rightIcon && <span className="ml-2">{rightIcon}</span>}
      </button>
    );
  }
);

Button.displayName = 'Button';
```

#### DataTable Component
```typescript
// components/common/DataTable/DataTable.tsx
import React, { useMemo, useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  ColumnDef,
  flexRender,
} from '@tanstack/react-table';

export interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  pageSize?: number;
  onRowClick?: (row: TData) => void;
  isLoading?: boolean;
  emptyMessage?: string;
  showPagination?: boolean;
  showSearch?: boolean;
  customActions?: React.ReactNode;
  verticalTheme?: 'medical' | 'public';
}

export function DataTable<TData, TValue>({
  columns,
  data,
  pageSize = 10,
  onRowClick,
  isLoading,
  emptyMessage = 'No data available',
  showPagination = true,
  showSearch = true,
  customActions,
  verticalTheme,
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = useState([]);
  const [filtering, setFiltering] = useState('');
  
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    onSortingChange: setSorting,
    onGlobalFilterChange: setFiltering,
    state: {
      sorting,
      globalFilter: filtering,
    },
    initialState: {
      pagination: {
        pageSize,
      },
    },
  });
  
  const tableClass = cn(
    'w-full caption-bottom text-sm',
    verticalTheme === 'medical' && 'table-medical',
    verticalTheme === 'public' && 'table-public'
  );
  
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        {showSearch && (
          <Input
            placeholder="Search..."
            value={filtering}
            onChange={(e) => setFiltering(e.target.value)}
            className="max-w-sm"
          />
        )}
        {customActions}
      </div>
      
      <div className="rounded-md border">
        <table className={tableClass}>
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th key={header.id} className="px-4 py-2">
                    {header.isPlaceholder ? null : (
                      <div
                        className={cn(
                          'flex items-center space-x-2',
                          header.column.getCanSort() && 'cursor-pointer select-none'
                        )}
                        onClick={header.column.getToggleSortingHandler()}
                      >
                        {flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                        {header.column.getCanSort() && (
                          <SortIcon direction={header.column.getIsSorted()} />
                        )}
                      </div>
                    )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={columns.length} className="text-center py-8">
                  <Spinner />
                </td>
              </tr>
            ) : table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  onClick={() => onRowClick?.(row.original)}
                  className={cn(
                    onRowClick && 'cursor-pointer hover:bg-muted/50'
                  )}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-2">
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={columns.length} className="text-center py-8">
                  {emptyMessage}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      
      {showPagination && (
        <DataTablePagination table={table} />
      )}
    </div>
  );
}
```

#### Form Components
```typescript
// components/common/Form/FormField.tsx
import React from 'react';
import { UseFormRegister, FieldError } from 'react-hook-form';
import { cn } from '@/utils/cn';

interface FormFieldProps {
  name: string;
  label: string;
  type?: 'text' | 'email' | 'password' | 'number' | 'date' | 'select' | 'textarea';
  register: UseFormRegister<any>;
  error?: FieldError;
  required?: boolean;
  placeholder?: string;
  options?: { value: string; label: string }[];
  vertical?: 'medical' | 'public';
  className?: string;
}

export const FormField: React.FC<FormFieldProps> = ({
  name,
  label,
  type = 'text',
  register,
  error,
  required,
  placeholder,
  options,
  vertical,
  className,
}) => {
  const fieldClass = cn(
    'w-full rounded-md border border-input bg-background px-3 py-2',
    'focus:outline-none focus:ring-2 focus:ring-ring',
    error && 'border-destructive',
    vertical === 'medical' && 'focus:ring-medical',
    vertical === 'public' && 'focus:ring-public',
    className
  );
  
  return (
    <div className="space-y-2">
      <label htmlFor={name} className="text-sm font-medium">
        {label}
        {required && <span className="text-destructive ml-1">*</span>}
      </label>
      
      {type === 'select' && options ? (
        <select
          id={name}
          className={fieldClass}
          {...register(name, { required })}
        >
          <option value="">Select...</option>
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      ) : type === 'textarea' ? (
        <textarea
          id={name}
          className={fieldClass}
          placeholder={placeholder}
          rows={4}
          {...register(name, { required })}
        />
      ) : (
        <input
          id={name}
          type={type}
          className={fieldClass}
          placeholder={placeholder}
          {...register(name, { required })}
        />
      )}
      
      {error && (
        <p className="text-sm text-destructive">{error.message}</p>
      )}
    </div>
  );
};
```

---

### 2. Layout Components

#### Dashboard Layout
```typescript
// components/common/Layout/DashboardLayout.tsx
import React from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useVertical } from '@/hooks/useVertical';

interface DashboardLayoutProps {
  children: React.ReactNode;
  sidebar?: React.ReactNode;
  header?: React.ReactNode;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  children,
  sidebar,
  header,
}) => {
  const { vertical, theme } = useVertical();
  
  return (
    <div className={cn('min-h-screen bg-background', `theme-${vertical}`)}>
      <Header>
        {header || <DefaultHeader vertical={vertical} />}
      </Header>
      
      <div className="flex h-[calc(100vh-4rem)]">
        <Sidebar>
          {sidebar || <DefaultSidebar vertical={vertical} />}
        </Sidebar>
        
        <main className="flex-1 overflow-y-auto p-6">
          <div className="mx-auto max-w-7xl">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};
```

---

## Vertical-Specific Components

### Medical Components

```typescript
// verticals/medical/components/PatientCard/PatientCard.tsx
import React from 'react';
import { Card, Badge, Avatar } from '@/components/common';
import { MedicalPatient } from '@/verticals/medical/types';
import { calculateAge } from '@/verticals/medical/utils';

interface PatientCardProps {
  patient: MedicalPatient;
  onSelect?: (patient: MedicalPatient) => void;
  showDetails?: boolean;
}

export const PatientCard: React.FC<PatientCardProps> = ({
  patient,
  onSelect,
  showDetails = false,
}) => {
  const age = calculateAge(patient.dateOfBirth);
  const hasAllergies = patient.allergies?.length > 0;
  
  return (
    <Card 
      onClick={() => onSelect?.(patient)}
      className="hover:shadow-lg transition-shadow cursor-pointer"
    >
      <Card.Header>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Avatar 
              name={`${patient.firstName} ${patient.lastName}`}
              size="lg"
            />
            <div>
              <h3 className="font-semibold">
                {patient.firstName} {patient.lastName}
              </h3>
              <p className="text-sm text-muted-foreground">
                MRN: {patient.medicalRecordNumber} | Age: {age}
              </p>
            </div>
          </div>
          
          {hasAllergies && (
            <Badge variant="warning" className="ml-auto">
              <AlertTriangleIcon className="w-3 h-3 mr-1" />
              Allergies
            </Badge>
          )}
        </div>
      </Card.Header>
      
      {showDetails && (
        <Card.Content>
          <dl className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="text-muted-foreground">Blood Type</dt>
              <dd className="font-medium">{patient.bloodType || 'Unknown'}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Insurance</dt>
              <dd className="font-medium">{patient.insuranceProvider || 'None'}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Last Visit</dt>
              <dd className="font-medium">
                {patient.lastVisit ? formatDate(patient.lastVisit) : 'N/A'}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Primary Care</dt>
              <dd className="font-medium">{patient.primaryCarePhysician || 'None'}</dd>
            </div>
          </dl>
        </Card.Content>
      )}
    </Card>
  );
};
```

### Public Components

```typescript
// verticals/public/components/TenderCard/TenderCard.tsx
import React from 'react';
import { Card, Badge, Button } from '@/components/common';
import { PublicTender } from '@/verticals/public/types';
import { calculateDaysUntil, formatCurrency } from '@/verticals/public/utils';

interface TenderCardProps {
  tender: PublicTender;
  onView?: (tender: PublicTender) => void;
  onBid?: (tender: PublicTender) => void;
  userRole?: 'buyer' | 'supplier' | 'public';
}

export const TenderCard: React.FC<TenderCardProps> = ({
  tender,
  onView,
  onBid,
  userRole = 'public',
}) => {
  const daysLeft = calculateDaysUntil(tender.submissionDeadline);
  const isUrgent = daysLeft <= 7;
  
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <Card.Header>
        <div className="flex items-start justify-between">
          <div>
            <Badge variant="secondary" className="mb-2">
              {tender.tenderNumber}
            </Badge>
            <h3 className="font-semibold text-lg line-clamp-2">
              {tender.title}
            </h3>
          </div>
          
          <div className="text-right">
            <p className="text-2xl font-bold">
              {formatCurrency(tender.estimatedValue, tender.currency)}
            </p>
            {isUrgent && (
              <Badge variant="destructive" className="mt-1">
                <ClockIcon className="w-3 h-3 mr-1" />
                {daysLeft} days left
              </Badge>
            )}
          </div>
        </div>
      </Card.Header>
      
      <Card.Content>
        <p className="text-sm text-muted-foreground line-clamp-3 mb-4">
          {tender.description}
        </p>
        
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span className="text-muted-foreground">Authority:</span>
            <span className="ml-2 font-medium">
              {tender.contractingAuthority.name}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">Category:</span>
            <span className="ml-2 font-medium">{tender.category}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Method:</span>
            <span className="ml-2 font-medium">{tender.procurementMethod}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Deadline:</span>
            <span className="ml-2 font-medium">
              {formatDate(tender.submissionDeadline)}
            </span>
          </div>
        </div>
      </Card.Content>
      
      <Card.Footer className="flex justify-end space-x-2">
        <Button variant="outline" size="sm" onClick={() => onView?.(tender)}>
          View Details
        </Button>
        {userRole === 'supplier' && tender.status === 'published' && (
          <Button variant="primary" size="sm" onClick={() => onBid?.(tender)}>
            Submit Bid
          </Button>
        )}
      </Card.Footer>
    </Card>
  );
};
```

---

## Theming System

### Theme Configuration

```typescript
// styles/themes/theme.types.ts
export interface Theme {
  name: string;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    foreground: string;
    muted: string;
    border: string;
    success: string;
    warning: string;
    error: string;
  };
  fonts: {
    sans: string;
    mono: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
  borderRadius: {
    sm: string;
    md: string;
    lg: string;
    full: string;
  };
}
```

### Medical Theme
```typescript
// verticals/medical/theme/medical.theme.ts
export const medicalTheme: Theme = {
  name: 'medical',
  colors: {
    primary: '#0EA5E9',      // Sky blue
    secondary: '#10B981',    // Emerald
    accent: '#06B6D4',       // Cyan
    background: '#FFFFFF',
    foreground: '#0F172A',
    muted: '#F1F5F9',
    border: '#E2E8F0',
    success: '#22C55E',
    warning: '#F59E0B',
    error: '#EF4444',
  },
  fonts: {
    sans: 'Inter, system-ui, sans-serif',
    mono: 'JetBrains Mono, monospace',
  },
  spacing: {
    xs: '0.5rem',
    sm: '1rem',
    md: '1.5rem',
    lg: '2rem',
    xl: '3rem',
  },
  borderRadius: {
    sm: '0.25rem',
    md: '0.5rem',
    lg: '0.75rem',
    full: '9999px',
  },
};
```

### Public Theme
```typescript
// verticals/public/theme/public.theme.ts
export const publicTheme: Theme = {
  name: 'public',
  colors: {
    primary: '#3B82F6',      // Blue
    secondary: '#8B5CF6',    // Purple
    accent: '#6366F1',       // Indigo
    background: '#FFFFFF',
    foreground: '#1E293B',
    muted: '#F8FAFC',
    border: '#CBD5E1',
    success: '#10B981',
    warning: '#F59E0B',
    error: '#DC2626',
  },
  fonts: {
    sans: 'Roboto, system-ui, sans-serif',
    mono: 'Fira Code, monospace',
  },
  spacing: {
    xs: '0.5rem',
    sm: '1rem',
    md: '1.5rem',
    lg: '2rem',
    xl: '3rem',
  },
  borderRadius: {
    sm: '0.125rem',
    md: '0.375rem',
    lg: '0.5rem',
    full: '9999px',
  },
};
```

### Theme Provider
```typescript
// core/theme/ThemeProvider.tsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import { Theme } from '@/styles/themes/theme.types';
import { medicalTheme } from '@/verticals/medical/theme';
import { publicTheme } from '@/verticals/public/theme';

interface ThemeContextValue {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  vertical: 'medical' | 'public';
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ 
  children 
}) => {
  const [vertical, setVertical] = useState<'medical' | 'public'>('medical');
  const [theme, setTheme] = useState<Theme>(medicalTheme);
  
  useEffect(() => {
    // Determine vertical from URL or config
    const currentVertical = window.location.hostname.includes('medical') 
      ? 'medical' 
      : 'public';
    setVertical(currentVertical);
    setTheme(currentVertical === 'medical' ? medicalTheme : publicTheme);
    
    // Apply CSS variables
    applyTheme(theme);
  }, []);
  
  const applyTheme = (theme: Theme) => {
    const root = document.documentElement;
    
    Object.entries(theme.colors).forEach(([key, value]) => {
      root.style.setProperty(`--color-${key}`, value);
    });
    
    Object.entries(theme.spacing).forEach(([key, value]) => {
      root.style.setProperty(`--spacing-${key}`, value);
    });
    
    root.style.setProperty('--font-sans', theme.fonts.sans);
    root.style.setProperty('--font-mono', theme.fonts.mono);
  };
  
  return (
    <ThemeContext.Provider value={{ theme, setTheme, vertical }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};
```

---

## State Management

### Global Store Structure

```typescript
// core/store/store.ts
import { configureStore } from '@reduxjs/toolkit';
import { authReducer } from './slices/auth';
import { uiReducer } from './slices/ui';
import { medicalReducer } from '@/verticals/medical/store';
import { publicReducer } from '@/verticals/public/store';

export const store = configureStore({
  reducer: {
    // Core slices
    auth: authReducer,
    ui: uiReducer,
    
    // Vertical slices (conditionally loaded)
    ...(import.meta.env.VITE_VERTICAL === 'medical' && {
      medical: medicalReducer,
    }),
    ...(import.meta.env.VITE_VERTICAL === 'public' && {
      public: publicReducer,
    }),
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

### Vertical-Specific State

```typescript
// verticals/medical/store/index.ts
import { combineReducers } from '@reduxjs/toolkit';
import { patientsSlice } from './slices/patients';
import { appointmentsSlice } from './slices/appointments';
import { clinicalSlice } from './slices/clinical';

export const medicalReducer = combineReducers({
  patients: patientsSlice.reducer,
  appointments: appointmentsSlice.reducer,
  clinical: clinicalSlice.reducer,
});

// verticals/public/store/index.ts
import { combineReducers } from '@reduxjs/toolkit';
import { tendersSlice } from './slices/tenders';
import { suppliersSlice } from './slices/suppliers';
import { bidsSlice } from './slices/bids';

export const publicReducer = combineReducers({
  tenders: tendersSlice.reducer,
  suppliers: suppliersSlice.reducer,
  bids: bidsSlice.reducer,
});
```

---

## Routing Configuration

### Multi-Vertical Router

```typescript
// core/router/AppRouter.tsx
import React, { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { LoadingScreen } from '@/components/common';

// Lazy load vertical routers
const MedicalRouter = lazy(() => import('@/verticals/medical/router'));
const PublicRouter = lazy(() => import('@/verticals/public/router'));

// Common pages
const Login = lazy(() => import('@/pages/Login'));
const NotFound = lazy(() => import('@/pages/NotFound'));

export const AppRouter: React.FC = () => {
  const { isAuthenticated, user } = useAuth();
  const vertical = import.meta.env.VITE_VERTICAL;
  
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingScreen />}>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          
          {/* Protected routes */}
          {isAuthenticated ? (
            <>
              {/* Redirect root to vertical */}
              <Route path="/" element={<Navigate to={`/${vertical}`} />} />
              
              {/* Medical routes */}
              {vertical === 'medical' && (
                <Route path="/medical/*" element={<MedicalRouter />} />
              )}
              
              {/* Public procurement routes */}
              {vertical === 'public' && (
                <Route path="/public/*" element={<PublicRouter />} />
              )}
            </>
          ) : (
            <Route path="*" element={<Navigate to="/login" />} />
          )}
          
          {/* 404 */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
};
```

### Vertical Router Example

```typescript
// verticals/medical/router/index.tsx
import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { DashboardLayout } from '@/components/common';
import { MedicalSidebar } from '../components/MedicalSidebar';

// Medical pages
import Dashboard from '../pages/Dashboard';
import Patients from '../pages/Patients';
import PatientDetail from '../pages/PatientDetail';
import Appointments from '../pages/Appointments';
import Surgery from '../pages/Surgery';
import Clinical from '../pages/Clinical';

const MedicalRouter: React.FC = () => {
  return (
    <DashboardLayout sidebar={<MedicalSidebar />}>
      <Routes>
        <Route index element={<Dashboard />} />
        <Route path="patients" element={<Patients />} />
        <Route path="patients/:id" element={<PatientDetail />} />
        <Route path="appointments" element={<Appointments />} />
        <Route path="surgery" element={<Surgery />} />
        <Route path="clinical" element={<Clinical />} />
      </Routes>
    </DashboardLayout>
  );
};

export default MedicalRouter;
```

---

## Build Configuration

### Vite Configuration

```typescript
// vite.config.ts
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd());
  const vertical = env.VITE_VERTICAL || 'medical';
  
  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        '@medical': path.resolve(__dirname, './src/verticals/medical'),
        '@public': path.resolve(__dirname, './src/verticals/public'),
      },
    },
    build: {
      outDir: `dist/${vertical}`,
      rollupOptions: {
        input: {
          main: path.resolve(__dirname, 'index.html'),
        },
        output: {
          manualChunks: {
            // Common vendor chunks
            'react-vendor': ['react', 'react-dom', 'react-router-dom'],
            'ui-vendor': ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
            
            // Vertical-specific chunks
            ...(vertical === 'medical' && {
              'medical-vendor': ['@/verticals/medical'],
            }),
            ...(vertical === 'public' && {
              'public-vendor': ['@/verticals/public'],
            }),
          },
        },
      },
    },
    server: {
      port: vertical === 'medical' ? 3001 : 3002,
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  };
});
```

### Package.json Scripts

```json
{
  "scripts": {
    "dev:medical": "VITE_VERTICAL=medical vite",
    "dev:public": "VITE_VERTICAL=public vite",
    "build:medical": "VITE_VERTICAL=medical vite build",
    "build:public": "VITE_VERTICAL=public vite build",
    "build:all": "npm run build:medical && npm run build:public",
    "preview:medical": "VITE_VERTICAL=medical vite preview",
    "preview:public": "VITE_VERTICAL=public vite preview",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "lint": "eslint src --ext ts,tsx",
    "type-check": "tsc --noEmit",
    "storybook": "storybook dev -p 6006",
    "build-storybook": "storybook build"
  }
}
```

---

## Shared Hooks

### useVertical Hook

```typescript
// core/hooks/useVertical.ts
export const useVertical = () => {
  const vertical = import.meta.env.VITE_VERTICAL as 'medical' | 'public';
  const theme = vertical === 'medical' ? medicalTheme : publicTheme;
  
  const config = {
    medical: {
      name: 'Medical Hub',
      logo: '/medical/logo.svg',
      primaryColor: '#0EA5E9',
      features: ['patients', 'appointments', 'clinical'],
    },
    public: {
      name: 'Public Hub',
      logo: '/public/logo.svg',
      primaryColor: '#3B82F6',
      features: ['tenders', 'suppliers', 'contracts'],
    },
  };
  
  return {
    vertical,
    theme,
    config: config[vertical],
    isMedical: vertical === 'medical',
    isPublic: vertical === 'public',
  };
};
```

### useFeatureFlag Hook

```typescript
// core/hooks/useFeatureFlag.ts
export const useFeatureFlag = (feature: string): boolean => {
  const { vertical, config } = useVertical();
  const { user } = useAuth();
  
  // Check vertical-specific features
  if (!config.features.includes(feature)) {
    return false;
  }
  
  // Check organization-specific features
  if (user?.organization?.enabledFeatures) {
    return user.organization.enabledFeatures.includes(feature);
  }
  
  return false;
};
```

---

## Testing Strategy

### Component Testing

```typescript
// components/common/Button/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button Component', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });
  
  it('applies vertical theme correctly', () => {
    const { container } = render(
      <Button vertical="medical">Medical Button</Button>
    );
    expect(container.firstChild).toHaveClass('shadow-medical');
  });
  
  it('shows loading spinner when isLoading', () => {
    render(<Button isLoading>Loading</Button>);
    expect(screen.getByTestId('spinner')).toBeInTheDocument();
  });
});
```

### Vertical-Specific Testing

```typescript
// verticals/medical/components/PatientCard/PatientCard.test.tsx
import { render, screen } from '@testing-library/react';
import { PatientCard } from './PatientCard';
import { mockPatient } from '@/verticals/medical/test-utils';

describe('PatientCard Component', () => {
  it('displays patient information correctly', () => {
    render(<PatientCard patient={mockPatient} />);
    
    expect(screen.getByText(`${mockPatient.firstName} ${mockPatient.lastName}`))
      .toBeInTheDocument();
    expect(screen.getByText(`MRN: ${mockPatient.medicalRecordNumber}`))
      .toBeInTheDocument();
  });
  
  it('shows allergy warning when patient has allergies', () => {
    const patientWithAllergies = {
      ...mockPatient,
      allergies: ['Penicillin', 'Peanuts'],
    };
    
    render(<PatientCard patient={patientWithAllergies} />);
    expect(screen.getByText('Allergies')).toBeInTheDocument();
  });
});
```

---

## Storybook Configuration

```typescript
// .storybook/preview.tsx
import type { Preview } from '@storybook/react';
import { ThemeProvider } from '../src/core/theme/ThemeProvider';
import '../src/styles/globals.css';

const preview: Preview = {
  parameters: {
    actions: { argTypesRegex: '^on[A-Z].*' },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/,
      },
    },
  },
  decorators: [
    (Story, context) => {
      const vertical = context.globals.vertical || 'medical';
      return (
        <ThemeProvider vertical={vertical}>
          <Story />
        </ThemeProvider>
      );
    },
  ],
  globalTypes: {
    vertical: {
      name: 'Vertical',
      description: 'Choose vertical theme',
      defaultValue: 'medical',
      toolbar: {
        icon: 'globe',
        items: [
          { value: 'medical', title: 'Medical Hub' },
          { value: 'public', title: 'Public Hub' },
        ],
      },
    },
  },
};

export default preview;
```

---

## Performance Optimizations

### Code Splitting

```typescript
// Lazy load heavy components
const HeavyChart = lazy(() => 
  import(/* webpackChunkName: "charts" */ '@/components/charts/HeavyChart')
);

// Conditional loading based on vertical
const VerticalComponent = lazy(() => {
  const vertical = import.meta.env.VITE_VERTICAL;
  return import(`@/verticals/${vertical}/components/SpecialComponent`);
});
```

### Memoization

```typescript
// Memoize expensive computations
export const ExpensiveList = memo(({ items, filter }) => {
  const filteredItems = useMemo(() => 
    items.filter(item => item.name.includes(filter)),
    [items, filter]
  );
  
  return (
    <VirtualList
      items={filteredItems}
      renderItem={(item) => <ItemCard key={item.id} item={item} />}
    />
  );
});
```

---

## Summary

This frontend component library architecture provides:

1. **Shared Component Library**: Reusable components across all verticals
2. **Vertical Extensions**: Easy extension of common components for specific needs
3. **Theming System**: Consistent theming with vertical-specific customization
4. **State Management**: Modular state with vertical-specific slices
5. **Build Configuration**: Optimized builds for each vertical
6. **Testing Strategy**: Comprehensive testing for shared and vertical components
7. **Performance**: Code splitting and lazy loading for optimal performance
8. **Developer Experience**: Clear patterns and strong typing with TypeScript

The architecture scales from 2 to N verticals while maintaining clean separation and maximum code reuse.