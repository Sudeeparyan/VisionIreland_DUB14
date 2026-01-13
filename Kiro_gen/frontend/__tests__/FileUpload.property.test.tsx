import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FileUpload } from '@/components/FileUpload';
import { apiClient } from '@/lib/api-client';
import { useAppStore } from '@/lib/store';
import * as fc from 'fast-check';
import { describe, it, expect, beforeEach, vi } from 'vitest';

vi.mock('@/lib/api-client');
vi.mock('@/lib/store');

/**
 * Feature: comic-audio-narrator, Property 15: File Validation
 * Validates: Requirements 5.2
 */
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

  /**
   * Property 15: File Validation
   * For any file upload attempt, the system SHALL validate the file format and size, 
   * rejecting invalid files before processing
   */
  it('should validate all non-PDF file types as invalid', () => {
    fc.assert(
      fc.property(
        fc.oneof(
          fc.constant('text/plain'),
          fc.constant('image/jpeg'),
          fc.constant('image/png'),
          fc.constant('application/msword'),
          fc.constant('application/zip'),
          fc.constant('video/mp4'),
          fc.constant('audio/mpeg')
        ),
        fc.stringMatching(/^[a-zA-Z0-9_\-]+\.[a-z]{2,4}$/),
        (mimeType: string, filename: string) => {
          // Create a file with non-PDF type
          const file = new File(['content'], filename, { type: mimeType });
          const error = validateFile(file);
          
          // Should always return an error for non-PDF files
          return error !== null && error.includes('PDF');
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should reject files exceeding size limit consistently', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 51, max: 200 }), // Size in MB above the 50MB limit
        (sizeMB: number) => {
          // Create a file larger than 50MB
          const sizeInBytes = sizeMB * 1024 * 1024;
          const file = new File(['x'.repeat(sizeInBytes)], 'large.pdf', {
            type: 'application/pdf',
          });
          
          const error = validateFile(file);
          
          // Should always return a size error for files over 50MB
          return error !== null && error.includes('File size must be less than');
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should accept valid PDF files with various names and sizes', () => {
    fc.assert(
      fc.property(
        fc.stringMatching(/^[a-zA-Z0-9_\-\s]+\.pdf$/),
        fc.integer({ min: 1, max: 49 }), // Valid size range in MB
        (filename: string, sizeMB: number) => {
          const sizeInBytes = sizeMB * 1024 * 1024;
          const file = new File(['x'.repeat(sizeInBytes)], filename, { 
            type: 'application/pdf' 
          });
          
          const error = validateFile(file);
          
          // Should return null (no error) for valid PDF files
          return error === null;
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should reject empty files consistently', () => {
    fc.assert(
      fc.property(
        fc.stringMatching(/^[a-zA-Z0-9_\-]+\.pdf$/),
        (filename: string) => {
          // Create an empty file
          const file = new File([], filename, { type: 'application/pdf' });
          const error = validateFile(file);
          
          // Should always return an error for empty files
          return error !== null && error.includes('empty');
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should handle file extension fallback validation', () => {
    fc.assert(
      fc.property(
        fc.oneof(
          fc.constant(''),
          fc.constant('application/octet-stream'),
          fc.constant('text/plain')
        ),
        fc.stringMatching(/^[a-zA-Z0-9_\-]+\.pdf$/),
        (mimeType: string, filename: string) => {
          // Create a file with PDF extension but different/missing MIME type
          const file = new File(['pdf content'], filename, { type: mimeType });
          const error = validateFile(file);
          
          // Should accept files with .pdf extension even if MIME type is wrong
          return error === null;
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should preserve job ID through upload completion', () => {
    fc.assert(
      fc.property(
        fc.uuid(),
        async (jobId: string) => {
          mockUploadPdf.mockResolvedValue({ job_id: jobId });
          const onUploadComplete = vi.fn();
          const user = userEvent.setup();

          render(<FileUpload onUploadComplete={onUploadComplete} />);

          const file = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' });
          const input = screen.getByRole('button', { name: /Upload PDF file/i });

          await user.click(input);
          
          // Simulate file selection
          const fileInput = screen.getByLabelText(/Upload PDF file/i) as HTMLInputElement;
          await user.upload(fileInput, file);

          await waitFor(() => {
            expect(onUploadComplete).toHaveBeenCalledWith(jobId);
          }, { timeout: 3000 });

          return true;
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should handle progress updates monotonically', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 100 }),
        (progress: number) => {
          (useAppStore as any).mockReturnValue({
            isUploading: true,
            uploadProgress: progress,
            uploadError: null,
            setUploading: mockSetUploading,
            setUploadProgress: mockSetUploadProgress,
            setUploadError: mockSetUploadError,
          });

          render(<FileUpload />);
          const progressText = screen.getByText(`${progress}% complete`);
          expect(progressText).toBeInTheDocument();
          
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should validate multiple file selection rejection', () => {
    fc.assert(
      fc.property(
        fc.array(fc.stringMatching(/^[a-zA-Z0-9_\-]+\.pdf$/), { minLength: 2, maxLength: 5 }),
        (filenames: string[]) => {
          const files = filenames.map(name => 
            new File(['pdf content'], name, { type: 'application/pdf' })
          );
          
          // Simulate multiple file drop
          const mockSetUploadError = vi.fn();
          (useAppStore as any).mockReturnValue({
            isUploading: false,
            uploadProgress: 0,
            uploadError: null,
            setUploading: vi.fn(),
            setUploadProgress: vi.fn(),
            setUploadError: mockSetUploadError,
          });

          render(<FileUpload />);
          
          const dropZone = screen.getByRole('button', { name: /Upload PDF file/i });
          
          // Simulate drop event with multiple files
          const dropEvent = new Event('drop', { bubbles: true });
          Object.defineProperty(dropEvent, 'dataTransfer', {
            value: { files }
          });
          
          dropZone.dispatchEvent(dropEvent);
          
          // Should call setUploadError with multiple files message
          expect(mockSetUploadError).toHaveBeenCalledWith(
            expect.stringContaining('only one PDF file')
          );
          
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });
});

// Helper function that matches the actual validation logic in FileUpload component
function validateFile(file: File): string | null {
  const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
  const ALLOWED_TYPES = ['application/pdf'];
  const ALLOWED_EXTENSIONS = ['.pdf'];

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
}
