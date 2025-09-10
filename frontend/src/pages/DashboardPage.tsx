/**
 * DashboardPage - Protected Dashboard
 * Main application dashboard requiring authentication
 */

import React from 'react';
import { useAuth } from '@/lib/auth';
import { Button, Card, CardHeader, CardTitle, CardContent, Badge, StatsCard } from '@/lib/ui/atoms';

export const DashboardPage: React.FC = () => {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return (
    <div className="min-h-screen bg-surface-background">
      {/* Header */}
      <header className="bg-surface-surface border-b border-border-default">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-semibold text-text-on-surface">
                ReactDjango Hub
              </h1>
              <Badge variant="success" size="sm">
                Authenticated
              </Badge>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="text-sm text-text-on-surface-variant">
                Welcome, <span className="font-medium text-text-on-surface">{user?.first_name}</span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleLogout}
              >
                Sign Out
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-text-on-surface mb-2">
            Welcome back, {user?.first_name}!
          </h2>
          <p className="text-text-on-surface-variant">
            Your authentication system is working perfectly. Here's your dashboard overview.
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatsCard
            title="API Status"
            value="Online"
            description="Identity Service"
            color="success"
            icon={
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
            trend="up"
            trendValue="+100%"
          />
          
          <StatsCard
            title="Auth Method"
            value="JWT"
            description="Secure tokens"
            color="info"
            icon={
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            }
          />
          
          <StatsCard
            title="Theme"
            value="Dynamic"
            description="Multi-app support"
            color="default"
            icon={
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zM21 5a2 2 0 00-2-2h-4a2 2 0 00-2 2v12a4 4 0 004 4h4a2 2 0 002-2V5z" />
              </svg>
            }
          />
          
          <StatsCard
            title="Components"
            value="25+"
            description="Reusable UI library"
            color="warning"
            icon={
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14-7H5a2 2 0 00-2 2v12a2 2 0 002 2h14a2 2 0 002-2V6a2 2 0 00-2-2z" />
              </svg>
            }
          />
        </div>

        {/* Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* User Profile Card */}
          <Card variant="elevated">
            <CardHeader>
              <CardTitle>User Profile</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="space-y-4">
                <div>
                  <dt className="text-sm font-medium text-text-on-surface-variant">Full Name</dt>
                  <dd className="text-text-on-surface">{user?.first_name} {user?.last_name}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-text-on-surface-variant">Email</dt>
                  <dd className="text-text-on-surface">{user?.email}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-text-on-surface-variant">Status</dt>
                  <dd>
                    <Badge 
                      variant={user?.is_verified ? "success" : "warning"}
                      size="sm"
                    >
                      {user?.is_verified ? "Verified" : "Pending Verification"}
                    </Badge>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-text-on-surface-variant">Account Status</dt>
                  <dd>
                    <Badge 
                      variant={user?.status === 'active' ? "success" : "secondary"}
                      size="sm"
                    >
                      {user?.status?.charAt(0).toUpperCase() + user?.status?.slice(1)}
                    </Badge>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-text-on-surface-variant">Joined</dt>
                  <dd className="text-text-on-surface">
                    {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          {/* System Information */}
          <Card variant="elevated">
            <CardHeader>
              <CardTitle>System Information</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="space-y-4">
                <div>
                  <dt className="text-sm font-medium text-text-on-surface-variant">Frontend</dt>
                  <dd className="text-text-on-surface">React 19 + TypeScript + Vite</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-text-on-surface-variant">Backend API</dt>
                  <dd className="text-text-on-surface">FastAPI Identity Service</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-text-on-surface-variant">UI Components</dt>
                  <dd className="text-text-on-surface">Atomic Design + Tailwind CSS</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-text-on-surface-variant">Theme System</dt>
                  <dd className="text-text-on-surface">Multi-app CSS Custom Properties</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-text-on-surface-variant">Features</dt>
                  <dd className="flex flex-wrap gap-2 mt-1">
                    <Badge variant="primary" size="xs">Authentication</Badge>
                    <Badge variant="success" size="xs">Theming</Badge>
                    <Badge variant="info" size="xs">Reusable Components</Badge>
                    <Badge variant="warning" size="xs">Medical UI/UX</Badge>
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>
        </div>

        {/* Action Buttons */}
        <div className="mt-8 flex flex-wrap gap-4">
          <Button variant="primary">
            Explore Components
          </Button>
          <Button variant="outline">
            View Documentation
          </Button>
          <Button variant="ghost">
            Change Theme
          </Button>
        </div>
      </main>
    </div>
  );
};

export default DashboardPage;