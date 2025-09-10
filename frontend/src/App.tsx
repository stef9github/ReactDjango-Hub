import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ApolloClient, InMemoryCache, ApolloProvider } from '@apollo/client';
import { ThemeProvider } from '@/lib/theme';
import { AuthProvider, useAuth } from '@/lib/auth';
import { Alert } from '@/lib/ui/atoms';

// Lazy load pages for better performance
const HomePage = React.lazy(() => import('./pages/HomePage'));
const LoginPage = React.lazy(() => import('./pages/auth/LoginPage'));
const RegisterPage = React.lazy(() => import('./pages/auth/RegisterPage'));
const DashboardPage = React.lazy(() => import('./pages/DashboardPage'));

// Create clients
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const apolloClient = new ApolloClient({
  uri: import.meta.env.VITE_GRAPHQL_URL || 'http://localhost:8000/graphql',
  cache: new InMemoryCache(),
});

// Loading component
const LoadingSpinner = () => (
  <div className="min-h-screen flex items-center justify-center bg-surface-background">
    <div className="text-center">
      <div className="w-12 h-12 mx-auto mb-4 border-4 border-semantic-primary-200 border-t-semantic-primary-500 rounded-full animate-spin" />
      <p className="text-text-on-surface-variant">Loading...</p>
    </div>
  </div>
);

// Error boundary component
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('App Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-surface-background p-4">
          <div className="max-w-md w-full">
            <Alert
              variant="error"
              title="Something went wrong"
              description="The application encountered an unexpected error. Please refresh the page or contact support if the problem persists."
              actions={
                <button
                  onClick={() => window.location.reload()}
                  className="px-4 py-2 bg-semantic-primary-500 text-text-on-primary rounded-md text-sm font-medium hover:bg-semantic-primary-600 transition-colors"
                >
                  Reload Page
                </button>
              }
            />
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Protected Route component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading, isInitialized } = useAuth();

  if (!isInitialized || isLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

// Guest Route component (redirect authenticated users)
const GuestRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading, isInitialized } = useAuth();

  if (!isInitialized || isLoading) {
    return <LoadingSpinner />;
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

// App Routes component
const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route 
        path="/" 
        element={
          <Suspense fallback={<LoadingSpinner />}>
            <HomePage />
          </Suspense>
        } 
      />

      {/* Guest-only Routes */}
      <Route 
        path="/login" 
        element={
          <GuestRoute>
            <Suspense fallback={<LoadingSpinner />}>
              <LoginPage />
            </Suspense>
          </GuestRoute>
        } 
      />
      <Route 
        path="/register" 
        element={
          <GuestRoute>
            <Suspense fallback={<LoadingSpinner />}>
              <RegisterPage />
            </Suspense>
          </GuestRoute>
        } 
      />

      {/* Protected Routes */}
      <Route 
        path="/dashboard" 
        element={
          <ProtectedRoute>
            <Suspense fallback={<LoadingSpinner />}>
              <DashboardPage />
            </Suspense>
          </ProtectedRoute>
        } 
      />

      {/* Catch-all redirect */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

// Main App component
function App() {
  return (
    <ErrorBoundary>
      <ApolloProvider client={apolloClient}>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider
            defaultColorMode="system"
            defaultAppTheme="default"
          >
            <AuthProvider autoInitialize={true}>
              <BrowserRouter>
                <div className="min-h-screen bg-surface-background text-text-on-background">
                  <AppRoutes />
                </div>
              </BrowserRouter>
            </AuthProvider>
          </ThemeProvider>
        </QueryClientProvider>
      </ApolloProvider>
    </ErrorBoundary>
  );
}

export default App;
