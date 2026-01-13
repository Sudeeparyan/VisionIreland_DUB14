"""
Test script to upload a PDF file to the Comic Voice Agent
"""

import requests
import sys
from pathlib import Path


def test_upload(pdf_path: str):
    """Upload a PDF file and print the response."""
    url = "http://localhost:8000/api/upload"

    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"Error: File not found: {pdf_path}")
        return

    print(f"Uploading: {pdf_file.name}")
    print("-" * 50)

    with open(pdf_file, "rb") as f:
        files = {"file": (pdf_file.name, f, "application/pdf")}
        try:
            response = requests.post(url, files=files, timeout=120)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    # Default to test-1.pdf in uploads folder
    default_pdf = Path(__file__).parent / "uploads" / "test-1.pdf"
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else str(default_pdf)
    test_upload(pdf_path)
