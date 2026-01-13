'use client';

import { useState } from 'react';
import { FileUpload } from '@/components/FileUpload';

export default function UploadPage() {
  const [jobId, setJobId] = useState<string | null>(null);

  const handleUploadComplete = (id: string) => {
    setJobId(id);
  };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-gray-900">Upload Comic</h1>
        <p className="text-gray-600 mt-2">
          Upload a PDF comic to generate accessible audio narratives with AI-powered character voices and scene descriptions
        </p>
      </header>

      <div className="bg-white rounded-lg shadow-sm border p-8">
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            Select Your Comic
          </h2>
          <p className="text-sm text-gray-600 mb-4">
            Choose a PDF comic file to transform into an audio narrative. Our AI will analyze each panel, 
            identify characters and scenes, and generate professional audio descriptions.
          </p>
        </div>
        
        <FileUpload onUploadComplete={handleUploadComplete} />
        
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h3 className="text-sm font-semibold text-blue-900 mb-2">
            What happens next?
          </h3>
          <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
            <li>Your PDF will be analyzed panel by panel</li>
            <li>Characters and scenes will be identified</li>
            <li>Audio descriptions will be generated following professional standards</li>
            <li>Character-appropriate voices will be assigned</li>
            <li>The complete audio narrative will be available in your library</li>
          </ol>
        </div>
      </div>

      {jobId && (
        <div 
          className="bg-green-50 border border-green-200 rounded-lg p-6"
          role="status"
          aria-live="polite"
        >
          <div className="flex items-start">
            <svg 
              className="w-6 h-6 text-green-600 mt-0.5 mr-3 flex-shrink-0" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" 
              />
            </svg>
            <div>
              <h3 className="text-sm font-semibold text-green-800 mb-1">
                Upload Successful!
              </h3>
              <p className="text-sm text-green-700 mb-2">
                Your comic has been uploaded and is being processed.
              </p>
              <p className="text-xs text-green-600 font-mono bg-green-100 px-2 py-1 rounded">
                Job ID: {jobId}
              </p>
              <p className="text-sm text-green-700 mt-3">
                You can track the processing progress in your{' '}
                <a 
                  href="/library" 
                  className="font-medium underline hover:text-green-800 focus:text-green-800"
                >
                  library
                </a>
                . Processing typically takes 2-5 minutes depending on the comic length.
              </p>
            </div>
          </div>
        </div>
      )}

      <section className="bg-white rounded-lg shadow-sm border p-6" aria-labelledby="tips-heading">
        <h2 id="tips-heading" className="text-lg font-semibold text-gray-900 mb-4">
          Tips for Best Results
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-3">
            <div>
              <h3 className="text-sm font-medium text-gray-900">File Quality</h3>
              <p className="text-sm text-gray-600">
                Use high-resolution PDFs for better character and scene recognition
              </p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-900">File Size</h3>
              <p className="text-sm text-gray-600">
                Keep files under 50MB for optimal processing speed
              </p>
            </div>
          </div>
          <div className="space-y-3">
            <div>
              <h3 className="text-sm font-medium text-gray-900">Comic Format</h3>
              <p className="text-sm text-gray-600">
                Standard comic book layouts work best for panel detection
              </p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-900">Processing Time</h3>
              <p className="text-sm text-gray-600">
                Longer comics may take additional time for thorough analysis
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
