"use client";

import React from "react";

interface SpinnerProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function Spinner({ size = "md", className = "" }: SpinnerProps) {
  const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-8 w-8",
    lg: "h-12 w-12",
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

interface LoadingOverlayProps {
  message?: string;
}

export function LoadingOverlay({
  message = "Loading...",
}: LoadingOverlayProps) {
  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      role="status"
      aria-live="polite"
    >
      <div className="bg-white rounded-lg p-8 flex flex-col items-center shadow-xl">
        <Spinner size="lg" className="text-blue-600" />
        <p className="mt-4 text-gray-700 font-medium">{message}</p>
      </div>
    </div>
  );
}

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className = "" }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse bg-gray-200 rounded ${className}`}
      aria-hidden="true"
    />
  );
}

export function LibraryItemSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow-sm border p-4 space-y-3">
      <div className="flex items-start justify-between">
        <Skeleton className="h-6 w-2/3" />
        <Skeleton className="h-6 w-16" />
      </div>
      <Skeleton className="h-4 w-1/2" />
      <div className="flex gap-2">
        <Skeleton className="h-6 w-16 rounded-full" />
        <Skeleton className="h-6 w-20 rounded-full" />
        <Skeleton className="h-6 w-14 rounded-full" />
      </div>
      <div className="flex items-center justify-between pt-2">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-8 w-20 rounded-md" />
      </div>
    </div>
  );
}

export function LibraryGridSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
      aria-label="Loading library items"
      role="status"
    >
      <span className="sr-only">Loading library items...</span>
      {Array.from({ length: count }).map((_, i) => (
        <LibraryItemSkeleton key={i} />
      ))}
    </div>
  );
}

export function PageLoadingState({
  message = "Loading...",
}: {
  message?: string;
}) {
  return (
    <div
      className="min-h-[400px] flex flex-col items-center justify-center"
      role="status"
      aria-live="polite"
    >
      <Spinner size="lg" className="text-blue-600" />
      <p className="mt-4 text-gray-600">{message}</p>
    </div>
  );
}

interface ProgressBarProps {
  progress: number;
  label?: string;
  showPercentage?: boolean;
}

export function ProgressBar({
  progress,
  label,
  showPercentage = true,
}: ProgressBarProps) {
  const percentage = Math.min(100, Math.max(0, progress));

  return (
    <div className="w-full">
      {(label || showPercentage) && (
        <div className="flex justify-between mb-1">
          {label && <span className="text-sm text-gray-600">{label}</span>}
          {showPercentage && (
            <span className="text-sm text-gray-600" aria-hidden="true">
              {percentage.toFixed(0)}%
            </span>
          )}
        </div>
      )}
      <div
        className="w-full bg-gray-200 rounded-full h-2.5"
        role="progressbar"
        aria-valuenow={percentage}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label || "Progress"}
      >
        <div
          className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

interface InlineLoadingProps {
  message?: string;
  className?: string;
}

export function InlineLoading({
  message = "Loading...",
  className = "",
}: InlineLoadingProps) {
  return (
    <div
      className={`flex items-center ${className}`}
      role="status"
      aria-live="polite"
    >
      <Spinner size="sm" className="text-blue-600 mr-2" />
      <span className="text-sm text-gray-600">{message}</span>
    </div>
  );
}
