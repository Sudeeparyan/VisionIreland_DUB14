"""Character identification and voice profile assignment for comic panels."""

import logging
from typing import Dict, List, Optional, Tuple
from .models import Character, VoiceProfile

logger = logging.getLogger(__name__)


class CharacterIdentifier:
    """Identifies characters from Bedrock visual analysis and assigns voice profiles."""

    # Voice profile templates based on personality and demographics
    VOICE_TEMPLATES = {
        'heroic_male': VoiceProfile(
            voice_id='Joanna',  # Polly voice ID
            gender='male',
            age='young-adult',
            tone='heroic'
        ),
        'heroic_female': VoiceProfile(
            voice_id='Joanna',
            gender='female',
            age='young-adult',
            tone='heroic'
        ),
        'comedic_male': VoiceProfile(
            voice_id='Joey',
            gender='male',
            age='adult',
            tone='comedic'
        ),
        'comedic_female': VoiceProfile(
            voice_id='Joanna',
            gender='female',
            age='adult',
            tone='comedic'
        ),
        'mysterious_male': VoiceProfile(
            voice_id='Matthew',
            gender='male',
            age='adult',
            tone='mysterious'
        ),
        'mysterious_female': VoiceProfile(
            voice_id='Joanna',
            gender='female',
            age='adult',
            tone='mysterious'
        ),
        'child': VoiceProfile(
            voice_id='Joanna',
            gender='neutral',
            age='child',
            tone='innocent'
        ),
        'elderly_male': VoiceProfile(
            voice_id='Brian',
            gender='male',
            age='senior',
            tone='wise'
        ),
        'elderly_female': VoiceProfile(
            voice_id='Joanna',
            gender='female',
            age='senior',
            tone='wise'
        ),
        'neutral': VoiceProfile(
            voice_id='Joanna',
            gender='neutral',
            age='adult',
            tone='neutral'
        ),
    }

    def __init__(self):
        """Initialize character identifier."""
        self.character_counter = 0

    def identify_characters_from_analysis(
        self,
        visual_analysis: Dict,
        panel_number: int
    ) -> List[Tuple[str, Character]]:
        """
        Identify characters from Bedrock visual analysis results.

        Args:
            visual_analysis: Visual analysis dict from Bedrock
            panel_number: Panel number for tracking

        Returns:
            List of (character_name, Character) tuples
        """
        characters = []
        characters_data = visual_analysis.get('characters', [])

        for char_data in characters_data:
            if isinstance(char_data, str):
                # Simple string format
                character = self._create_character_from_description(
                    char_data, panel_number
                )
            elif isinstance(char_data, dict):
                # Structured format from Bedrock
                character = self._create_character_from_dict(
                    char_data, panel_number
                )
            else:
                continue

            if character:
                characters.append((character.name, character))

        return characters

    def _create_character_from_description(
        self,
        description: str,
        panel_number: int
    ) -> Optional[Character]:
        """
        Create a character from a text description.

        Args:
            description: Character description from Bedrock
            panel_number: Panel number

        Returns:
            Character object
        """
        # Extract basic info from description
        name = self._extract_name(description)
        if not name:
            return None

        visual_description = description
        personality = self._infer_personality(description)
        voice_profile = self._assign_voice_profile(description, personality)

        character_id = f"char_{self.character_counter}"
        self.character_counter += 1

        return Character(
            id=character_id,
            name=name,
            visual_description=visual_description,
            personality=personality,
            voice_profile=voice_profile,
            first_introduced=panel_number,
            last_seen=panel_number,
            visual_signatures=self._extract_visual_signatures(description)
        )

    def _create_character_from_dict(
        self,
        char_dict: Dict,
        panel_number: int
    ) -> Optional[Character]:
        """
        Create a character from structured Bedrock data.

        Args:
            char_dict: Character data dictionary from Bedrock
            panel_number: Panel number

        Returns:
            Character object
        """
        name = char_dict.get('name', '')
        if not name:
            return None

        visual_description = char_dict.get('visual_description', '')
        personality = char_dict.get('personality', '')
        
        # Extract visual signatures from dict or infer from description
        if 'visual_signatures' in char_dict and char_dict['visual_signatures']:
            visual_signatures = char_dict['visual_signatures']
        else:
            visual_signatures = self._extract_visual_signatures(visual_description)

        # Use provided voice profile or assign one
        if 'voice_profile' in char_dict and isinstance(char_dict['voice_profile'], dict):
            voice_profile = VoiceProfile(
                voice_id=char_dict['voice_profile'].get('voice_id', 'Joanna'),
                gender=char_dict['voice_profile'].get('gender', 'neutral'),
                age=char_dict['voice_profile'].get('age', 'adult'),
                tone=char_dict['voice_profile'].get('tone', 'neutral')
            )
        else:
            voice_profile = self._assign_voice_profile(
                visual_description, personality
            )

        character_id = f"char_{self.character_counter}"
        self.character_counter += 1

        return Character(
            id=character_id,
            name=name,
            visual_description=visual_description,
            personality=personality,
            voice_profile=voice_profile,
            first_introduced=panel_number,
            last_seen=panel_number,
            visual_signatures=visual_signatures
        )

    def _extract_name(self, description: str) -> Optional[str]:
        """
        Extract character name from description.

        Args:
            description: Character description

        Returns:
            Character name or None
        """
        # Simple heuristic: first capitalized word or phrase
        words = description.split()
        for word in words:
            if word and word[0].isupper():
                return word.rstrip(',:;.')
        return None

    def _infer_personality(self, description: str) -> str:
        """
        Infer character personality from description.

        Args:
            description: Character description

        Returns:
            Personality description
        """
        description_lower = description.lower()

        # Simple keyword-based inference
        if any(word in description_lower for word in ['hero', 'brave', 'strong', 'powerful']):
            return 'heroic'
        elif any(word in description_lower for word in ['funny', 'comic', 'laugh', 'silly']):
            return 'comedic'
        elif any(word in description_lower for word in ['dark', 'mysterious', 'shadow', 'secret']):
            return 'mysterious'
        elif any(word in description_lower for word in ['child', 'young', 'small', 'kid']):
            return 'innocent'
        elif any(word in description_lower for word in ['old', 'elder', 'wise', 'ancient']):
            return 'wise'
        else:
            return 'neutral'

    def _assign_voice_profile(
        self,
        visual_description: str,
        personality: str
    ) -> VoiceProfile:
        """
        Assign voice profile based on visual description and personality.

        Args:
            visual_description: Character visual description
            personality: Character personality

        Returns:
            VoiceProfile object
        """
        description_lower = visual_description.lower()

        # Infer gender from description - check female first to avoid "man" in "woman"
        gender = 'neutral'
        if any(word in description_lower for word in ['woman', 'female', 'girl', 'she', 'her']):
            gender = 'female'
        elif any(word in description_lower for word in ['man', 'male', 'boy', 'he', 'his']):
            gender = 'male'

        # Infer age from description
        age = 'adult'
        if any(word in description_lower for word in ['child', 'kid', 'boy', 'girl']):
            age = 'child'
        elif any(word in description_lower for word in ['old', 'elder', 'aged', 'senior']):
            age = 'senior'
        elif any(word in description_lower for word in ['teen', 'young', 'youth']):
            age = 'young-adult'

        # Select voice template based on personality and demographics
        template_key = self._select_voice_template(personality, gender, age)
        return self.VOICE_TEMPLATES.get(template_key, self.VOICE_TEMPLATES['neutral'])

    def _select_voice_template(
        self,
        personality: str,
        gender: str,
        age: str
    ) -> str:
        """
        Select voice template key based on personality and demographics.

        Args:
            personality: Character personality
            gender: Character gender
            age: Character age

        Returns:
            Voice template key
        """
        if age == 'child':
            return 'child'
        elif age == 'senior':
            if gender == 'male':
                return 'elderly_male'
            else:
                return 'elderly_female'
        elif personality == 'heroic':
            if gender == 'male':
                return 'heroic_male'
            else:
                return 'heroic_female'
        elif personality == 'comedic':
            if gender == 'male':
                return 'comedic_male'
            else:
                return 'comedic_female'
        elif personality == 'mysterious':
            if gender == 'male':
                return 'mysterious_male'
            else:
                return 'mysterious_female'
        else:
            return 'neutral'

    def _extract_visual_signatures(self, description: str) -> List[str]:
        """
        Extract distinctive visual features from description.

        Args:
            description: Character description

        Returns:
            List of visual signature strings
        """
        signatures = []

        # Extract color mentions
        colors = ['red', 'blue', 'green', 'yellow', 'black', 'white', 'purple', 'orange']
        for color in colors:
            if color in description.lower():
                signatures.append(f'{color} clothing/appearance')

        # Extract distinctive features
        features = ['scar', 'tattoo', 'mask', 'cape', 'hat', 'glasses', 'beard', 'long hair']
        for feature in features:
            if feature in description.lower():
                signatures.append(feature)

        return signatures

    def reset(self) -> None:
        """Reset identifier for new comic."""
        self.character_counter = 0
        logger.info("Character identifier reset")
