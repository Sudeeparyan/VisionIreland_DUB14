"""Unit tests for PDF extraction pipeline."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from src.pdf_processing.pipeline import PDFExtractionPipeline
from src.pdf_processing.models import Panel, ComicMetadata


@pytest.fixture
def pipeline():
    """Create extraction pipeline instance."""
    return PDFExtractionPipeline(max_file_size_mb=100)


@pytest.fixture
def sample_pdf_path():
    """Create a temporary PDF file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        # Create minimal valid PDF
        pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< >>
stream
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000214 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
262
%%EOF
"""
        f.write(pdf_content)
        f.flush()
        yield f.name
        Path(f.name).unlink()


def test_process_pdf_file_not_found(pipeline):
    """Test processing non-existent PDF file."""
    with pytest.raises(IOError, match="PDF file not found"):
        pipeline.process_pdf("/nonexistent/file.pdf")


def test_process_pdf_invalid_format(pipeline):
    """Test processing file with invalid format."""
    with tempfile.NamedTemporaryFile(suffix='.txt') as f:
        with pytest.raises(ValueError, match="Invalid file format"):
            pipeline.process_pdf(f.name)


def test_process_pdf_file_too_large(pipeline):
    """Test processing file exceeding size limit."""
    with tempfile.NamedTemporaryFile(suffix='.pdf') as f:
        # Write data exceeding max size
        f.write(b'x' * (101 * 1024 * 1024))
        f.flush()
        
        with pytest.raises(ValueError, match="PDF file too large"):
            pipeline.process_pdf(f.name)


def test_validate_panel_sequence_empty(pipeline):
    """Test validation with empty panel list."""
    assert pipeline.validate_panel_sequence([]) is False


def test_validate_panel_sequence_valid(pipeline):
    """Test validation with properly sequenced panels."""
    panels = [
        Panel(
            id="panel_0",
            sequence_number=0,
            image_data=b"test",
            image_format="png",
            image_resolution={"width": 100, "height": 100}
        ),
        Panel(
            id="panel_1",
            sequence_number=1,
            image_data=b"test",
            image_format="png",
            image_resolution={"width": 100, "height": 100}
        ),
    ]
    assert pipeline.validate_panel_sequence(panels) is True


def test_validate_panel_sequence_invalid(pipeline):
    """Test validation with out-of-order panels."""
    panels = [
        Panel(
            id="panel_0",
            sequence_number=0,
            image_data=b"test",
            image_format="png",
            image_resolution={"width": 100, "height": 100}
        ),
        Panel(
            id="panel_1",
            sequence_number=5,  # Wrong sequence number
            image_data=b"test",
            image_format="png",
            image_resolution={"width": 100, "height": 100}
        ),
    ]
    assert pipeline.validate_panel_sequence(panels) is False


def test_extract_supplementary_text(pipeline):
    """Test extraction of supplementary text from panels."""
    panels = [
        Panel(
            id="panel_0",
            sequence_number=0,
            image_data=b"test",
            image_format="png",
            image_resolution={"width": 100, "height": 100},
            extracted_text="Panel 0 text"
        ),
        Panel(
            id="panel_1",
            sequence_number=1,
            image_data=b"test",
            image_format="png",
            image_resolution={"width": 100, "height": 100},
            extracted_text="Panel 1 text"
        ),
    ]
    
    text_map = pipeline.extract_supplementary_text(panels)
    assert len(text_map) == 2
    assert text_map["panel_0"] == "Panel 0 text"
    assert text_map["panel_1"] == "Panel 1 text"


def test_extract_supplementary_text_no_text(pipeline):
    """Test extraction when panels have no text."""
    panels = [
        Panel(
            id="panel_0",
            sequence_number=0,
            image_data=b"test",
            image_format="png",
            image_resolution={"width": 100, "height": 100}
        ),
    ]
    
    text_map = pipeline.extract_supplementary_text(panels)
    assert len(text_map) == 0


def test_get_extraction_stats(pipeline):
    """Test extraction statistics calculation."""
    panels = [
        Panel(
            id="panel_0",
            sequence_number=0,
            image_data=b"test_data_1",
            image_format="png",
            image_resolution={"width": 100, "height": 100}
        ),
        Panel(
            id="panel_1",
            sequence_number=1,
            image_data=b"test_data_2",
            image_format="png",
            image_resolution={"width": 100, "height": 100}
        ),
    ]
    
    metadata = ComicMetadata(
        title="Test Comic",
        author="Test Author",
        total_panels=2,
        extracted_at=datetime.now(),
        image_quality="high"
    )
    
    stats = pipeline.get_extraction_stats(panels, metadata)
    
    assert stats['total_panels'] == 2
    assert stats['total_size_bytes'] == 22  # len(b"test_data_1") + len(b"test_data_2")
    assert stats['average_panel_size_bytes'] == 11
    assert stats['image_format'] == 'png'
    assert stats['title'] == 'Test Comic'
    assert stats['author'] == 'Test Author'


def test_get_extraction_stats_empty(pipeline):
    """Test extraction statistics with empty panels."""
    metadata = ComicMetadata(
        title="Empty Comic",
        total_panels=0,
        extracted_at=datetime.now(),
        image_quality="high"
    )
    
    stats = pipeline.get_extraction_stats([], metadata)
    
    assert stats['total_panels'] == 0
    assert stats['total_size_bytes'] == 0
    assert stats['average_panel_size_bytes'] == 0
    assert stats['image_format'] is None
