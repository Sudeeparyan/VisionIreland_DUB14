"""Voice profile management for character-specific audio generation"""

from typing import Optional, Dict
from ..bedrock_analysis.models import VoiceProfile, Character


class VoiceProfileManager:
    """Manages voice profile assignment and consistency"""

    def __init__(self):
        """Initialize voice profile manager"""
        self.character_voices: Dict[str, str] = {}  # character_id -> voice_id
        self.voice_profiles: Dict[str, VoiceProfile] = {}  # character_id -> VoiceProfile

    def assign_voice_profile(
        self, character: Character, voice_id: Optional[str] = None
    ) -> VoiceProfile:
        """
        Assign a voice profile to a character.

        Args:
            character: Character to assign voice to
            voice_id: Polly voice ID to use (optional, uses character's voice profile if not provided)

        Returns:
            VoiceProfile for the character
        """
        # Use provided voice_id or get from character's voice profile
        if voice_id is None:
            voice_id = character.voice_profile.voice_id if character.voice_profile else 'Joanna'
        
        # Store voice assignment
        self.character_voices[character.id] = voice_id

        # Store voice profile
        self.voice_profiles[character.id] = character.voice_profile

        return character.voice_profile

    def get_voice_for_character(self, character_id: str) -> Optional[str]:
        """
        Get the assigned voice ID for a character.

        Args:
            character_id: Character identifier

        Returns:
            Polly voice ID or None if not assigned
        """
        return self.character_voices.get(character_id)

    def get_voice_profile(self, character_id: str) -> Optional[VoiceProfile]:
        """
        Get the voice profile for a character.

        Args:
            character_id: Character identifier

        Returns:
            VoiceProfile or None if not assigned
        """
        return self.voice_profiles.get(character_id)

    def ensure_voice_consistency(
        self, character: Character, voice_id: str
    ) -> bool:
        """
        Ensure voice consistency for a character across panels.

        Args:
            character: Character to check
            voice_id: Voice ID to verify

        Returns:
            True if voice is consistent, False if mismatch
        """
        existing_voice = self.character_voices.get(character.id)

        if existing_voice is None:
            # First appearance, assign voice
            self.assign_voice_profile(character, voice_id)
            return True

        # Check consistency
        return existing_voice == voice_id

    def get_all_character_voices(self) -> Dict[str, str]:
        """Get all character-to-voice assignments"""
        return self.character_voices.copy()

    def reset(self) -> None:
        """Reset voice assignments for new comic"""
        self.character_voices.clear()
        self.voice_profiles.clear()

    def validate_voice_id(self, voice_id: str) -> bool:
        """
        Validate that a voice ID is a valid Polly voice.

        Args:
            voice_id: Voice ID to validate

        Returns:
            True if valid, False otherwise
        """
        # List of valid Polly voice IDs
        valid_voices = {
            # Neural voices
            "Matthew",
            "Joanna",
            "Justin",
            "Ivy",
            "Brian",
            "Kendra",
            "Arthur",
            "Aria",
            # Standard voices
            "Joey",
            "Emma",
            "Salli",
            # Additional voices
            "Geraint",
            "Celine",
            "Mathieu",
            "Lucia",
            "Lupe",
            "Conchita",
            "Enrique",
            "Vitoria",
            "Ricardo",
            "Maxim",
            "Tatyana",
            "Astrid",
            "Filiz",
            "Mizuki",
            "Zhiyu",
            "Naja",
            "Mads",
            "Ruben",
            "Ewa",
            "Jan",
            "Jacek",
            "Ines",
            "Cristiano",
            "Bianca",
            "Karl",
            "Dora",
            "Aditi",
            "Raveesh",
            "Sunil",
            "Chantal",
            "Celine",
            "Gwyneth",
            "Gérard",
            "Carla",
            "Liam",
            "Rory",
            "Siobhan",
            "Seoyeon",
            "Takumi",
            "Olivia",
            "Russell",
            "Ava",
            "Amy",
            "Vicki",
            "Ivy",
            "Kimberly",
            "Kendra",
            "Justin",
            "Joey",
            "Kevin",
            "Salli",
            "Raveesh",
            "Aditi",
            "Sunil",
            "Chantal",
            "Celine",
            "Gwyneth",
            "Gérard",
            "Carla",
            "Liam",
            "Rory",
            "Siobhan",
            "Seoyeon",
            "Takumi",
            "Olivia",
            "Russell",
            "Ava",
            "Amy",
            "Vicki",
            "Ivy",
            "Kimberly",
            "Kendra",
            "Justin",
            "Joey",
            "Kevin",
            "Salli",
        }

        return voice_id in valid_voices
