"""Test PDF extraction with PyMuPDF"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pdf_processing import PDFExtractor

# Test with a PDF file
pdf_path = '../../pdf/test-1.pdf'
if os.path.exists(pdf_path):
    print(f"Testing PDF extraction with: {pdf_path}")
    extractor = PDFExtractor(image_quality='standard')
    
    # Get PDF info first
    info = extractor.get_pdf_info(pdf_path)
    print(f"PDF Info: {info}")
    
    # Extract panels
    panels, metadata = extractor.extract_panels(pdf_path)
    print(f"Extracted {len(panels)} panels")
    print(f"Metadata: title={metadata.title}, quality={metadata.image_quality}")
    
    # Show first panel info
    if panels:
        p = panels[0]
        print(f"First panel: id={p.id[:8]}..., size={len(p.image_data)} bytes, resolution={p.image_resolution}")
        print("SUCCESS: PDF extraction working!")
else:
    print(f"Test PDF not found at {pdf_path}")
    # Try another path
    alt_path = '../../test.pdf'
    if os.path.exists(alt_path):
        print(f"Found alternative PDF: {alt_path}")
        extractor = PDFExtractor(image_quality='standard')
        panels, metadata = extractor.extract_panels(alt_path)
        print(f"Extracted {len(panels)} panels from {alt_path}")
        print("SUCCESS: PDF extraction working!")
    else:
        print("No test PDF found")
