"""Data models for Polly audio generation module"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class AudioSegment:
    """Represents a single audio segment for a panel"""

    panel_id: str
    audio_data: bytes
    duration: float  # in seconds
    voice_id: str
    engine: str  # 'neural' or 'standard'


@dataclass
class AudioMetadata:
    """Metadata for generated audio"""

    title: str
    characters: List[str] = field(default_factory=list)
    scenes: List[str] = field(default_factory=list)
    generated_at: str = ""  # ISO format timestamp
    model_used: str = ""
    total_duration: float = 0.0
    voice_profiles: dict = field(default_factory=dict)


@dataclass
class CompositeAudio:
    """Complete audio file composed from segments"""

    segments: List[AudioSegment] = field(default_factory=list)
    total_duration: float = 0.0
    metadata: Optional[AudioMetadata] = None
    output_format: str = "mp3"  # 'mp3' or 'ogg_vorbis'


@dataclass
class AudioGenerationRequest:
    """Request for audio generation from narrative text"""

    text: str
    voice_id: str
    engine: str = "neural"  # 'neural' for quality, 'standard' for cost
    output_format: str = "mp3"  # 'mp3' or 'ogg_vorbis'
    panel_id: Optional[str] = None
