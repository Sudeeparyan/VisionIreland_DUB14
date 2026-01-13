"""Character identification and tracking for comic panels."""

import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

from .models import Character, VoiceProfile

logger = logging.getLogger(__name__)


@dataclass
class CharacterAppearance:
    """Record of a character's appearance in a panel."""
    character_id: str
    panel_number: int
    visual_description: str
    position: Optional[str] = None
    emotion: Optional[str] = None


class CharacterTracker:
    """Tracks character identification and appearances across panels."""

    def __init__(self):
        """Initialize character tracker."""
        self.characters: Dict[str, Character] = {}
        self.appearances: List[CharacterAppearance] = []
        self.character_counter = 0

    def register_character(
        self,
        name: str,
        visual_description: str,
        personality: str,
        voice_profile: VoiceProfile,
        panel_number: int,
        visual_signatures: List[str] = None
    ) -> Character:
        """Register a new character.
        
        Args:
            name: Character name
            visual_description: Description of character appearance
            personality: Character personality traits
            voice_profile: Voice profile for character
            panel_number: Panel where character first appears
            visual_signatures: Distinctive visual features
            
        Returns:
            Character object
        """
        character_id = f"char_{self.character_counter}"
        self.character_counter += 1
        
        character = Character(
            id=character_id,
            name=name,
            visual_description=visual_description,
            personality=personality,
            voice_profile=voice_profile,
            first_introduced=panel_number,
            last_seen=panel_number,
            visual_signatures=visual_signatures or []
        )
        
        self.characters[character_id] = character
        logger.info(f"Registered new character: {name} (ID: {character_id})")
        
        return character

    def record_appearance(
        self,
        character_id: str,
        panel_number: int,
        visual_description: str = None,
        position: str = None,
        emotion: str = None
    ) -> Optional[CharacterAppearance]:
        """Record character appearance in a panel.
        
        Args:
            character_id: ID of character
            panel_number: Panel number where character appears
            visual_description: Updated visual description if changed
            position: Character position in panel
            emotion: Character emotion/expression
            
        Returns:
            CharacterAppearance object, or None if character not found
        """
        if character_id not in self.characters:
            logger.warning(f"Character {character_id} not found")
            return None
        
        character = self.characters[character_id]
        character.last_seen = panel_number
        
        # Update visual description if provided
        if visual_description:
            character.visual_description = visual_description
        
        appearance = CharacterAppearance(
            character_id=character_id,
            panel_number=panel_number,
            visual_description=character.visual_description,
            position=position,
            emotion=emotion
        )
        
        self.appearances.append(appearance)
        logger.info(f"Recorded appearance of {character.name} in panel {panel_number}")
        
        return appearance

    def get_character(self, character_id: str) -> Optional[Character]:
        """Get character by ID.
        
        Args:
            character_id: Character ID
            
        Returns:
            Character object, or None if not found
        """
        return self.characters.get(character_id)

    def get_character_by_name(self, name: str) -> Optional[Character]:
        """Get character by name.
        
        Args:
            name: Character name
            
        Returns:
            Character object, or None if not found
        """
        for character in self.characters.values():
            if character.name.lower() == name.lower():
                return character
        return None

    def get_all_characters(self) -> List[Character]:
        """Get all registered characters.
        
        Returns:
            List of Character objects
        """
        return list(self.characters.values())

    def get_characters_in_panel(self, panel_number: int) -> List[Character]:
        """Get all characters appearing in a specific panel.
        
        Args:
            panel_number: Panel number
            
        Returns:
            List of Character objects
        """
        character_ids = set()
        for appearance in self.appearances:
            if appearance.panel_number == panel_number:
                character_ids.add(appearance.character_id)
        
        return [self.characters[cid] for cid in character_ids if cid in self.characters]

    def get_character_appearances(self, character_id: str) -> List[CharacterAppearance]:
        """Get all appearances of a character.
        
        Args:
            character_id: Character ID
            
        Returns:
            List of CharacterAppearance objects
        """
        return [app for app in self.appearances if app.character_id == character_id]

    def get_character_appearance_count(self, character_id: str) -> int:
        """Get number of times character appears.
        
        Args:
            character_id: Character ID
            
        Returns:
            Number of appearances
        """
        return len(self.get_character_appearances(character_id))

    def is_character_introduced(self, character_id: str, panel_number: int) -> bool:
        """Check if character has been introduced by a given panel.
        
        Args:
            character_id: Character ID
            panel_number: Panel number to check
            
        Returns:
            True if character introduced by this panel
        """
        if character_id not in self.characters:
            return False
        
        character = self.characters[character_id]
        return character.first_introduced <= panel_number

    def get_introduced_characters(self, panel_number: int) -> List[Character]:
        """Get all characters introduced up to a given panel.
        
        Args:
            panel_number: Panel number
            
        Returns:
            List of Character objects
        """
        return [
            char for char in self.characters.values()
            if char.first_introduced <= panel_number
        ]

    def get_new_characters_in_panel(self, panel_number: int) -> List[Character]:
        """Get characters first appearing in a specific panel.
        
        Args:
            panel_number: Panel number
            
        Returns:
            List of Character objects
        """
        return [
            char for char in self.characters.values()
            if char.first_introduced == panel_number
        ]

    def update_character_voice(self, character_id: str, voice_profile: VoiceProfile) -> bool:
        """Update character's voice profile.
        
        Args:
            character_id: Character ID
            voice_profile: New voice profile
            
        Returns:
            True if update successful
        """
        if character_id not in self.characters:
            logger.warning(f"Character {character_id} not found")
            return False
        
        self.characters[character_id].voice_profile = voice_profile
        logger.info(f"Updated voice profile for character {character_id}")
        return True

    def add_visual_signature(self, character_id: str, signature: str) -> bool:
        """Add distinctive visual feature to character.
        
        Args:
            character_id: Character ID
            signature: Visual signature description
            
        Returns:
            True if added successfully
        """
        if character_id not in self.characters:
            logger.warning(f"Character {character_id} not found")
            return False
        
        character = self.characters[character_id]
        if signature not in character.visual_signatures:
            character.visual_signatures.append(signature)
            logger.info(f"Added visual signature to character {character_id}")
        
        return True

    def get_character_summary(self, character_id: str) -> Optional[Dict]:
        """Get summary information about a character.
        
        Args:
            character_id: Character ID
            
        Returns:
            Dictionary with character summary, or None if not found
        """
        if character_id not in self.characters:
            return None
        
        character = self.characters[character_id]
        appearances = self.get_character_appearances(character_id)
        
        return {
            'id': character.id,
            'name': character.name,
            'visual_description': character.visual_description,
            'personality': character.personality,
            'voice_profile': {
                'voice_id': character.voice_profile.voice_id,
                'gender': character.voice_profile.gender,
                'age': character.voice_profile.age,
                'tone': character.voice_profile.tone,
            },
            'first_introduced': character.first_introduced,
            'last_seen': character.last_seen,
            'appearance_count': len(appearances),
            'visual_signatures': character.visual_signatures,
        }

    def reset(self) -> None:
        """Reset tracker for new comic."""
        self.characters.clear()
        self.appearances.clear()
        self.character_counter = 0
        logger.info("Character tracker reset")
