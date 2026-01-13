"""
PDF Extractor - Extracts pages, images, and text from PDF comic books
"""

import base64
import io
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import fitz  # PyMuPDF
from PIL import Image


class PDFExtractor:
    """
    Extracts content from PDF comic books including:
    - Full page images
    - Individual panel images (if detectable)
    - Text content
    - Metadata
    """

    def __init__(self, pdf_path: str):
        """
        Initialize the PDF extractor.

        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = Path(pdf_path)
        self.doc: Optional[fitz.Document] = None
        self.pages: List[Dict] = []
        self.metadata: Dict = {}

    def open(self) -> bool:
        """
        Open the PDF file.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.doc = fitz.open(self.pdf_path)
            self._extract_metadata()
            return True
        except Exception as e:
            print(f"Error opening PDF: {e}")
            return False

    def close(self):
        """Close the PDF document."""
        if self.doc:
            self.doc.close()
            self.doc = None

    def _extract_metadata(self):
        """Extract PDF metadata."""
        if not self.doc:
            return

        self.metadata = {
            "title": self.doc.metadata.get("title", "Unknown Comic"),
            "author": self.doc.metadata.get("author", "Unknown Author"),
            "page_count": len(self.doc),
            "file_name": self.pdf_path.name,
        }

    def get_page_count(self) -> int:
        """Get the total number of pages."""
        return len(self.doc) if self.doc else 0

    def extract_page_image(
        self, page_num: int, dpi: int = 150, as_base64: bool = False
    ) -> Optional[Image.Image | str]:
        """
        Extract a full page as an image.

        Args:
            page_num: Page number (0-indexed)
            dpi: Resolution for rendering
            as_base64: If True, return base64 encoded string

        Returns:
            PIL Image or base64 string, or None if failed
        """
        if not self.doc or page_num < 0 or page_num >= len(self.doc):
            return None

        try:
            page = self.doc[page_num]

            # Calculate zoom factor for desired DPI
            zoom = dpi / 72  # 72 is the default PDF DPI
            mat = fitz.Matrix(zoom, zoom)

            # Render page to pixmap
            pix = page.get_pixmap(matrix=mat, alpha=False)

            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            if as_base64:
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                return base64.b64encode(buffered.getvalue()).decode("utf-8")

            return img

        except Exception as e:
            print(f"Error extracting page {page_num}: {e}")
            return None

    def extract_page_text(self, page_num: int) -> str:
        """
        Extract text from a page.

        Args:
            page_num: Page number (0-indexed)

        Returns:
            Extracted text as string
        """
        if not self.doc or page_num < 0 or page_num >= len(self.doc):
            return ""

        try:
            page = self.doc[page_num]
            return page.get_text()
        except Exception as e:
            print(f"Error extracting text from page {page_num}: {e}")
            return ""

    def extract_all_pages(
        self, output_dir: Optional[Path] = None, dpi: int = 150
    ) -> List[Dict]:
        """
        Extract all pages from the PDF.

        Args:
            output_dir: Directory to save extracted images
            dpi: Resolution for rendering

        Returns:
            List of page data dictionaries
        """
        if not self.doc:
            return []

        self.pages = []

        for page_num in range(len(self.doc)):
            page_data = {
                "page_number": page_num + 1,  # 1-indexed for user display
                "text": self.extract_page_text(page_num),
                "image_base64": self.extract_page_image(page_num, dpi, as_base64=True),
            }

            # Save image to disk if output_dir provided
            if output_dir:
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)

                img = self.extract_page_image(page_num, dpi)
                if img:
                    img_path = output_dir / f"page_{page_num + 1:03d}.png"
                    img.save(img_path)
                    page_data["image_path"] = str(img_path)

            self.pages.append(page_data)

        return self.pages

    def get_page_data(self, page_num: int) -> Optional[Dict]:
        """
        Get extracted data for a specific page.

        Args:
            page_num: Page number (1-indexed for user convenience)

        Returns:
            Page data dictionary or None
        """
        idx = page_num - 1  # Convert to 0-indexed
        if 0 <= idx < len(self.pages):
            return self.pages[idx]
        return None

    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def process_pdf(pdf_path: str, output_dir: Optional[str] = None) -> Dict:
    """
    Convenience function to process a PDF file.

    Args:
        pdf_path: Path to the PDF file
        output_dir: Optional directory to save extracted content

    Returns:
        Dictionary containing metadata and pages
    """
    with PDFExtractor(pdf_path) as extractor:
        pages = extractor.extract_all_pages(
            output_dir=Path(output_dir) if output_dir else None
        )

        return {
            "metadata": extractor.metadata,
            "pages": pages,
            "page_count": extractor.get_page_count(),
        }
