"""
Configuration settings for Comic Voice Agent
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent.parent
UPLOAD_DIR = BASE_DIR / os.getenv("UPLOAD_DIR", "uploads")
PROCESSED_DIR = BASE_DIR / os.getenv("PROCESSED_DIR", "processed")

# Create directories if they don't exist
UPLOAD_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

# API Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Application Settings
APP_NAME = os.getenv("APP_NAME", "Comic Voice Agent")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Voice Configuration
VOICE_NAME = os.getenv("VOICE_NAME", "Puck")

# Available voice options
AVAILABLE_VOICES = [
    "Puck",
    "Charon",
    "Kore",
    "Fenrir",
    "Aoede",
    "Leda",
    "Orus",
    "Zephyr",
]

# File Upload Settings
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf"}

# Session Settings
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))

# Accessibility Settings
DEFAULT_SPEECH_RATE = float(os.getenv("DEFAULT_SPEECH_RATE", "1.0"))
HIGH_CONTRAST_MODE = os.getenv("HIGH_CONTRAST_MODE", "false").lower() == "true"
CHILD_MODE = os.getenv("CHILD_MODE", "false").lower() == "true"

# Model Configuration - Using models that support live audio (bidiGenerateContent)
# Native audio model explicitly supports streaming audio
GEMINI_MODEL = "gemini-2.5-flash-native-audio-latest"
VISION_MODEL = "gemini-2.5-flash"


# Validate configuration
def validate_config():
    """Validate required configuration settings"""
    errors = []

    if not GOOGLE_API_KEY:
        errors.append("GOOGLE_API_KEY is required. Please set it in .env file.")

    if VOICE_NAME not in AVAILABLE_VOICES:
        errors.append(f"VOICE_NAME must be one of: {', '.join(AVAILABLE_VOICES)}")

    return errors


# Export validation function
__all__ = [
    "GOOGLE_API_KEY",
    "APP_NAME",
    "DEBUG",
    "HOST",
    "PORT",
    "VOICE_NAME",
    "AVAILABLE_VOICES",
    "MAX_UPLOAD_SIZE_MB",
    "MAX_UPLOAD_SIZE_BYTES",
    "ALLOWED_EXTENSIONS",
    "UPLOAD_DIR",
    "PROCESSED_DIR",
    "SESSION_TIMEOUT_MINUTES",
    "DEFAULT_SPEECH_RATE",
    "HIGH_CONTRAST_MODE",
    "CHILD_MODE",
    "GEMINI_MODEL",
    "VISION_MODEL",
    "validate_config",
]
