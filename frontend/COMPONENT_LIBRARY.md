# ReactDjango Hub - Authentication Component Library

A comprehensive, reusable authentication component library built with React 18, TypeScript, and Tailwind CSS. Designed for maximum reusability across multiple applications with medical UI/UX compliance.

## 🏗️ Architecture Overview

### Atomic Design Pattern

Our component library follows atomic design principles for maximum reusability and maintainability:

```
lib/
├── theme/           # Theme system and design tokens
├── ui/
│   ├── atoms/       # Basic building blocks (Button, Input, Card)
│   ├── molecules/   # Compound components (LoginForm, RegisterForm)
│   └── organisms/   # Complete sections (AuthPortal)
├── auth/            # Authentication context and hooks
├── api/             # API client and utilities
└── utils/           # Utility functions
```

### Design System Features

- **Multi-App Theming**: CSS custom properties for dynamic theming
- **Medical UI/UX**: WCAG 2.1 compliant, accessible components
- **Responsive Design**: Mobile-first approach with breakpoint utilities
- **Type Safety**: Full TypeScript coverage with comprehensive type definitions
- **Modern Stack**: React 19, Vite, Tailwind CSS 4.0

## 🎨 Theme System

### Design Tokens

The theme system uses CSS custom properties for dynamic theming:

```typescript
import { ThemeProvider, useTheme } from '@/lib/theme';

// Wrap your app
<ThemeProvider 
  defaultColorMode="system"
  defaultAppTheme="medical"
>
  <App />
</ThemeProvider>

// Use in components
const { toggleColorMode, setAppTheme } = useTheme();
```

### Available Themes

- **`default`**: Standard business application theme
- **`medical`**: Healthcare/medical application theme with enhanced accessibility
- **`custom`**: Fully customizable theme with your own tokens

### Color Modes

- **`light`**: Light theme
- **`dark`**: Dark theme
- **`system`**: Follows system preference

## 🧩 Component Library

### Atoms (Basic Components)

#### Button
```tsx
import { Button } from '@/lib/ui/atoms';

<Button 
  variant="primary"
  size="lg"
  loading={isSubmitting}
  loadingText="Signing in..."
>
  Sign In
</Button>
```

**Variants**: `primary`, `secondary`, `outline`, `ghost`, `success`, `warning`, `error`, `link`
**Sizes**: `xs`, `sm`, `md`, `lg`, `xl`, `icon`

#### Input
```tsx
import { Input } from '@/lib/ui/atoms';

<Input
  type="email"
  label="Email address"
  placeholder="Enter your email"
  errorText="Email is required"
  showPasswordToggle={type === 'password'}
  leftIcon={<EmailIcon />}
/>
```

**Features**: Password toggle, validation states, icons, accessibility

#### Card
```tsx
import { Card, CardHeader, CardTitle, CardContent } from '@/lib/ui/atoms';

<Card variant="elevated" interactive>
  <CardHeader>
    <CardTitle>Welcome</CardTitle>
  </CardHeader>
  <CardContent>
    <p>Card content here</p>
  </CardContent>
</Card>
```

#### Alert
```tsx
import { Alert } from '@/lib/ui/atoms';

<Alert 
  variant="error"
  title="Authentication Failed"
  description="Invalid credentials"
  closeable
  onClose={() => handleClose()}
/>
```

#### Badge
```tsx
import { Badge, StatusBadge } from '@/lib/ui/atoms';

<Badge variant="success" dot>Active</Badge>
<StatusBadge status="pending" />
```

### Molecules (Compound Components)

#### LoginForm
```tsx
import { LoginForm } from '@/lib/ui/molecules';

<LoginForm
  onSuccess={handleLoginSuccess}
  onError={handleLoginError}
  showRememberMe={true}
  showForgotPassword={true}
  onForgotPassword={() => navigateToReset()}
  onRegister={() => navigateToRegister()}
/>
```

#### RegisterForm
```tsx
import { RegisterForm } from '@/lib/ui/molecules';

<RegisterForm
  onSuccess={handleRegisterSuccess}
  onError={handleRegisterError}
  requirePhoneNumber={false}
  showPasswordStrength={true}
  onLogin={() => navigateToLogin()}
/>
```

#### ForgotPasswordForm
```tsx
import { ForgotPasswordForm } from '@/lib/ui/molecules';

<ForgotPasswordForm
  onSuccess={handleResetSuccess}
  onBackToLogin={() => navigateToLogin()}
/>
```

#### EmailVerificationForm
```tsx
import { EmailVerificationForm } from '@/lib/ui/molecules';

<EmailVerificationForm
  email="user@example.com"
  onSuccess={handleVerificationSuccess}
  onResendVerification={handleResendVerification}
/>
```

### Organisms (Complete Sections)

#### AuthPortal
```tsx
import { AuthPortal, MedicalAuthPortal } from '@/lib/ui/organisms';

// Standard portal
<AuthPortal
  initialFlow="login"
  onAuthSuccess={() => navigate('/dashboard')}
  allowRegistration={true}
  requireEmailVerification={true}
/>

// Medical preset
<MedicalAuthPortal
  onAuthSuccess={() => navigate('/dashboard')}
/>
```

**Presets Available**:
- `MedicalAuthPortal`: Healthcare applications
- `BusinessAuthPortal`: Standard business applications  
- `ConsumerAuthPortal`: Consumer applications
- `SecurityAuthPortal`: High-security applications

## 🔐 Authentication System

### Auth Context & Hooks

```tsx
import { AuthProvider, useAuth } from '@/lib/auth';

// Wrap your app
<AuthProvider autoInitialize={true}>
  <App />
</AuthProvider>

// Use in components
const { 
  user, 
  isAuthenticated, 
  login, 
  register, 
  logout 
} = useAuth();
```

