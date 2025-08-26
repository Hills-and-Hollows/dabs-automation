import React, { useEffect } from 'react';

export const CustomersPage: React.FC = () => {
  useEffect(() => {
    // Redirect to the actual restaurant portal (which includes customer functionality)
    window.location.href = '/src/web_portal/restaurant_portal_with_catalog.html';
  }, []);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-purple-600 mx-auto mb-4"></div>
        <p className="text-lg text-gray-600">Redirecting to Customer Portal...</p>
      </div>
    </div>
  );
};
