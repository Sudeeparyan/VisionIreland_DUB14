"""Bedrock vision-based panel analysis for comic narratives."""

import logging
import base64
from typing import Optional, List
import json

from .models import PanelNarrative, VisualAnalysis, DialogueLine, Character, Scene
from .character_tracker import CharacterTracker
from .scene_tracker import SceneTracker
from .character_identifier import CharacterIdentifier
from .analyzer import BedrockPanelAnalyzer

logger = logging.getLogger(__name__)


class PanelAnalysisPipeline:
    """Orchestrates Bedrock vision-based panel analysis with character and scene tracking."""

    def __init__(self):
        """Initialize panel analysis pipeline."""
        self.bedrock_analyzer = BedrockPanelAnalyzer()
        self.character_tracker = CharacterTracker()
        self.scene_tracker = SceneTracker()
        self.character_identifier = CharacterIdentifier()
        self.panel_narratives: List[PanelNarrative] = []

    def analyze_panel(
        self,
        panel_id: str,
        panel_number: int,
        image_data: bytes,
        image_format: str = 'png'
    ) -> Optional[PanelNarrative]:
        """Analyze a single panel using Bedrock vision.
        
        Args:
            panel_id: Unique panel identifier
            panel_number: Sequential panel number
            image_data: Panel image as bytes
            image_format: Image format (png, jpeg)
            
        Returns:
            PanelNarrative object with analysis results
        """
        try:
            # Encode image for Bedrock
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Call Bedrock for vision analysis
            analysis_result = self.bedrock_analyzer.analyze_panel(
                panel_id=panel_id,
                image_data=image_base64,
                image_format=image_format,
                context=self.bedrock_analyzer.get_context()
            )
            
            if not analysis_result:
                logger.error(f"Failed to analyze panel {panel_id}")
                return None
            
            # Process character information
            characters_in_panel = self._process_characters(
                panel_number,
                analysis_result.get('characters', [])
            )
            
            # Process scene information
            scene_id = self._process_scene(
                panel_number,
                analysis_result.get('scene', {})
            )
            
            # Create panel narrative
            panel_narrative = PanelNarrative(
                panel_id=panel_id,
                visual_analysis=VisualAnalysis(
                    characters=characters_in_panel,
                    objects=analysis_result.get('objects', []),
                    spatial_layout=analysis_result.get('spatial_layout', ''),
                    colors=analysis_result.get('colors', []),
                    mood=analysis_result.get('mood', '')
                ),
                action_description=analysis_result.get('action_description', ''),
                dialogue=self._process_dialogue(analysis_result.get('dialogue', [])),
                scene_description=analysis_result.get('scene_description') if scene_id else None,
                audio_description=analysis_result.get('audio_description', '')
            )
            
            self.panel_narratives.append(panel_narrative)
            logger.info(f"Successfully analyzed panel {panel_id}")
            
            return panel_narrative
            
        except Exception as e:
            logger.error(f"Failed to analyze panel {panel_id}: {e}")
            return None

    def _process_characters(self, panel_number: int, characters_data: List[dict]) -> List[str]:
        """Process character information from Bedrock analysis.
        
        Identifies new characters, assigns voice profiles, and tracks appearances.
        
        Args:
            panel_number: Panel number
            characters_data: Character data from Bedrock
            
        Returns:
            List of character IDs appearing in panel
        """
        character_ids = []
        
        # Use character identifier to process characters
        identified_characters = self.character_identifier.identify_characters_from_analysis(
            {'characters': characters_data},
            panel_number
        )
        
        for character_name, identified_character in identified_characters:
            # Check if character already exists by name
            existing_char = self.character_tracker.get_character_by_name(character_name)
            
            if existing_char:
                # Record appearance of existing character
                self.character_tracker.record_appearance(
                    character_id=existing_char.id,
                    panel_number=panel_number,
                    visual_description=identified_character.visual_description
                    if identified_character.visual_description != existing_char.visual_description
                    else None
                )
                character_ids.append(existing_char.id)
            else:
                # Register new character with identified properties
                character = self.character_tracker.register_character(
                    name=identified_character.name,
                    visual_description=identified_character.visual_description,
                    personality=identified_character.personality,
                    voice_profile=identified_character.voice_profile,
                    panel_number=panel_number,
                    visual_signatures=identified_character.visual_signatures
                )
                character_ids.append(character.id)
        
        return character_ids

    def _process_scene(self, panel_number: int, scene_data: dict) -> Optional[str]:
        """Process scene information from Bedrock analysis.
        
        Args:
            panel_number: Panel number
            scene_data: Scene data from Bedrock
            
        Returns:
            Scene ID, or None if no scene data
        """
        if not scene_data:
            return None
        
        location = scene_data.get('location', '')
        if not location:
            return None
        
        # Check if scene already exists
        existing_scene = self.scene_tracker.get_scene_by_location(location)
        
        if existing_scene:
            # Set scene for this panel
            self.scene_tracker.set_scene_for_panel(
                scene_id=existing_scene.id,
                panel_number=panel_number,
                visual_description=scene_data.get('visual_description')
            )
            return existing_scene.id
        else:
            # Register new scene
            scene = self.scene_tracker.register_scene(
                location=location,
                visual_description=scene_data.get('visual_description', ''),
                panel_number=panel_number,
                time_of_day=scene_data.get('time_of_day'),
                atmosphere=scene_data.get('atmosphere'),
                color_palette=scene_data.get('color_palette', []),
                lighting=scene_data.get('lighting')
            )
            self.scene_tracker.set_scene_for_panel(scene.id, panel_number)
            return scene.id

    def _process_dialogue(self, dialogue_data: List[dict]) -> List[DialogueLine]:
        """Process dialogue information from Bedrock analysis.
        
        Args:
            dialogue_data: Dialogue data from Bedrock
            
        Returns:
            List of DialogueLine objects
        """
        dialogue_lines = []
        
        for line_data in dialogue_data:
            character_name = line_data.get('character', '')
            text = line_data.get('text', '')
            emotion = line_data.get('emotion')
            
            # Find character ID by name
            character = self.character_tracker.get_character_by_name(character_name)
            character_id = character.id if character else character_name
            
            dialogue_line = DialogueLine(
                character_id=character_id,
                text=text,
                emotion=emotion
            )
            dialogue_lines.append(dialogue_line)
        
        return dialogue_lines

    def analyze_panel_batch(
        self,
        panels: List[tuple]
    ) -> List[Optional[PanelNarrative]]:
        """Analyze multiple panels.
        
        Args:
            panels: List of (panel_id, panel_number, image_data, image_format) tuples
            
        Returns:
            List of PanelNarrative objects
        """
        narratives = []
        for panel_id, panel_number, image_data, image_format in panels:
            narrative = self.analyze_panel(panel_id, panel_number, image_data, image_format)
            narratives.append(narrative)
        
        return narratives

    def get_all_characters(self) -> List[Character]:
        """Get all characters identified in comic.
        
        Returns:
            List of Character objects
        """
        return self.character_tracker.get_all_characters()

    def get_all_scenes(self) -> List[Scene]:
        """Get all scenes identified in comic.
        
        Returns:
            List of Scene objects
        """
        return self.scene_tracker.get_all_scenes()

    def get_panel_narratives(self) -> List[PanelNarrative]:
        """Get all panel narratives.
        
        Returns:
            List of PanelNarrative objects
        """
        return self.panel_narratives.copy()

    def reset(self) -> None:
        """Reset pipeline for new comic."""
        self.character_tracker.reset()
        self.scene_tracker.reset()
        self.character_identifier.reset()
        self.panel_narratives.clear()
        self.bedrock_analyzer.reset_context()
        logger.info("Panel analysis pipeline reset")
