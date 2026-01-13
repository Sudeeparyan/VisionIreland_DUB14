"""File validation utilities for PDF uploads"""

from pathlib import Path
from typing import Optional, Tuple


class FileValidator:
    """Validates uploaded files for PDF processing"""

    # Configuration constants
    MAX_FILE_SIZE_MB = 100
    SUPPORTED_FORMATS = {".pdf", ".epub"}
    SUPPORTED_MIME_TYPES = {"application/pdf", "application/epub+zip"}

    @classmethod
    def validate_file(
        cls, file_path: Path, mime_type: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a file for PDF processing

        Args:
            file_path: Path to the file
            mime_type: Optional MIME type of the file

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file exists
        if not file_path.exists():
            return False, "File does not exist"

        # Check file extension
        file_ext = file_path.suffix.lower()
        if file_ext not in cls.SUPPORTED_FORMATS:
            supported = ", ".join(cls.SUPPORTED_FORMATS)
            return False, f"Unsupported file format. Supported formats: {supported}"

        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > cls.MAX_FILE_SIZE_MB:
            return (
                False,
                f"File size {file_size_mb:.1f}MB exceeds maximum {cls.MAX_FILE_SIZE_MB}MB",
            )

        # Check MIME type if provided
        if mime_type and mime_type not in cls.SUPPORTED_MIME_TYPES:
            return False, f"Unsupported MIME type: {mime_type}"

        return True, None

    @classmethod
    def validate_filename(cls, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a filename

        Args:
            filename: The filename to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not filename:
            return False, "Filename cannot be empty"

        if len(filename) > 255:
            return False, "Filename exceeds maximum length of 255 characters"

        # Check for invalid characters
        invalid_chars = {"<", ">", ":", '"', "|", "?", "*", "\0"}
        if any(char in filename for char in invalid_chars):
            return False, "Filename contains invalid characters"

        return True, None
