import {
  render,
  screen,
  fireEvent,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { FileUpload } from "@/components/FileUpload";
import { apiClient } from "@/lib/api-client";
import { useAppStore } from "@/lib/store";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";

vi.mock("@/lib/api-client");
vi.mock("@/lib/store");

describe("FileUpload Component - Unit Tests", () => {
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

  it("renders upload area with drag-and-drop instructions", () => {
    render(<FileUpload />);
    expect(
      screen.getByText(/Drag and drop your PDF here/i)
    ).toBeInTheDocument();
  });

  it("accepts PDF file selection via file input", async () => {
    mockUploadPdf.mockResolvedValue({ job_id: "job-123" });
    const user = userEvent.setup();
    render(<FileUpload />);

    const file = new File(["pdf content"], "test.pdf", {
      type: "application/pdf",
    });
    // Get the actual file input element (which is hidden with sr-only class)
    const input = document.querySelector(
      'input[type="file"]'
    ) as HTMLInputElement;

    await user.upload(input, file);
    await waitFor(() => {
      expect(mockUploadPdf).toHaveBeenCalledWith(file);
    });
  });

  it("rejects non-PDF files with error message", async () => {
    render(<FileUpload />);

    const file = new File(["content"], "test.txt", { type: "text/plain" });
    // Use drag-and-drop to bypass the accept attribute
    const dropZone = screen.getByRole("button", { name: /Upload PDF file/i });

    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] },
    });

    await waitFor(() => {
      expect(mockSetUploadError).toHaveBeenCalledWith(
        expect.stringContaining("PDF")
      );
    });
  });

  it("rejects files larger than 50MB", async () => {
    const user = userEvent.setup();
    render(<FileUpload />);

    const largeFile = new File(["x".repeat(51 * 1024 * 1024)], "large.pdf", {
      type: "application/pdf",
    });
    // Get the actual file input element
    const input = document.querySelector(
      'input[type="file"]'
    ) as HTMLInputElement;

    await user.upload(input, largeFile);
    await waitFor(() => {
      expect(mockSetUploadError).toHaveBeenCalledWith(
        expect.stringContaining("File size must be less than")
      );
    });
  });

  it("shows progress bar during upload", async () => {
    (useAppStore as any).mockReturnValue({
      isUploading: true,
      uploadProgress: 50,
      uploadError: null,
      setUploading: mockSetUploading,
      setUploadProgress: mockSetUploadProgress,
      setUploadError: mockSetUploadError,
    });

    render(<FileUpload />);
    // The component shows "Uploading {filename}..." with whitespace variations
    expect(screen.getByText(/Uploading/i)).toBeInTheDocument();
    expect(screen.getByText(/50.*%.*complete/i)).toBeInTheDocument();
  });

  it("displays error message on upload failure", async () => {
    (useAppStore as any).mockReturnValue({
      isUploading: false,
      uploadProgress: 0,
      uploadError: "Network error",
      setUploading: mockSetUploading,
      setUploadProgress: mockSetUploadProgress,
      setUploadError: mockSetUploadError,
    });

    render(<FileUpload />);
    expect(screen.getByText("Network error")).toBeInTheDocument();
  });

  it("calls onUploadComplete callback with job ID", async () => {
    mockUploadPdf.mockResolvedValue({ job_id: "job-456" });
    const onUploadComplete = vi.fn();
    const user = userEvent.setup();

    render(<FileUpload onUploadComplete={onUploadComplete} />);

    const file = new File(["pdf"], "test.pdf", { type: "application/pdf" });
    // Get the actual file input element
    const input = document.querySelector(
      'input[type="file"]'
    ) as HTMLInputElement;

    await user.upload(input, file);
    await waitFor(() => {
      expect(onUploadComplete).toHaveBeenCalledWith("job-456");
    });
  });

  it("disables file input during upload", () => {
    (useAppStore as any).mockReturnValue({
      isUploading: true,
      uploadProgress: 30,
      uploadError: null,
      setUploading: mockSetUploading,
      setUploadProgress: mockSetUploadProgress,
      setUploadError: mockSetUploadError,
    });

    render(<FileUpload />);
    // Get the actual file input element
    const input = document.querySelector(
      'input[type="file"]'
    ) as HTMLInputElement;
    expect(input).toBeDisabled();
  });

  it("handles drag and drop file upload", async () => {
    mockUploadPdf.mockResolvedValue({ job_id: "job-789" });
    render(<FileUpload />);

    // Get the drop zone by role
    const dropZone = screen.getByRole("button", { name: /Upload PDF file/i });
    const file = new File(["pdf"], "test.pdf", { type: "application/pdf" });

    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] },
    });

    await waitFor(() => {
      expect(mockUploadPdf).toHaveBeenCalledWith(file);
    });
  });

  it("shows visual feedback on drag over", () => {
    render(<FileUpload />);
    // Get the drop zone by role
    const dropZone = screen.getByRole("button", { name: /Upload PDF file/i });

    // Create proper drag events with dataTransfer
    const dataTransfer = {
      files: [],
      items: [],
      types: ["Files"],
    };

    fireEvent.dragEnter(dropZone, { dataTransfer });
    fireEvent.dragOver(dropZone, { dataTransfer });

    // The component adds these classes when isDragging is true
    expect(dropZone).toHaveClass("border-blue-500", "bg-blue-50");
  });
});
