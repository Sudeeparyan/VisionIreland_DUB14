"""
Run the Comic Voice Agent application
"""

import uvicorn


def main():
    """Start the Comic Voice Agent server."""
    print("=" * 60)
    print(" Comic Voice Agent - Accessible Comic Book Experience")
    print(" For Blind People and Children")
    print("=" * 60)
    print()
    print("Starting server at http://localhost:8000")
    print("Press Ctrl+C to stop")
    print()

    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )


if __name__ == "__main__":
    main()
