"""Context management for character and scene tracking"""

from typing import Optional, Dict, List
from .models import Character, Scene, BedrockAnalysisContext, VoiceProfile


class ContextManager:
    """Manages character and scene context throughout comic processing"""

    def __init__(self):
        """Initialize context manager"""
        self.context = BedrockAnalysisContext()
        self._character_counter = 0
        self._scene_counter = 0

    def add_character(
        self,
        name: str,
        visual_description: str,
        personality: str,
        voice_profile: VoiceProfile,
        panel_number: int,
        visual_signatures: Optional[List[str]] = None,
    ) -> Character:
        """
        Add a new character to the context.

        Args:
            name: Character name
            visual_description: Description of character's appearance
            personality: Character personality traits
            voice_profile: Voice profile for the character
            panel_number: Panel where character is introduced
            visual_signatures: Distinctive visual features

        Returns:
            Created Character object
        """
        character_id = f"char_{self._character_counter}"
        self._character_counter += 1

        character = Character(
            id=character_id,
            name=name,
            visual_description=visual_description,
            personality=personality,
            voice_profile=voice_profile,
            first_introduced=panel_number,
            last_seen=panel_number,
            visual_signatures=visual_signatures or [],
        )

        self.context.characters[character_id] = character
        return character

    def get_character(self, character_id: str) -> Optional[Character]:
        """
        Retrieve a character from context.

        Args:
            character_id: Character identifier

        Returns:
            Character object or None if not found
        """
        return self.context.characters.get(character_id)

    def get_character_by_name(self, name: str) -> Optional[Character]:
        """
        Find a character by name.

        Args:
            name: Character name

        Returns:
            Character object or None if not found
        """
        for character in self.context.characters.values():
            if character.name.lower() == name.lower():
                return character
        return None

    def update_character_last_seen(
        self, character_id: str, panel_number: int
    ) -> None:
        """
        Update when a character was last seen.

        Args:
            character_id: Character identifier
            panel_number: Current panel number
        """
        if character_id in self.context.characters:
            self.context.characters[character_id].last_seen = panel_number

    def add_scene(
        self,
        location: str,
        visual_description: str,
        panel_number: int,
        time_of_day: Optional[str] = None,
        atmosphere: Optional[str] = None,
        color_palette: Optional[List[str]] = None,
        lighting: Optional[str] = None,
    ) -> Scene:
        """
        Add a new scene to the context.

        Args:
            location: Scene location name
            visual_description: Description of the scene
            panel_number: Panel where scene is introduced
            time_of_day: Time of day (optional)
            atmosphere: Scene atmosphere (optional)
            color_palette: Color palette (optional)
            lighting: Lighting description (optional)

        Returns:
            Created Scene object
        """
        scene_id = f"scene_{self._scene_counter}"
        self._scene_counter += 1

        scene = Scene(
            id=scene_id,
            location=location,
            visual_description=visual_description,
            first_introduced=panel_number,
            last_seen=panel_number,
            time_of_day=time_of_day,
            atmosphere=atmosphere,
            color_palette=color_palette or [],
            lighting=lighting,
        )

        self.context.scenes[scene_id] = scene
        return scene

    def get_scene(self, scene_id: str) -> Optional[Scene]:
        """
        Retrieve a scene from context.

        Args:
            scene_id: Scene identifier

        Returns:
            Scene object or None if not found
        """
        return self.context.scenes.get(scene_id)

    def get_scene_by_location(self, location: str) -> Optional[Scene]:
        """
        Find a scene by location name.

        Args:
            location: Location name

        Returns:
            Scene object or None if not found
        """
        for scene in self.context.scenes.values():
            if scene.location.lower() == location.lower():
                return scene
        return None

    def update_scene_last_seen(self, scene_id: str, panel_number: int) -> None:
        """
        Update when a scene was last seen.

        Args:
            scene_id: Scene identifier
            panel_number: Current panel number
        """
        if scene_id in self.context.scenes:
            self.context.scenes[scene_id].last_seen = panel_number

    def get_all_characters(self) -> Dict[str, Character]:
        """Get all characters in context"""
        return self.context.characters.copy()

    def get_all_scenes(self) -> Dict[str, Scene]:
        """Get all scenes in context"""
        return self.context.scenes.copy()

    def get_context(self) -> BedrockAnalysisContext:
        """Get the full context"""
        return self.context

    def reset(self) -> None:
        """Reset context for new comic"""
        self.context = BedrockAnalysisContext()
        self._character_counter = 0
        self._scene_counter = 0

    def set_story_state(self, key: str, value) -> None:
        """
        Set a story state value.

        Args:
            key: State key
            value: State value
        """
        self.context.story_state[key] = value

    def get_story_state(self, key: str, default=None):
        """
        Get a story state value.

        Args:
            key: State key
            default: Default value if key not found

        Returns:
            State value or default
        """
        return self.context.story_state.get(key, default)
