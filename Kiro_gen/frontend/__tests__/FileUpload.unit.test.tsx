import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FileUpload } from '@/components/FileUpload';
import { apiClient } from '@/lib/api-client';
import { useAppStore } from '@/lib/store';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

vi.mock('@/lib/api-client');
vi.mock('@/lib/store');

describe('FileUpload Component - Unit Tests', () => {
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

  it('renders upload area with drag-and-drop instructions', () => {
    render(<FileUpload />);
    expect(screen.getByText(/Drag and drop your PDF here/i)).toBeInTheDocument();
  });

  it('accepts PDF file selection via file input', async () => {
    mockUploadPdf.mockResolvedValue({ job_id: 'job-123' });
    const user = userEvent.setup();
    render(<FileUpload />);

    const file = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' });
    const input = screen.getByLabelText(/Upload PDF file/i) as HTMLInputElement;

    await user.upload(input, file);
    await waitFor(() => {
      expect(mockUploadPdf).toHaveBeenCalledWith(file);
    });
  });

  it('rejects non-PDF files with error message', async () => {
    const user = userEvent.setup();
    render(<FileUpload />);

    const file = new File(['content'], 'test.txt', { type: 'text/plain' });
    const input = screen.getByLabelText(/Upload PDF file/i) as HTMLInputElement;

    await user.upload(input, file);
    await waitFor(() => {
      expect(mockSetUploadError).toHaveBeenCalledWith('Only PDF files are supported');
    });
  });

  it('rejects files larger than 50MB', async () => {
    const user = userEvent.setup();
    render(<FileUpload />);

    const largeFile = new File(['x'.repeat(51 * 1024 * 1024)], 'large.pdf', {
      type: 'application/pdf',
    });
    const input = screen.getByLabelText(/Upload PDF file/i) as HTMLInputElement;

    await user.upload(input, largeFile);
    await waitFor(() => {
      expect(mockSetUploadError).toHaveBeenCalledWith(
        expect.stringContaining('File size must be less than')
      );
    });
  });

  it('shows progress bar during upload', async () => {
    mockUploadPdf.mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ job_id: 'job-123' }), 500))
    );
    (useAppStore as any).mockReturnValue({
      isUploading: true,
      uploadProgress: 50,
      uploadError: null,
      setUploading: mockSetUploading,
      setUploadProgress: mockSetUploadProgress,
      setUploadError: mockSetUploadError,
    });

    render(<FileUpload />);
    expect(screen.getByText('Uploading...')).toBeInTheDocument();
    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  it('displays error message on upload failure', async () => {
    mockUploadPdf.mockRejectedValue(new Error('Network error'));
    (useAppStore as any).mockReturnValue({
      isUploading: false,
      uploadProgress: 0,
      uploadError: 'Network error',
      setUploading: mockSetUploading,
      setUploadProgress: mockSetUploadProgress,
      setUploadError: mockSetUploadError,
    });

    render(<FileUpload />);
    expect(screen.getByText('Network error')).toBeInTheDocument();
  });

  it('calls onUploadComplete callback with job ID', async () => {
    mockUploadPdf.mockResolvedValue({ job_id: 'job-456' });
    const onUploadComplete = vi.fn();
    const user = userEvent.setup();

    render(<FileUpload onUploadComplete={onUploadComplete} />);

    const file = new File(['pdf'], 'test.pdf', { type: 'application/pdf' });
    const input = screen.getByLabelText(/Upload PDF file/i) as HTMLInputElement;

    await user.upload(input, file);
    await waitFor(() => {
      expect(onUploadComplete).toHaveBeenCalledWith('job-456');
    });
  });

  it('disables file input during upload', () => {
    (useAppStore as any).mockReturnValue({
      isUploading: true,
      uploadProgress: 30,
      uploadError: null,
      setUploading: mockSetUploading,
      setUploadProgress: mockSetUploadProgress,
      setUploadError: mockSetUploadError,
    });

    render(<FileUpload />);
    const input = screen.getByLabelText(/Upload PDF file/i) as HTMLInputElement;
    expect(input).toBeDisabled();
  });

  it('handles drag and drop file upload', async () => {
    mockUploadPdf.mockResolvedValue({ job_id: 'job-789' });
    render(<FileUpload />);

    const dropZone = screen.getByText(/Drag and drop your PDF here/i).closest('div');
    const file = new File(['pdf'], 'test.pdf', { type: 'application/pdf' });

    fireEvent.drop(dropZone!, {
      dataTransfer: { files: [file] },
    });

    await waitFor(() => {
      expect(mockUploadPdf).toHaveBeenCalledWith(file);
    });
  });

  it('shows visual feedback on drag over', () => {
    render(<FileUpload />);
    const dropZone = screen.getByText(/Drag and drop your PDF here/i).closest('div');

    fireEvent.dragOver(dropZone!);
    expect(dropZone).toHaveClass('border-blue-500', 'bg-blue-50');
  });
});
