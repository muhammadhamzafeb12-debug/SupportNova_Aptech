import React from 'react';

interface SkeletonProps {
  rows?: number;
  height?: string;
  className?: string;
}

export const SkeletonLoader: React.FC<SkeletonProps> = ({ rows = 3, height = 'h-12', className = '' }) => {
  return (
    <div className={`space-y-3 w-full ${className}`}>
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className={`w-full ${height} rounded-xl skeleton-shimmer border border-slate-800/60`}
        />
      ))}
    </div>
  );
};
