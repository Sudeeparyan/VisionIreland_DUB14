"""Polly text-to-speech audio generation module"""

from typing import Optional, List
from datetime import datetime
from .models import (
    AudioSegment,
    AudioMetadata,
    CompositeAudio,
    AudioGenerationRequest,
)
from ..aws_clients import aws_clients


class PollyAudioGenerator:
    """Generates audio from narrative text using AWS Polly"""

    # Supported output formats
    SUPPORTED_FORMATS = ["mp3", "ogg_vorbis"]

    # Polly voice IDs (neural voices for quality)
    NEURAL_VOICES = {
        "male_adult": "Matthew",
        "female_adult": "Joanna",
        "male_young": "Justin",
        "female_young": "Ivy",
        "male_senior": "Brian",
        "female_senior": "Kendra",
        "male_heroic": "Arthur",
        "female_heroic": "Aria",
    }

    # Standard voices (for cost optimization)
    STANDARD_VOICES = {
        "male_adult": "Joey",
        "female_adult": "Emma",
        "male_young": "Justin",
        "female_young": "Salli",
        "male_senior": "Brian",
        "female_senior": "Kendra",
    }

    def __init__(self, use_neural: bool = True):
        """
        Initialize the audio generator.

        Args:
            use_neural: Use neural voices for quality (True) or standard for cost (False)
        """
        self.polly_client = aws_clients.polly
        self.use_neural = use_neural
        self.voice_map = self.NEURAL_VOICES if use_neural else self.STANDARD_VOICES
        self.segments: List[AudioSegment] = []

    def generate_audio(self, request: AudioGenerationRequest) -> AudioSegment:
        """
        Generate audio from narrative text.

        Args:
            request: AudioGenerationRequest with text and voice settings

        Returns:
            AudioSegment with generated audio data
        """
        if not request.text or not request.text.strip():
            raise ValueError("Audio generation request text cannot be empty")

        if request.output_format not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported output format: {request.output_format}. "
                f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        try:
            # Call Polly to synthesize speech
            response = self.polly_client.synthesize_speech(
                Text=request.text,
                OutputFormat=request.output_format,
                VoiceId=request.voice_id,
                Engine=request.engine,
            )

            # Extract audio data from response
            audio_data = response["AudioStream"].read()

            # Create audio segment
            segment = AudioSegment(
                panel_id=request.panel_id or "unknown",
                audio_data=audio_data,
                duration=self._estimate_duration(request.text),
                voice_id=request.voice_id,
                engine=request.engine,
            )

            # Store segment for later composition
            self.segments.append(segment)

            return segment

        except Exception as e:
            raise RuntimeError(f"Polly audio generation failed: {str(e)}")

    def _estimate_duration(self, text: str) -> float:
        """
        Estimate audio duration from text length.

        Args:
            text: Text to estimate duration for

        Returns:
            Estimated duration in seconds
        """
        # Rough estimate: ~150 words per minute = 2.5 words per second
        # Average word length ~5 characters + 1 space = 6 chars per word
        word_count = len(text.split())
        duration_seconds = word_count / 2.5
        return max(0.5, duration_seconds)  # Minimum 0.5 seconds

    def get_voice_for_profile(
        self, gender: str, age: str, tone: Optional[str] = None
    ) -> str:
        """
        Get appropriate Polly voice ID for a character profile.

        Args:
            gender: 'male', 'female', or 'neutral'
            age: 'child', 'young-adult', 'adult', or 'senior'
            tone: Optional tone like 'heroic', 'comedic', 'mysterious'

        Returns:
            Polly voice ID
        """
        # Build voice key from profile
        if gender == "neutral":
            gender = "male"  # Default neutral to male

        age_map = {
            "child": "young",
            "young-adult": "young",
            "adult": "adult",
            "senior": "senior",
        }

        age_key = age_map.get(age, "adult")
        voice_key = f"{gender}_{age_key}"

        # Check for tone-specific voices
        if tone and tone.lower() == "heroic":
            heroic_key = f"{gender}_heroic"
            if heroic_key in self.voice_map:
                return self.voice_map[heroic_key]

        # Return standard voice for profile
        return self.voice_map.get(voice_key, self.voice_map["male_adult"])

    def compose_audio(
        self,
        segments: Optional[List[AudioSegment]] = None,
        metadata: Optional[AudioMetadata] = None,
        output_format: str = "mp3",
    ) -> CompositeAudio:
        """
        Compose multiple audio segments into a single audio file.

        Args:
            segments: List of AudioSegments to compose. If None, uses stored segments.
            metadata: AudioMetadata for the composite
            output_format: Output format for the composite

        Returns:
            CompositeAudio with all segments and metadata
        """
        segments_to_use = segments or self.segments

        if not segments_to_use:
            raise ValueError("No audio segments to compose")

        # Calculate total duration
        total_duration = sum(seg.duration for seg in segments_to_use)

        # Create composite audio
        composite = CompositeAudio(
            segments=segments_to_use,
            total_duration=total_duration,
            metadata=metadata,
            output_format=output_format,
        )

        return composite

    def reset_segments(self) -> None:
        """Clear stored segments for new comic"""
        self.segments = []

    def get_segments(self) -> List[AudioSegment]:
        """Get all stored audio segments"""
        return self.segments.copy()

    def set_engine(self, use_neural: bool) -> None:
        """
        Switch between neural and standard engines.

        Args:
            use_neural: True for neural (quality), False for standard (cost)
        """
        self.use_neural = use_neural
        self.voice_map = self.NEURAL_VOICES if use_neural else self.STANDARD_VOICES
