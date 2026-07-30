import React from 'react';

export const Loading: React.FC = () => {
  return (
    <div className="flex items-center justify-center p-12 space-x-3 text-blue-600">
      <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
      <span className="text-xs font-semibold text-slate-600">Loading Agent WAF Telemetry...</span>
    </div>
  );
};
