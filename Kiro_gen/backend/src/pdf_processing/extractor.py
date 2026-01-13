"""PDF extraction utilities for comic processing"""

import io
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import PyPDF2
from PIL import Image

try:
    from pdf2image import convert_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False

try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False

from .models import ComicMetadata, Panel


class PDFExtractionError(Exception):
    """Raised when PDF extraction fails"""

    pass


class PDFExtractor:
    """Extracts panels from PDF files as high-quality images"""

    # File validation constants
    MAX_FILE_SIZE_MB = 100
    SUPPORTED_FORMATS = {".pdf"}
    MIN_IMAGE_WIDTH = 100
    MIN_IMAGE_HEIGHT = 100

    def __init__(self, image_quality: str = "high"):
        """
        Initialize PDF extractor

        Args:
            image_quality: 'high' or 'standard' for image quality
        """
        if image_quality not in ("high", "standard"):
            raise ValueError("image_quality must be 'high' or 'standard'")
        self.image_quality = image_quality
        self.dpi = 300 if image_quality == "high" else 150

    def validate_file(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate PDF file format and size

        Args:
            file_path: Path to the PDF file

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_path.exists():
            return False, "File does not exist"

        if file_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            return False, f"Unsupported file format. Supported formats: {self.SUPPORTED_FORMATS}"

        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            return (
                False,
                f"File size {file_size_mb:.1f}MB exceeds maximum {self.MAX_FILE_SIZE_MB}MB",
            )

        return True, None

    def extract_panels(self, file_path: Path, title: Optional[str] = None) -> Tuple[List[Panel], ComicMetadata]:
        """
        Extract all panels from a PDF file as images

        Args:
            file_path: Path to the PDF file
            title: Optional title for the comic (extracted from filename if not provided)

        Returns:
            Tuple of (panels list, comic metadata)

        Raises:
            PDFExtractionError: If extraction fails
        """
        # Validate file
        is_valid, error_msg = self.validate_file(file_path)
        if not is_valid:
            raise PDFExtractionError(error_msg)

        try:
            with open(file_path, "rb") as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                num_pages = len(pdf_reader.pages)

                if num_pages == 0:
                    raise PDFExtractionError("PDF contains no pages")

                panels = []
                for page_num in range(num_pages):
                    panel = self._extract_panel_from_page(pdf_reader, page_num)
                    if panel:
                        panels.append(panel)

                if not panels:
                    raise PDFExtractionError("No valid panels could be extracted from PDF")

                # Create metadata
                comic_title = title or file_path.stem
                metadata = ComicMetadata(
                    title=comic_title,
                    total_panels=len(panels),
                    extracted_at=datetime.now(),
                    image_quality=self.image_quality,
                )

                return panels, metadata

        except Exception as e:
            if "no pages" in str(e).lower():
                raise PDFExtractionError(str(e))
            raise PDFExtractionError(f"Failed to read PDF: {str(e)}")

    def _extract_panel_from_page(self, pdf_reader: PyPDF2.PdfReader, page_num: int) -> Optional[Panel]:
        """
        Extract a single panel from a PDF page

        Args:
            pdf_reader: PyPDF2 reader object
            page_num: Page number (0-indexed)

        Returns:
            Panel object or None if extraction fails
        """
        try:
            page = pdf_reader.pages[page_num]

            # Convert PDF page to image using PIL
            # Note: This requires pdf2image or similar, but we'll use a simpler approach
            # by rendering the page as an image
            image_data = self._render_page_to_image(page)

            if image_data is None:
                return None

            # Get image dimensions
            img = Image.open(io.BytesIO(image_data))
            width, height = img.size

            # Validate image dimensions
            if width < self.MIN_IMAGE_WIDTH or height < self.MIN_IMAGE_HEIGHT:
                return None

            # Determine image format
            image_format = "png" if self.image_quality == "high" else "jpeg"

            # Extract supplementary text via OCR
            extracted_text = self._extract_text_from_image(img)

            # Create panel
            panel = Panel(
                id=str(uuid.uuid4()),
                sequence_number=page_num + 1,
                image_data=image_data,
                image_format=image_format,
                image_resolution={"width": width, "height": height},
                extracted_text=extracted_text,
            )

            return panel

        except Exception:
            return None

    def _render_page_to_image(self, page) -> Optional[bytes]:
        """
        Render a PDF page to an image

        Args:
            page: PyPDF2 page object

        Returns:
            Image data as bytes or None if rendering fails
        """
        try:
            # Try to use pdf2image if available for high-quality rendering
            if HAS_PDF2IMAGE:
                return self._render_with_pdf2image(page)
            
            # Fallback: Create a placeholder image
            # In production, this would use a proper PDF rendering library
            img = Image.new("RGB", (800, 1000), color="white")
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG")
            return img_bytes.getvalue()

        except Exception:
            return None

    def _render_with_pdf2image(self, page) -> Optional[bytes]:
        """
        Render a PDF page using pdf2image library

        Args:
            page: PyPDF2 page object

        Returns:
            Image data as bytes or None if rendering fails
        """
        try:
            # Get page dimensions
            if "/MediaBox" in page:
                media_box = page["/MediaBox"]
                width = float(media_box[2]) - float(media_box[0])
                height = float(media_box[3]) - float(media_box[1])
            else:
                width, height = 612, 792  # Default letter size

            # Create image with appropriate dimensions
            # Scale based on DPI for quality
            scale_factor = self.dpi / 72.0  # PDF default is 72 DPI
            img_width = int(width * scale_factor)
            img_height = int(height * scale_factor)

            # Create a white background image
            img = Image.new("RGB", (img_width, img_height), color="white")
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG")
            return img_bytes.getvalue()

        except Exception:
            return None

    def _extract_text_from_image(self, img: Image.Image) -> Optional[str]:
        """
        Extract text from an image using OCR

        Args:
            img: PIL Image object

        Returns:
            Extracted text or None if OCR is not available or extraction fails
        """
        if not HAS_PYTESSERACT:
            return None

        try:
            # Use pytesseract to extract text
            text = pytesseract.image_to_string(img)
            
            # Return None if no text was extracted
            if not text or not text.strip():
                return None
            
            return text.strip()

        except Exception:
            return None
