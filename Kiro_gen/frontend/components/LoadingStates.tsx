'use client';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function LoadingSpinner({ size = 'md', className = '' }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
  };

  return (
    <svg
      className={`animate-spin ${sizeClasses[size]} ${className}`}
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
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
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}

interface LoadingCardProps {
  title?: string;
  message?: string;
  showProgress?: boolean;
  progress?: number;
}

export function LoadingCard({ 
  title = 'Loading...', 
  message = 'Please wait while we process your request.',
  showProgress = false,
  progress = 0 
}: LoadingCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
      <div className="flex items-center justify-center space-x-3 mb-4">
        <LoadingSpinner size="lg" className="text-blue-600" />
        <span className="text-lg font-medium text-gray-900">{title}</span>
      </div>
      
      <p className="text-gray-600 mb-4">{message}</p>
      
      {showProgress && (
        <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
            role="progressbar"
            aria-valuenow={progress}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
      )}
      
      {showProgress && (
        <p className="text-sm text-gray-500" aria-live="polite">
          {progress}% complete
        </p>
      )}
    </div>
  );
}

interface SkeletonProps {
  className?: string;
  rows?: number;
}

export function Skeleton({ className = '', rows = 1 }: SkeletonProps) {
  return (
    <div className={`animate-pulse ${className}`}>
      {Array.from({ length: rows }).map((_, index) => (
        <div
          key={index}
          className={`bg-gray-200 rounded ${index > 0 ? 'mt-2' : ''}`}
          style={{ height: '1rem' }}
        />
      ))}
    </div>
  );
}

export function LibraryCardSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow-sm border p-6 animate-pulse">
      <div className="flex items-start justify-between mb-4">
        <div className="h-4 w-4 bg-gray-200 rounded" />
        <div className="h-6 w-16 bg-gray-200 rounded-full" />
      </div>
      
      <div className="h-6 bg-gray-200 rounded mb-4" />
      
      <div className="space-y-3 mb-4">
        <div>
          <div className="h-3 w-20 bg-gray-200 rounded mb-1" />
          <div className="flex gap-1">
            <div className="h-6 w-16 bg-gray-200 rounded-full" />
            <div className="h-6 w-20 bg-gray-200 rounded-full" />
            <div className="h-6 w-12 bg-gray-200 rounded-full" />
          </div>
        </div>
        
        <div>
          <div className="h-3 w-16 bg-gray-200 rounded mb-1" />
          <div className="flex gap-1">
            <div className="h-6 w-14 bg-gray-200 rounded-full" />
            <div className="h-6 w-18 bg-gray-200 rounded-full" />
          </div>
        </div>
      </div>
      
      <div className="h-3 w-24 bg-gray-200 rounded mb-4" />
      
      <div className="flex items-center space-x-2">
        <div className="flex-1 h-8 bg-gray-200 rounded" />
        <div className="h-8 w-8 bg-gray-200 rounded" />
        <div className="h-8 w-8 bg-gray-200 rounded" />
      </div>
    </div>
  );
}

export function AudioPlayerSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow-sm border p-6 space-y-4 animate-pulse">
      <div className="text-center">
        <div className="h-6 w-48 bg-gray-200 rounded mx-auto mb-2" />
        <div className="h-4 w-24 bg-gray-200 rounded mx-auto" />
      </div>
      
      <div className="space-y-2">
        <div className="w-full h-2 bg-gray-200 rounded-full" />
      </div>
      
      <div className="flex items-center justify-center space-x-4">
        <div className="h-10 w-10 bg-gray-200 rounded-full" />
        <div className="h-12 w-12 bg-gray-200 rounded-full" />
        <div className="h-10 w-10 bg-gray-200 rounded-full" />
      </div>
      
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="h-5 w-5 bg-gray-200 rounded" />
          <div className="h-2 w-20 bg-gray-200 rounded" />
        </div>
        <div className="flex items-center space-x-2">
          <div className="h-4 w-12 bg-gray-200 rounded" />
          <div className="h-8 w-16 bg-gray-200 rounded" />
        </div>
      </div>
    </div>
  );
}