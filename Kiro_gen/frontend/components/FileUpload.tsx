'use client';

import { useState, useRef, useCallback } from 'react';
import { useAppStore } from '@/lib/store';
import { apiClient } from '@/lib/api-client';

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const ALLOWED_TYPES = ['application/pdf'];
const ALLOWED_EXTENSIONS = ['.pdf'];

interface FileUploadProps {
  onUploadComplete?: (jobId: string) => void;
}

export function FileUpload({ onUploadComplete }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);
  
  const {
    isUploading,
    uploadProgress,
    uploadError,
    setUploading,
    setUploadProgress,
    setUploadError,
  } = useAppStore();

  const validateFile = useCallback((file: File): string | null => {
    // Check file type
    if (!ALLOWED_TYPES.includes(file.type)) {
      // Also check file extension as fallback
      const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
      if (!ALLOWED_EXTENSIONS.includes(extension)) {
        return 'Only PDF files are supported. Please select a valid PDF file.';
      }
    }
    
    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return `File size must be less than ${MAX_FILE_SIZE / 1024 / 1024}MB. Your file is ${(file.size / 1024 / 1024).toFixed(1)}MB.`;
    }
    
    // Check if file is empty
    if (file.size === 0) {
      return 'The selected file is empty. Please select a valid PDF file.';
    }
    
    return null;
  }, []);

  const handleUpload = useCallback(async (file: File) => {
    const error = validateFile(file);
    if (error) {
      setUploadError(error);
      setSelectedFile(null);
      return;
    }

    setUploadError(null);
    setSelectedFile(file);
    setUploading(true);
    setUploadProgress(0);

    try {
      // Simulate progress for better UX
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => Math.min(prev + 10, 90));
      }, 200);

      const result = await apiClient.uploadPdf(file);

      clearInterval(progressInterval);
      setUploadProgress(100);

      setTimeout(() => {
        setUploading(false);
        setUploadProgress(0);
        setSelectedFile(null);
        onUploadComplete?.(result.job_id);
      }, 500);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Upload failed. Please try again.';
      setUploadError(errorMessage);
      setUploading(false);
      setUploadProgress(0);
      setSelectedFile(null);
    }
  }, [validateFile, setUploadError, setUploading, setUploadProgress, onUploadComplete]);

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 1) {
      setUploadError('Please select only one PDF file at a time.');
      return;
    }
    
    if (files.length > 0) {
      handleUpload(files[0]);
    }
  }, [handleUpload, setUploadError]);

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    // Only set dragging to false if we're leaving the drop zone entirely
    if (dropZoneRef.current && !dropZoneRef.current.contains(e.relatedTarget as Node)) {
      setIsDragging(false);
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.currentTarget.files;
    if (files && files.length > 0) {
      handleUpload(files[0]);
    }
    // Reset the input value so the same file can be selected again
    e.currentTarget.value = '';
  }, [handleUpload]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      if (!isUploading) {
        fileInputRef.current?.click();
      }
    }
  }, [isUploading]);

  const clearError = useCallback(() => {
    setUploadError(null);
  }, [setUploadError]);

  return (
    <div className="space-y-4">
      <div
        ref={dropZoneRef}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        onKeyDown={handleKeyDown}
        tabIndex={isUploading ? -1 : 0}
        role="button"
        aria-label="Upload PDF file by clicking or dragging and dropping"
        aria-describedby="upload-instructions upload-constraints"
        className={`
          border-2 border-dashed rounded-lg p-12 text-center transition-all duration-200
          ${isDragging
            ? 'border-blue-500 bg-blue-50 scale-105'
            : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
          }
          ${isUploading 
            ? 'opacity-50 cursor-not-allowed' 
            : 'cursor-pointer focus:border-blue-500 focus:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleFileSelect}
          disabled={isUploading}
          className="sr-only"
          aria-describedby="upload-instructions upload-constraints"
        />

        {isUploading ? (
          <div className="space-y-4" role="status" aria-live="polite">
            <div className="flex items-center justify-center">
              <svg 
                className="animate-spin h-8 w-8 text-blue-600 mr-3" 
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
              <span className="text-gray-700 font-medium">
                Uploading {selectedFile?.name}...
              </span>
            </div>
            
            <div className="w-full bg-gray-200 rounded-full h-3" role="progressbar" aria-valuenow={uploadProgress} aria-valuemin={0} aria-valuemax={100}>
              <div
                className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            
            <p className="text-sm text-gray-600" aria-live="polite">
              {uploadProgress}% complete
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            <svg
              className="mx-auto h-16 w-16 text-gray-400"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
              aria-hidden="true"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v24a4 4 0 004 4h24a4 4 0 004-4V20m-14-8v16m-4-4l4 4 4-4"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            
            <div className="space-y-2">
              <p id="upload-instructions" className="text-lg text-gray-700 font-medium">
                Drag and drop your PDF here, or click to select
              </p>
              <p id="upload-constraints" className="text-sm text-gray-500">
                Maximum file size: {MAX_FILE_SIZE / 1024 / 1024}MB • PDF files only
              </p>
            </div>
            
            <div className="text-xs text-gray-400">
              <p>Supported formats: PDF (.pdf)</p>
              <p>Your file will be processed to generate an accessible audio narrative</p>
            </div>
          </div>
        )}
      </div>

      {uploadError && (
        <div 
          className="bg-red-50 border border-red-200 rounded-lg p-4"
          role="alert"
          aria-live="assertive"
        >
          <div className="flex items-start">
            <svg 
              className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
              />
            </svg>
            <div className="flex-1">
              <h3 className="text-sm font-medium text-red-800 mb-1">
                Upload Error
              </h3>
              <p className="text-sm text-red-700">{uploadError}</p>
            </div>
            <button
              onClick={clearError}
              className="ml-3 text-red-600 hover:text-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 rounded"
              aria-label="Dismiss error message"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
