import React, { useEffect } from 'react';

export const ManagerDashboardPage: React.FC = () => {
  useEffect(() => {
    // Redirect to the actual manager dashboard HTML file
    window.location.href = '/src/web_portal/manager_dashboard.html';
  }, []);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-green-600 mx-auto mb-4"></div>
        <p className="text-lg text-gray-600">Redirecting to Manager Dashboard...</p>
      </div>
    </div>
  );
};
