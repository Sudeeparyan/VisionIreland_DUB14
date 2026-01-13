"""
Test script to verify Comic Voice Agent installation
"""

import sys
from pathlib import Path


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    errors = []

    # Test config
    try:
        from app.config import GOOGLE_API_KEY, VOICE_NAME, GEMINI_MODEL

        print("  ✓ app.config")
    except ImportError as e:
        errors.append(f"  ✗ app.config: {e}")

    # Test PDF processor
    try:
        from app.pdf_processor import PDFExtractor, ComicAnalyzer, ComicParser

        print("  ✓ app.pdf_processor")
    except ImportError as e:
        errors.append(f"  ✗ app.pdf_processor: {e}")

    # Test agents
    try:
        from app.agents import create_storyteller_agent, STORYTELLER_PROMPT

        print("  ✓ app.agents")
    except ImportError as e:
        errors.append(f"  ✗ app.agents: {e}")

    # Test tools
    try:
        from app.tools import (
            navigate_to_page,
            describe_current_scene,
            get_page_narration,
        )

        print("  ✓ app.tools")
    except ImportError as e:
        errors.append(f"  ✗ app.tools: {e}")

    # Test main
    try:
        from app.main import app

        print("  ✓ app.main (FastAPI)")
    except ImportError as e:
        errors.append(f"  ✗ app.main: {e}")

    return errors


def test_static_files():
    """Test that static files exist."""
    print("\nTesting static files...")
    static_dir = Path(__file__).parent / "app" / "static"

    required_files = [
        "index.html",
        "css/styles.css",
        "js/app.js",
        "js/pcm-player-processor.js",
        "js/pcm-recorder-processor.js",
    ]

    errors = []
    for file in required_files:
        file_path = static_dir / file
        if file_path.exists():
            print(f"  ✓ {file}")
        else:
            errors.append(f"  ✗ {file} (missing)")

    return errors


def test_directories():
    """Test that required directories exist or can be created."""
    print("\nTesting directories...")
    from app.config import UPLOAD_DIR, PROCESSED_DIR

    errors = []
    for dir_path in [UPLOAD_DIR, PROCESSED_DIR]:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ {dir_path}")
        except Exception as e:
            errors.append(f"  ✗ {dir_path}: {e}")

    return errors


def test_dependencies():
    """Test that required dependencies are installed."""
    print("\nTesting dependencies...")

    packages = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("google.genai", "Google GenAI"),
        ("fitz", "PyMuPDF"),
        ("PIL", "Pillow"),
        ("dotenv", "python-dotenv"),
    ]

    errors = []
    for module, name in packages:
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            errors.append(f"  ✗ {name} (not installed)")

    return errors


def main():
    """Run all tests."""
    print("=" * 60)
    print("Comic Voice Agent - Setup Verification")
    print("=" * 60)

    all_errors = []

    # Run dependency test first
    all_errors.extend(test_dependencies())

    # Only run import tests if dependencies are OK
    if not all_errors:
        all_errors.extend(test_imports())
        all_errors.extend(test_static_files())
        all_errors.extend(test_directories())

    print("\n" + "=" * 60)
    if all_errors:
        print("SETUP INCOMPLETE - Issues found:")
        for error in all_errors:
            print(error)
        print("\nPlease install missing dependencies:")
        print("  pip install -r requirements.txt")
        return 1
    else:
        print("ALL TESTS PASSED ✓")
        print("\nTo start the application:")
        print("  1. Copy .env.example to .env")
        print("  2. Add your GOOGLE_API_KEY to .env")
        print("  3. Run: python run.py")
        return 0


if __name__ == "__main__":
    sys.exit(main())
