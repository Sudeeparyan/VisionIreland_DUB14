"""Data models for Bedrock analysis module"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class VoiceProfile:
    """Voice profile for a character"""

    voice_id: str
    gender: str  # 'male', 'female', 'neutral'
    age: str  # 'child', 'young-adult', 'adult', 'senior'
    tone: str  # e.g., 'heroic', 'comedic', 'mysterious'


@dataclass
class Character:
    """Represents a character in the comic"""

    id: str
    name: str
    visual_description: str
    personality: str
    voice_profile: VoiceProfile
    first_introduced: int  # panel number
    last_seen: int
    visual_signatures: List[str] = field(default_factory=list)


@dataclass
class Scene:
    """Represents a scene/location in the comic"""

    id: str
    location: str
    visual_description: str
    first_introduced: int  # panel number
    last_seen: int
    time_of_day: Optional[str] = None
    atmosphere: Optional[str] = None
    color_palette: List[str] = field(default_factory=list)
    lighting: Optional[str] = None


@dataclass
class DialogueLine:
    """Represents a line of dialogue in a panel"""

    character_id: str
    text: str
    emotion: Optional[str] = None


@dataclass
class VisualAnalysis:
    """Visual analysis results from Bedrock"""

    characters: List[str]  # Character IDs visible in panel
    objects: List[str]  # Objects and elements
    spatial_layout: str  # Spatial relationships
    colors: List[str]  # Color palette
    mood: str  # Emotional tone


@dataclass
class PanelNarrative:
    """Generated narrative for a single panel"""

    panel_id: str
    visual_analysis: VisualAnalysis
    action_description: str
    dialogue: List[DialogueLine] = field(default_factory=list)
    scene_description: Optional[str] = None
    character_updates: List[Character] = field(default_factory=list)
    audio_description: str = ""


@dataclass
class BedrockAnalysisContext:
    """Context maintained throughout comic processing"""

    characters: Dict[str, Character] = field(default_factory=dict)
    scenes: Dict[str, Scene] = field(default_factory=dict)
    story_state: Dict[str, Any] = field(default_factory=dict)
