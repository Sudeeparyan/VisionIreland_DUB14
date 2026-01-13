"""Property-based tests for PDF extraction module

**Feature: comic-audio-narrator, Property 1: Panel Extraction Completeness**
**Validates: Requirements 1.2**
"""

import io
import tempfile
from pathlib import Path

import PyPDF2
from hypothesis import given, settings
from hypothesis import strategies as st
from PIL import Image

from src.pdf_processing import PDFExtractor, PDFExtractionError


def create_test_pdf(num_pages: int) -> bytes:
    """
    Create a test PDF with specified number of pages

    Args:
        num_pages: Number of pages to create

    Returns:
        PDF file as bytes
    """
    pdf_writer = PyPDF2.PdfWriter()

    for i in range(num_pages):
        # Create a simple image for each page
        img = Image.new("RGB", (800, 1000), color=(255, 255, 255))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        # Add image to PDF (simplified - just add blank pages)
        page = PyPDF2.PageObject.create_blank_page(None, 800, 1000)
        pdf_writer.add_page(page)

    pdf_bytes = io.BytesIO()
    pdf_writer.write(pdf_bytes)
    pdf_bytes.seek(0)
    return pdf_bytes.getvalue()


@given(num_pages=st.integers(min_value=1, max_value=50))
@settings(max_examples=100, deadline=None)
def test_panel_extraction_completeness(num_pages: int):
    """
    Property: For any valid PDF comic, extracting panels SHALL result in all
    panels being present and in sequential order matching the original PDF

    This property tests that:
    1. All pages in the PDF are extracted as panels
    2. Panels maintain sequential ordering (sequence_number matches page order)
    3. No panels are skipped or duplicated
    """
    # Create a test PDF with the specified number of pages
    pdf_data = create_test_pdf(num_pages)

    # Write to temporary file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_file.write(pdf_data)
        tmp_path = Path(tmp_file.name)

    try:
        # Extract panels
        extractor = PDFExtractor(image_quality="standard")
        panels, metadata = extractor.extract_panels(tmp_path)

        # Property 1: All panels are present
        assert len(panels) == num_pages, (
            f"Expected {num_pages} panels but got {len(panels)}"
        )

        # Property 2: Panels are in sequential order
        for i, panel in enumerate(panels):
            expected_sequence = i + 1
            assert panel.sequence_number == expected_sequence, (
                f"Panel {i} has sequence_number {panel.sequence_number}, "
                f"expected {expected_sequence}"
            )

        # Property 3: No duplicate sequence numbers
        sequence_numbers = [p.sequence_number for p in panels]
        assert len(sequence_numbers) == len(set(sequence_numbers)), (
            "Duplicate sequence numbers found in extracted panels"
        )

        # Property 4: Sequence numbers are contiguous
        expected_sequences = list(range(1, num_pages + 1))
        assert sequence_numbers == expected_sequences, (
            f"Sequence numbers {sequence_numbers} do not match expected {expected_sequences}"
        )

        # Property 5: Metadata reflects correct panel count
        assert metadata.total_panels == num_pages, (
            f"Metadata total_panels {metadata.total_panels} does not match "
            f"extracted panels count {num_pages}"
        )

    finally:
        # Clean up
        tmp_path.unlink()


@given(num_pages=st.integers(min_value=1, max_value=50))
@settings(max_examples=100, deadline=None)
def test_panel_extraction_order_preservation(num_pages: int):
    """
    Property: Panel extraction SHALL preserve the order of pages from the PDF

    This property verifies that the sequence_number of each panel corresponds
    to its position in the original PDF.
    """
    pdf_data = create_test_pdf(num_pages)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_file.write(pdf_data)
        tmp_path = Path(tmp_file.name)

    try:
        extractor = PDFExtractor(image_quality="standard")
        panels, _ = extractor.extract_panels(tmp_path)

        # Verify order preservation
        for idx, panel in enumerate(panels):
            assert panel.sequence_number == idx + 1, (
                f"Panel at index {idx} has sequence_number {panel.sequence_number}, "
                f"expected {idx + 1}"
            )

    finally:
        tmp_path.unlink()


def test_panel_extraction_empty_pdf_fails():
    """
    Edge case: Extracting from an empty PDF should raise an error
    """
    # Create an empty PDF
    pdf_writer = PyPDF2.PdfWriter()
    pdf_bytes = io.BytesIO()
    pdf_writer.write(pdf_bytes)
    pdf_bytes.seek(0)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_file.write(pdf_bytes.getvalue())
        tmp_path = Path(tmp_file.name)

    try:
        extractor = PDFExtractor()
        try:
            extractor.extract_panels(tmp_path)
            assert False, "Expected PDFExtractionError for empty PDF"
        except PDFExtractionError as e:
            assert "no pages" in str(e).lower()

    finally:
        tmp_path.unlink()


def test_panel_extraction_single_page():
    """
    Edge case: Single page PDF should extract exactly one panel
    """
    pdf_data = create_test_pdf(1)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_file.write(pdf_data)
        tmp_path = Path(tmp_file.name)

    try:
        extractor = PDFExtractor()
        panels, metadata = extractor.extract_panels(tmp_path)

        assert len(panels) == 1
        assert panels[0].sequence_number == 1
        assert metadata.total_panels == 1

    finally:
        tmp_path.unlink()
