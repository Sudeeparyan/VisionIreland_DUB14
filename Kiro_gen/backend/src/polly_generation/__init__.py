"""Polly audio generation module for text-to-speech synthesis"""

from .models import (
    AudioSegment,
    AudioMetadata,
    CompositeAudio,
    AudioGenerationRequest,
)
from .generator import PollyAudioGenerator
from .voice_manager import VoiceProfileManager

__all__ = [
    "AudioSegment",
    "AudioMetadata",
    "CompositeAudio",
    "AudioGenerationRequest",
    "PollyAudioGenerator",
    "VoiceProfileManager",
]