### Specialized Hooks

```tsx
import { 
  useLoginForm,
  useRegisterForm,
  usePasswordStrength,
  useEmailVerification 
} from '@/lib/auth';

// Form hooks with validation
const {
  data,
  errors,
  handleSubmit,
  handleChange
} = useLoginForm();

// Password strength checker
const strength = usePasswordStrength(password);
```

### Route Protection

```tsx
import { useRequireAuth, useGuestOnly } from '@/lib/auth';

// Protected routes
function Dashboard() {
  const auth = useRequireAuth(); // Redirects if not authenticated
  return <div>Dashboard content</div>;
}

// Guest-only routes  
function Login() {
  const auth = useGuestOnly(); // Redirects if authenticated
  return <LoginForm />;
}
```

## 🌐 API Integration

### API Client

```tsx
import { apiClient, ApiException } from '@/lib/api';

try {
  const user = await apiClient.login({
    email: 'user@example.com',
    password: 'password'
  });
  console.log('Login successful:', user);
} catch (error) {
  if (error instanceof ApiException) {
    console.error('API Error:', error.message, error.status);
  }
}
```

### Available Methods

```typescript
// Authentication
await apiClient.register(userData);
await apiClient.login(credentials);
await apiClient.verifyEmail(token);
await apiClient.resendVerification(email);
await apiClient.forgotPassword(email);
await apiClient.resetPassword(data);

// User Management
await apiClient.getCurrentUser();
await apiClient.updateProfile(data);
await apiClient.changePassword(data);

// Token Management
await apiClient.refreshToken(refreshToken);
await apiClient.logout();
```

## 🎯 Usage Examples

### Basic Authentication Flow

```tsx
import React from 'react';
import { AuthProvider } from '@/lib/auth';
import { ThemeProvider } from '@/lib/theme';
import { AuthPortal } from '@/lib/ui/organisms';

function App() {
  return (
    <ThemeProvider defaultAppTheme="medical">
      <AuthProvider>
        <div className="min-h-screen bg-surface-background">
          <AuthPortal 
            initialFlow="login"
            onAuthSuccess={() => window.location.href = '/dashboard'}
          />
        </div>
      </AuthProvider>
    </ThemeProvider>
  );
}
```

### Custom Theme Integration

```tsx
import { ThemeProvider, createThemeConfig } from '@/lib/theme';

const customTheme = createThemeConfig('medical', {
  customTokens: {
    colors: {
      semantic: {
        primary: {
          500: '#2563eb', // Custom primary color
        },
      },
    },
  },
});

<ThemeProvider {...customTheme}>
  <App />
</ThemeProvider>
```

### Multi-App Component Reuse

```tsx
// App A (Medical)
import { MedicalAuthPortal } from '@/lib/ui/organisms';

<MedicalAuthPortal 
  logoSrc="/medical-logo.png"
  onAuthSuccess={() => navigate('/patients')}
/>

// App B (Business)
import { BusinessAuthPortal } from '@/lib/ui/organisms';

<BusinessAuthPortal
  logoSrc="/business-logo.png" 
  onAuthSuccess={() => navigate('/dashboard')}
/>
```

## 🎨 Styling & Customization

### CSS Custom Properties

The theme system exposes CSS custom properties for easy customization:

```css
:root {
  --colors-semantic-primary-500: #3b82f6;
  --colors-surface-background: #ffffff;
  --typography-font-family-sans: 'Inter', sans-serif;
  --border-radius-md: 0.375rem;
}
```

### Tailwind Integration

Components use Tailwind classes with theme-aware utilities:

```tsx
// Theme-aware classes
<div className="bg-surface-background text-text-on-surface">
  <Button className="bg-semantic-primary-500 hover:bg-semantic-primary-600">
    Custom Button
  </Button>
</div>
```

## 📱 Responsive Design

All components are mobile-first and fully responsive:

```tsx
<Card className="w-full max-w-md mx-auto sm:max-w-lg lg:max-w-xl">
  <LoginForm />
</Card>
```

## ♿ Accessibility

- **WCAG 2.1 AA Compliant**: All components meet accessibility standards
- **Keyboard Navigation**: Full keyboard support
- **Screen Reader Support**: Proper ARIA labels and semantic HTML
- **Focus Management**: Logical focus flow and visible focus indicators
- **Color Contrast**: Meets medical UI requirements

## 🧪 Testing Integration

```tsx
import { render, screen } from '@testing-library/react';
import { AuthProvider } from '@/lib/auth';
import { LoginForm } from '@/lib/ui/molecules';

test('renders login form', () => {
  render(
    <AuthProvider>
      <LoginForm onSubmit={mockSubmit} />
    </AuthProvider>
  );
  
  expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
});
```

## 🚀 Getting Started

1. **Install Dependencies**
```bash
npm install
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your API endpoints
```

3. **Start Development Server**
```bash
npm run dev
```

4. **Start Identity Service**
```bash
cd ../services/identity-service
python main.py
```

The authentication portal will be available at `http://localhost:5173` with the identity service API at `http://localhost:8001`.

## 📦 Export Structure

```typescript
// Main library exports
export * from '@/lib/theme';      // Theme system
export * from '@/lib/auth';       // Authentication
export * from '@/lib/api';        // API client
export * from '@/lib/ui/atoms';   // Base components
export * from '@/lib/ui/molecules'; // Compound components
export * from '@/lib/ui/organisms'; // Complete sections
```

This component library provides everything needed for a production-ready authentication system with enterprise-grade security, accessibility, and user experience.