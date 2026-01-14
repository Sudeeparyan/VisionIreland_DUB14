"""PDF extraction utilities for comic processing using PyMuPDF"""

import io
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

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
    """Extracts panels from PDF files as high-quality images using PyMuPDF"""

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
        # DPI for rendering: 300 for high quality, 150 for standard
        self.dpi = 300 if image_quality == "high" else 150
        # Zoom factor for PyMuPDF (72 DPI is default)
        self.zoom = self.dpi / 72.0

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

    def extract_panels(self, file_path, title: Optional[str] = None) -> Tuple[List[Panel], ComicMetadata]:
        """
        Extract all panels from a PDF file as images using PyMuPDF

        Args:
            file_path: Path to the PDF file (string or Path object)
            title: Optional title for the comic (extracted from filename if not provided)

        Returns:
            Tuple of (panels list, comic metadata)

        Raises:
            PDFExtractionError: If extraction fails
        """
        # Convert string path to Path object if needed
        if isinstance(file_path, str):
            file_path = Path(file_path)
            
        # Validate file
        is_valid, error_msg = self.validate_file(file_path)
        if not is_valid:
            raise PDFExtractionError(error_msg)

        # Check if PyMuPDF is available
        if not HAS_PYMUPDF:
            raise PDFExtractionError(
                "PyMuPDF (fitz) is not installed. Install it with: pip install PyMuPDF"
            )

        try:
            panels = []
            
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(str(file_path))
            
            if pdf_document.page_count == 0:
                pdf_document.close()
                raise PDFExtractionError("PDF contains no pages")
            
            # Process each page
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                
                # Render page to image with specified zoom/DPI
                mat = fitz.Matrix(self.zoom, self.zoom)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # Convert to PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Validate image dimensions
                if img.width < self.MIN_IMAGE_WIDTH or img.height < self.MIN_IMAGE_HEIGHT:
                    continue
                
                # Convert to bytes
                img_bytes = io.BytesIO()
                img_format = "PNG" if self.image_quality == "high" else "JPEG"
                img.save(img_bytes, format=img_format, quality=95 if img_format == "JPEG" else None)
                image_data = img_bytes.getvalue()
                
                # Extract text via OCR if available
                extracted_text = self._extract_text_from_image(img)
                
                # Also try to get text directly from PDF
                pdf_text = page.get_text()
                if pdf_text and pdf_text.strip():
                    if extracted_text:
                        extracted_text = f"{pdf_text}\n{extracted_text}"
                    else:
                        extracted_text = pdf_text.strip()
                
                # Create panel
                panel = Panel(
                    id=str(uuid.uuid4()),
                    sequence_number=page_num + 1,
                    image_data=image_data,
                    image_format=img_format.lower(),
                    image_resolution={"width": img.width, "height": img.height},
                    extracted_text=extracted_text,
                )
                panels.append(panel)
            
            pdf_document.close()

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

        except PDFExtractionError:
            raise
        except Exception as e:
            raise PDFExtractionError(f"Failed to read PDF: {str(e)}")

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

    def extract_images_from_pdf(self, file_path) -> List[bytes]:
        """
        Extract embedded images from PDF (not page renders).
        
        This extracts actual image objects embedded in the PDF,
        which can be useful for comics that have separate image layers.

        Args:
            file_path: Path to the PDF file

        Returns:
            List of image data as bytes
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        if not HAS_PYMUPDF:
            return []
        
        images = []
        try:
            pdf_document = fitz.open(str(file_path))
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                image_list = page.get_images()
                
                for img_index, img_info in enumerate(image_list):
                    xref = img_info[0]
                    base_image = pdf_document.extract_image(xref)
                    
                    if base_image:
                        image_data = base_image["image"]
                        images.append(image_data)
            
            pdf_document.close()
            
        except Exception:
            pass
        
        return images

    def get_pdf_info(self, file_path) -> dict:
        """
        Get PDF metadata and information.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dictionary with PDF information
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        if not HAS_PYMUPDF:
            return {"error": "PyMuPDF not installed"}
        
        try:
            pdf_document = fitz.open(str(file_path))
            
            info = {
                "page_count": pdf_document.page_count,
                "metadata": pdf_document.metadata,
                "is_encrypted": pdf_document.is_encrypted,
                "is_pdf": pdf_document.is_pdf,
            }
            
            # Get page dimensions
            if pdf_document.page_count > 0:
                first_page = pdf_document[0]
                rect = first_page.rect
                info["page_width"] = rect.width
                info["page_height"] = rect.height
            
            pdf_document.close()
            return info
            
        except Exception as e:
            return {"error": str(e)}
