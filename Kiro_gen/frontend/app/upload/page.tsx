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
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Upload Comic</h2>
        <p className="text-gray-600 mt-2">
          Upload a PDF comic to generate audio narratives
        </p>
      </div>

      <div className="bg-white rounded-lg shadow p-8">
        <FileUpload onUploadComplete={handleUploadComplete} />
      </div>

      {jobId && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-green-800 text-sm">
            Upload successful! Job ID: <span className="font-mono">{jobId}</span>
          </p>
          <p className="text-green-700 text-sm mt-2">
            Your comic is being processed. You can track progress in the library.
          </p>
        </div>
      )}
    </div>
  );
}
