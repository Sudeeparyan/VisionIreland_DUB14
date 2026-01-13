"""Narrative generation following professional audio description standards."""

import logging
from typing import List, Optional
import re

from .models import PanelNarrative, Character, Scene, DialogueLine

logger = logging.getLogger(__name__)


class NarrativeGenerator:
    """Generates audio descriptions following professional standards."""

    # Audio description standards
    PRESENT_TENSE_VERBS = {
        'walks': 'walks', 'runs': 'runs', 'jumps': 'jumps',
        'sits': 'sits', 'stands': 'stands', 'lies': 'lies',
        'speaks': 'speaks', 'shouts': 'shouts', 'whispers': 'whispers',
        'looks': 'looks', 'sees': 'sees', 'watches': 'watches',
    }

    def __init__(self):
        """Initialize narrative generator."""
        self.generated_narratives = []

    def generate_narrative(
        self,
        panel_narrative: PanelNarrative,
        characters: dict,
        scenes: dict,
        is_first_appearance: dict = None
    ) -> str:
        """Generate audio description for a panel.
        
        Args:
            panel_narrative: Panel narrative with visual analysis
            characters: Dictionary of character ID to Character object
            scenes: Dictionary of scene ID to Scene object
            is_first_appearance: Dictionary tracking first appearances
            
        Returns:
            Generated audio description
        """
        if is_first_appearance is None:
            is_first_appearance = {}
        
        narrative_parts = []
        
        # Add scene description if new scene
        if panel_narrative.scene_description:
            scene_intro = self._generate_scene_introduction(
                panel_narrative.scene_description
            )
            narrative_parts.append(scene_intro)
        
        # Add character introductions if new characters
        for char_id in panel_narrative.visual_analysis.characters:
            if char_id not in is_first_appearance:
                character = characters.get(char_id)
                if character:
                    char_intro = self._generate_character_introduction(character)
                    narrative_parts.append(char_intro)
                    is_first_appearance[char_id] = True
        
        # Add action description with spatial details
        if panel_narrative.action_description:
            action = self._enhance_action_description(
                panel_narrative.action_description,
                panel_narrative.visual_analysis
            )
            narrative_parts.append(action)
        
        # Add dialogue integrated with action
        if panel_narrative.dialogue:
            dialogue_text = self._integrate_dialogue(
                panel_narrative.dialogue,
                characters
            )
            narrative_parts.append(dialogue_text)
        
        # Combine all parts
        full_narrative = ' '.join(filter(None, narrative_parts))
        
        # Ensure present tense and active voice
        full_narrative = self._enforce_present_tense(full_narrative)
        
        self.generated_narratives.append(full_narrative)
        logger.info(f"Generated narrative for panel {panel_narrative.panel_id}")
        
        return full_narrative

    def _generate_scene_introduction(self, scene_description: str) -> str:
        """Generate scene introduction following standards.
        
        Args:
            scene_description: Scene description from analysis
            
        Returns:
            Formatted scene introduction
        """
        # Ensure present tense
        description = self._enforce_present_tense(scene_description)
        
        # Add context and atmosphere
        return f"The scene opens with {description}."

    def _generate_character_introduction(self, character: Character) -> str:
        """Generate character introduction following standards.
        
        Args:
            character: Character object
            
        Returns:
            Formatted character introduction
        """
        intro = f"{character.name} appears"
        
        if character.visual_description:
            intro += f", {character.visual_description.lower()}"
        
        if character.personality:
            intro += f". {character.personality}"
        
        return intro + "."

    def _enhance_action_description(
        self,
        action_description: str,
        visual_analysis
    ) -> str:
        """Enhance action description with spatial details.
        
        Args:
            action_description: Base action description
            visual_analysis: Visual analysis with spatial information
            
        Returns:
            Enhanced action description with spatial details
        """
        enhanced = action_description
        
        # Add spatial layout if available
        if visual_analysis.spatial_layout:
            enhanced += f" {visual_analysis.spatial_layout}"
        
        # Add color context if available
        if visual_analysis.colors:
            colors_str = ', '.join(visual_analysis.colors[:3])
            enhanced += f" The scene is dominated by {colors_str}."
        
        # Add mood/emotion if available
        if visual_analysis.mood:
            enhanced += f" The mood is {visual_analysis.mood}."
        
        return enhanced

    def _integrate_dialogue(
        self,
        dialogue_lines: List[DialogueLine],
        characters: dict
    ) -> str:
        """Integrate dialogue naturally with action.
        
        Args:
            dialogue_lines: List of dialogue lines
            characters: Dictionary of character ID to Character object
            
        Returns:
            Integrated dialogue text
        """
        dialogue_parts = []
        
        for line in dialogue_lines:
            character = characters.get(line.character_id)
            char_name = character.name if character else line.character_id
            
            # Format dialogue with emotion if available
            if line.emotion:
                dialogue_parts.append(
                    f"{char_name} says, {line.emotion}, \"{line.text}\""
                )
            else:
                dialogue_parts.append(f"{char_name} says, \"{line.text}\"")
        
        return ' '.join(dialogue_parts)

    def _enforce_present_tense(self, text: str) -> str:
        """Enforce present tense and active voice.
        
        Args:
            text: Text to convert
            
        Returns:
            Text in present tense
        """
        # Replace common past tense with present
        replacements = {
            r'\bwalked\b': 'walks',
            r'\bran\b': 'runs',
            r'\bjumped\b': 'jumps',
            r'\bsat\b': 'sits',
            r'\bstood\b': 'stands',
            r'\blaid\b': 'lies',
            r'\bspoke\b': 'speaks',
            r'\bshouted\b': 'shouts',
            r'\bwhispered\b': 'whispers',
            r'\blooked\b': 'looks',
            r'\bsaw\b': 'sees',
            r'\bwatched\b': 'watches',
            r'\bwas\b': 'is',
            r'\bwere\b': 'are',
            r'\bhad\b': 'has',
        }
        
        result = text
        for past, present in replacements.items():
            result = re.sub(past, present, result, flags=re.IGNORECASE)
        
        return result

    def generate_transition(
        self,
        from_scene: Optional[Scene],
        to_scene: Scene,
        characters_present: List[Character]
    ) -> str:
        """Generate smooth narrative transition between scenes.
        
        Args:
            from_scene: Previous scene (or None if first scene)
            to_scene: New scene
            characters_present: Characters present in new scene
            
        Returns:
            Transition narrative
        """
        if from_scene is None:
            return f"We begin in {to_scene.location}."
        
        # Create smooth transition
        transition = f"The scene shifts to {to_scene.location}."
        
        if to_scene.atmosphere:
            transition += f" {to_scene.atmosphere}"
        
        if characters_present:
            char_names = ', '.join([c.name for c in characters_present[:3]])
            transition += f" {char_names} are present."
        
        return transition

    def get_all_narratives(self) -> List[str]:
        """Get all generated narratives.
        
        Returns:
            List of generated narrative strings
        """
        return self.generated_narratives.copy()

    def validate_narrative(self, narrative: str) -> dict:
        """Validate narrative against audio description standards.
        
        Args:
            narrative: Narrative text to validate
            
        Returns:
            Dictionary with validation results
        """
        issues = []
        
        # Check for present tense
        past_tense_words = re.findall(r'\b(was|were|had|walked|ran|jumped)\b', narrative, re.IGNORECASE)
        if past_tense_words:
            issues.append(f"Found past tense words: {set(past_tense_words)}")
        
        # Check for passive voice indicators
        passive_indicators = re.findall(r'\bwas\s+\w+ed\b', narrative, re.IGNORECASE)
        if passive_indicators:
            issues.append(f"Found passive voice: {passive_indicators}")
        
        # Check for spatial details
        spatial_keywords = ['left', 'right', 'center', 'above', 'below', 'behind', 'front']
        has_spatial = any(keyword in narrative.lower() for keyword in spatial_keywords)
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'has_spatial_details': has_spatial,
            'length': len(narrative),
        }

    def reset(self) -> None:
        """Reset generator for new comic."""
        self.generated_narratives.clear()
        logger.info("Narrative generator reset")
