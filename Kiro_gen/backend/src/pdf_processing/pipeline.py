"""PDF panel extraction pipeline for processing comic PDFs."""

import logging
from typing import List, Optional
from pathlib import Path

from .extractor import PDFExtractor
from .models import Panel, ComicMetadata

logger = logging.getLogger(__name__)


class PDFExtractionPipeline:
    """Orchestrates PDF panel extraction with error handling and edge case management."""

    def __init__(self, max_file_size_mb: int = 100):
        """Initialize extraction pipeline.
        
        Args:
            max_file_size_mb: Maximum PDF file size in megabytes
        """
        self.extractor = PDFExtractor()
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024

    def process_pdf(self, pdf_path: str) -> tuple[List[Panel], ComicMetadata]:
        """Process PDF file and extract panels.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (panels list, comic metadata)
            
        Raises:
            ValueError: If PDF is invalid or exceeds size limits
            IOError: If file cannot be read
        """
        pdf_file = Path(pdf_path)
        
        # Validate file exists
        if not pdf_file.exists():
            raise IOError(f"PDF file not found: {pdf_path}")
        
        # Validate file format
        if pdf_file.suffix.lower() != '.pdf':
            raise ValueError(f"Invalid file format. Expected .pdf, got {pdf_file.suffix}")
        
        # Validate file size
        file_size = pdf_file.stat().st_size
        if file_size > self.max_file_size_bytes:
            raise ValueError(
                f"PDF file too large: {file_size / 1024 / 1024:.1f}MB "
                f"(max: {self.max_file_size_bytes / 1024 / 1024:.1f}MB)"
            )
        
        try:
            # Extract panels
            panels = self.extractor.extract_panels(pdf_path)
            
            # Handle empty PDF
            if not panels:
                logger.warning(f"No panels extracted from {pdf_path}")
                raise ValueError("PDF contains no extractable panels")
            
            # Extract metadata
            metadata = self.extractor.extract_metadata(pdf_path)
            metadata.total_panels = len(panels)
            
            logger.info(f"Successfully extracted {len(panels)} panels from {pdf_path}")
            return panels, metadata
            
        except Exception as e:
            logger.error(f"Failed to process PDF {pdf_path}: {e}")
            raise

    def process_pdf_batch(self, pdf_paths: List[str]) -> List[tuple[List[Panel], ComicMetadata]]:
        """Process multiple PDF files.
        
        Args:
            pdf_paths: List of paths to PDF files
            
        Returns:
            List of (panels, metadata) tuples
        """
        results = []
        for pdf_path in pdf_paths:
            try:
                panels, metadata = self.process_pdf(pdf_path)
                results.append((panels, metadata))
            except Exception as e:
                logger.error(f"Skipping PDF {pdf_path}: {e}")
                continue
        
        return results

    def validate_panel_sequence(self, panels: List[Panel]) -> bool:
        """Validate that panels are in correct sequential order.
        
        Args:
            panels: List of extracted panels
            
        Returns:
            True if panels are properly sequenced
        """
        if not panels:
            return False
        
        for i, panel in enumerate(panels):
            if panel.sequence_number != i:
                logger.warning(
                    f"Panel sequence mismatch at index {i}: "
                    f"expected {i}, got {panel.sequence_number}"
                )
                return False
        
        return True

    def extract_supplementary_text(self, panels: List[Panel]) -> dict:
        """Extract OCR text from panels as supplementary content.
        
        Args:
            panels: List of extracted panels
            
        Returns:
            Dictionary mapping panel IDs to extracted text
        """
        text_map = {}
        for panel in panels:
            if panel.extracted_text:
                text_map[panel.id] = panel.extracted_text
        
        return text_map

    def handle_corrupted_pdf(self, pdf_path: str) -> Optional[tuple[List[Panel], ComicMetadata]]:
        """Attempt recovery from corrupted PDF.
        
        Args:
            pdf_path: Path to potentially corrupted PDF
            
        Returns:
            Tuple of (panels, metadata) if recovery successful, None otherwise
        """
        try:
            logger.warning(f"Attempting recovery from corrupted PDF: {pdf_path}")
            
            # Try extraction with error recovery
            panels = self.extractor.extract_panels(pdf_path)
            
            if panels:
                metadata = self.extractor.extract_metadata(pdf_path)
                metadata.total_panels = len(panels)
                logger.info(f"Successfully recovered {len(panels)} panels from corrupted PDF")
                return panels, metadata
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to recover from corrupted PDF: {e}")
            return None

    def get_extraction_stats(self, panels: List[Panel], metadata: ComicMetadata) -> dict:
        """Get statistics about extracted panels.
        
        Args:
            panels: List of extracted panels
            metadata: Comic metadata
            
        Returns:
            Dictionary with extraction statistics
        """
        total_size = sum(len(panel.image_data) for panel in panels)
        
        return {
            'total_panels': len(panels),
            'total_size_bytes': total_size,
            'average_panel_size_bytes': total_size // len(panels) if panels else 0,
            'image_format': panels[0].image_format if panels else None,
            'title': metadata.title,
            'author': metadata.author,
            'extraction_time': metadata.extracted_at.isoformat() if metadata.extracted_at else None,
        }
