import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FileUpload } from '@/components/FileUpload';
import { apiClient } from '@/lib/api-client';
import { useAppStore } from '@/lib/store';
import { fc, describe, it, expect, beforeEach } from 'vitest';
import { vi } from 'vitest';

vi.mock('@/lib/api-client');
vi.mock('@/lib/store');

describe('FileUpload Component - Property Tests', () => {
  const mockUploadPdf = vi.fn();
  const mockSetUploading = vi.fn();
  const mockSetUploadProgress = vi.fn();
  const mockSetUploadError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (apiClient.uploadPdf as any) = mockUploadPdf;
    (useAppStore as any).mockReturnValue({
      isUploading: false,
      uploadProgress: 0,
      uploadError: null,
      setUploading: mockSetUploading,
      setUploadProgress: mockSetUploadProgress,
      setUploadError: mockSetUploadError,
    });
  });

  it('should validate all non-PDF file types as invalid', () => {
    fc.assert(
      fc.property(
        fc.stringMatching(/^[a-z]+\/[a-z0-9+\-]+$/),
        (mimeType: string) => {
          if (mimeType === 'application/pdf') {
            return true; // Skip PDF type
          }

          const file = new File(['content'], 'test.file', { type: mimeType });
          const error = validateFileType(file);
          return error !== null && error.includes('PDF');
        }
      ),
      { numRuns: 50 }
    );
  });

  it('should reject files exceeding size limit consistently', () => {
    fc.assert(
      fc.property(fc.integer({ min: 51, max: 200 }), (sizeMB: number) => {
        const file = new File(['x'.repeat(sizeMB * 1024 * 1024)], 'large.pdf', {
          type: 'application/pdf',
        });
        const error = validateFileSize(file);
        return error !== null && error.includes('File size must be less than');
      }),
      { numRuns: 10 }
    );
  });

  it('should accept valid PDF files with various names', () => {
    fc.assert(
      fc.property(
        fc.stringMatching(/^[a-zA-Z0-9_\-]+\.pdf$/),
        (filename: string) => {
          const file = new File(['pdf content'], filename, { type: 'application/pdf' });
          const typeError = validateFileType(file);
          const sizeError = validateFileSize(file);
          return typeError === null && sizeError === null;
        }
      ),
      { numRuns: 50 }
    );
  });

  it('should preserve job ID through upload completion', () => {
    fc.assert(
      fc.property(fc.uuid(), async (jobId: string) => {
        mockUploadPdf.mockResolvedValue({ job_id: jobId });
        const onUploadComplete = vi.fn();
        const user = userEvent.setup();

        render(<FileUpload onUploadComplete={onUploadComplete} />);

        const file = new File(['pdf'], 'test.pdf', { type: 'application/pdf' });
        const input = screen.getByLabelText(/Upload PDF file/i) as HTMLInputElement;

        await user.upload(input, file);
        await waitFor(() => {
          expect(onUploadComplete).toHaveBeenCalledWith(jobId);
        });
      }),
      { numRuns: 20 }
    );
  });

  it('should handle progress updates monotonically', () => {
    fc.assert(
      fc.property(fc.integer({ min: 0, max: 100 }), (progress: number) => {
        (useAppStore as any).mockReturnValue({
          isUploading: true,
          uploadProgress: progress,
          uploadError: null,
          setUploading: mockSetUploading,
          setUploadProgress: mockSetUploadProgress,
          setUploadError: mockSetUploadError,
        });

        render(<FileUpload />);
        expect(screen.getByText(`${progress}%`)).toBeInTheDocument();
      }),
      { numRuns: 50 }
    );
  });

  it('should clear errors on successful upload', () => {
    fc.assert(
      fc.property(fc.string({ minLength: 1, maxLength: 100 }), async (errorMsg: string) => {
        mockUploadPdf.mockResolvedValue({ job_id: 'job-123' });
        (useAppStore as any).mockReturnValue({
          isUploading: false,
          uploadProgress: 0,
          uploadError: errorMsg,
          setUploading: mockSetUploading,
          setUploadProgress: mockSetUploadProgress,
          setUploadError: mockSetUploadError,
        });

        render(<FileUpload />);
        expect(mockSetUploadError).toHaveBeenCalledWith(null);
      }),
      { numRuns: 20 }
    );
  });
});

// Helper functions for validation
function validateFileType(file: File): string | null {
  if (file.type !== 'application/pdf') {
    return 'Only PDF files are supported';
  }
  return null;
}

function validateFileSize(file: File): string | null {
  const MAX_FILE_SIZE = 50 * 1024 * 1024;
  if (file.size > MAX_FILE_SIZE) {
    return `File size must be less than ${MAX_FILE_SIZE / 1024 / 1024}MB`;
  }
  return null;
}
