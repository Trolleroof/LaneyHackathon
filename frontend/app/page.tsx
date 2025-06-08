'use client';

import { useAuth } from '@/contexts/AuthContext';
import LandingPage from '@/components/LandingPage';
import AuthenticatedApp from '@/components/AuthenticatedApp';

export default function HomePage() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return user ? <AuthenticatedApp /> : <LandingPage />;
} 