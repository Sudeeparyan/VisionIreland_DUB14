"""Voice profile assignment for characters based on personality and demographics."""

import logging
from typing import Dict, Optional, List

from .models import VoiceProfile
from src.bedrock_analysis.models import Character

logger = logging.getLogger(__name__)


class VoiceAssignmentEngine:
    """Assigns voice profiles to characters based on personality and demographics."""

    # Voice mappings by gender, age, and tone
    VOICE_MAPPINGS = {
        ('male', 'child', 'heroic'): 'Justin',
        ('male', 'child', 'comedic'): 'Joey',
        ('male', 'child', 'mysterious'): 'Matthew',
        ('male', 'young-adult', 'heroic'): 'Liam',
        ('male', 'young-adult', 'comedic'): 'Joanna',
        ('male', 'young-adult', 'mysterious'): 'Kendra',
        ('male', 'adult', 'heroic'): 'Brian',
        ('male', 'adult', 'comedic'): 'Joey',
        ('male', 'adult', 'mysterious'): 'Matthew',
        ('male', 'senior', 'heroic'): 'Brian',
        ('male', 'senior', 'comedic'): 'Joey',
        ('male', 'senior', 'mysterious'): 'Matthew',
        ('female', 'child', 'heroic'): 'Ivy',
        ('female', 'child', 'comedic'): 'Joanna',
        ('female', 'child', 'mysterious'): 'Kendra',
        ('female', 'young-adult', 'heroic'): 'Joanna',
        ('female', 'young-adult', 'comedic'): 'Joanna',
        ('female', 'young-adult', 'mysterious'): 'Kendra',
        ('female', 'adult', 'heroic'): 'Joanna',
        ('female', 'adult', 'comedic'): 'Joanna',
        ('female', 'adult', 'mysterious'): 'Kendra',
        ('female', 'senior', 'heroic'): 'Joanna',
        ('female', 'senior', 'comedic'): 'Joanna',
        ('female', 'senior', 'mysterious'): 'Kendra',
        ('neutral', 'child', 'heroic'): 'Ivy',
        ('neutral', 'child', 'comedic'): 'Joey',
        ('neutral', 'young-adult', 'heroic'): 'Liam',
        ('neutral', 'young-adult', 'comedic'): 'Joanna',
        ('neutral', 'adult', 'heroic'): 'Brian',
        ('neutral', 'adult', 'comedic'): 'Joanna',
        ('neutral', 'senior', 'heroic'): 'Brian',
        ('neutral', 'senior', 'comedic'): 'Joanna',
    }

    # Polly voice IDs
    POLLY_VOICES = {
        'Brian': 'Brian',
        'Joanna': 'Joanna',
        'Kendra': 'Kendra',
        'Liam': 'Liam',
        'Matthew': 'Matthew',
        'Joey': 'Joey',
        'Justin': 'Justin',
        'Ivy': 'Ivy',
    }

    def __init__(self):
        """Initialize voice assignment engine."""
        self.character_voices: Dict[str, VoiceProfile] = {}
        self.voice_consistency: Dict[str, str] = {}  # character_id -> voice_id

    def assign_voice_profile(self, character: Character) -> VoiceProfile:
        """Assign voice profile to character.
        
        Args:
            character: Character object
            
        Returns:
            VoiceProfile object
        """
        # Check if character already has assigned voice
        if character.id in self.character_voices:
            return self.character_voices[character.id]
        
        # Extract demographics from character
        gender = self._infer_gender(character)
        age = self._infer_age(character)
        tone = self._infer_tone(character)
        
        # Get voice ID from mapping
        voice_key = (gender, age, tone)
        voice_name = self.VOICE_MAPPINGS.get(voice_key, 'Joanna')  # Default fallback
        voice_id = self.POLLY_VOICES.get(voice_name, 'Joanna')
        
        # Create voice profile
        voice_profile = VoiceProfile(
            voice_id=voice_id,
            gender=gender,
            age=age,
            tone=tone
        )
        
        # Store for consistency
        self.character_voices[character.id] = voice_profile
        self.voice_consistency[character.id] = voice_id
        
        logger.info(f"Assigned voice {voice_id} to character {character.name}")
        
        return voice_profile

    def _infer_gender(self, character: Character) -> str:
        """Infer character gender from description.
        
        Args:
            character: Character object
            
        Returns:
            Gender: 'male', 'female', or 'neutral'
        """
        description = (character.visual_description + ' ' + character.personality).lower()
        
        male_indicators = ['man', 'boy', 'male', 'he', 'his', 'him', 'father', 'son', 'brother']
        female_indicators = ['woman', 'girl', 'female', 'she', 'her', 'hers', 'mother', 'daughter', 'sister']
        
        male_count = sum(1 for indicator in male_indicators if indicator in description)
        female_count = sum(1 for indicator in female_indicators if indicator in description)
        
        if male_count > female_count:
            return 'male'
        elif female_count > male_count:
            return 'female'
        else:
            return 'neutral'

    def _infer_age(self, character: Character) -> str:
        """Infer character age from description.
        
        Args:
            character: Character object
            
        Returns:
            Age: 'child', 'young-adult', 'adult', or 'senior'
        """
        description = (character.visual_description + ' ' + character.personality).lower()
        
        child_indicators = ['child', 'kid', 'boy', 'girl', 'young', 'small', 'tiny']
        young_adult_indicators = ['teenager', 'teen', 'young', 'youth', 'student']
        senior_indicators = ['old', 'elderly', 'aged', 'senior', 'grandfather', 'grandmother', 'gray', 'grey']
        
        child_count = sum(1 for indicator in child_indicators if indicator in description)
        young_adult_count = sum(1 for indicator in young_adult_indicators if indicator in description)
        senior_count = sum(1 for indicator in senior_indicators if indicator in description)
        
        if child_count > 0:
            return 'child'
        elif senior_count > 0:
            return 'senior'
        elif young_adult_count > 0:
            return 'young-adult'
        else:
            return 'adult'

    def _infer_tone(self, character: Character) -> str:
        """Infer character tone from personality.
        
        Args:
            character: Character object
            
        Returns:
            Tone: 'heroic', 'comedic', 'mysterious', or default
        """
        personality = character.personality.lower()
        
        if any(word in personality for word in ['hero', 'brave', 'strong', 'courageous', 'noble']):
            return 'heroic'
        elif any(word in personality for word in ['funny', 'comic', 'humorous', 'witty', 'joker']):
            return 'comedic'
        elif any(word in personality for word in ['mysterious', 'secret', 'hidden', 'enigmatic', 'cryptic']):
            return 'mysterious'
        else:
            return 'heroic'  # Default tone

    def get_voice_profile(self, character_id: str) -> Optional[VoiceProfile]:
        """Get assigned voice profile for character.
        
        Args:
            character_id: Character ID
            
        Returns:
            VoiceProfile or None if not assigned
        """
        return self.character_voices.get(character_id)

    def ensure_voice_consistency(self, character_id: str) -> bool:
        """Verify voice consistency for character across appearances.
        
        Args:
            character_id: Character ID
            
        Returns:
            True if voice is consistent
        """
        if character_id not in self.voice_consistency:
            return False
        
        voice_profile = self.character_voices.get(character_id)
        if not voice_profile:
            return False
        
        return voice_profile.voice_id == self.voice_consistency[character_id]

    def get_all_character_voices(self) -> Dict[str, VoiceProfile]:
        """Get all assigned character voices.
        
        Returns:
            Dictionary of character_id to VoiceProfile
        """
        return self.character_voices.copy()

    def validate_voice_id(self, voice_id: str) -> bool:
        """Validate that voice ID is supported by Polly.
        
        Args:
            voice_id: Voice ID to validate
            
        Returns:
            True if voice ID is valid
        """
        return voice_id in self.POLLY_VOICES.values()

    def reset(self) -> None:
        """Reset engine for new comic."""
        self.character_voices.clear()
        self.voice_consistency.clear()
        logger.info("Voice assignment engine reset")
