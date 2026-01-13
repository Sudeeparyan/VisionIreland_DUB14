"""Property-based tests for audio description standards.

Feature: comic-audio-narrator, Properties 6-10: Audio Description Standards
Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
import re

from src.bedrock_analysis.narrative_generator import NarrativeGenerator
from src.bedrock_analysis.models import (
    PanelNarrative, Character, Scene, DialogueLine, VisualAnalysis, VoiceProfile
)


# Strategies for generating test data
@st.composite
def visual_analysis_strategy(draw):
    """Generate random visual analysis data."""
    return VisualAnalysis(
        characters=draw(st.lists(st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz'), min_size=1, max_size=3)),
        objects=draw(st.lists(st.text(min_size=1, max_size=20), max_size=5)),
        spatial_layout=draw(st.sampled_from([
            "Hero stands on the left, villain on the right",
            "Characters positioned in the center of the frame",
            "Action moves from left to right across the panel",
            "Character in foreground, city skyline behind",
            "Two figures face each other in the middle"
        ])),
        colors=draw(st.lists(st.sampled_from(['red', 'blue', 'green', 'yellow', 'black', 'white', 'orange']), min_size=1, max_size=4)),
        mood=draw(st.sampled_from(['tense', 'joyful', 'mysterious', 'dramatic', 'peaceful', 'chaotic']))
    )


@st.composite
def character_strategy(draw):
    """Generate random character data."""
    return Character(
        id=draw(st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz')),
        name=draw(st.sampled_from(['Hero', 'Villain', 'Sidekick', 'Mentor', 'Stranger'])),
        visual_description=draw(st.sampled_from([
            'tall with dark hair',
            'wearing a red cape',
            'muscular build with a scar',
            'young woman with glasses',
            'elderly man with white beard'
        ])),
        personality=draw(st.sampled_from([
            'brave and determined',
            'cunning and mysterious',
            'cheerful and optimistic',
            'wise and patient',
            'fierce and protective'
        ])),
        voice_profile=VoiceProfile(
            voice_id='Matthew',
            gender='male',
            age='adult',
            tone='heroic'
        ),
        first_introduced=1,
        last_seen=1,
        visual_signatures=['cape', 'mask']
    )


@st.composite
def dialogue_line_strategy(draw):
    """Generate random dialogue line."""
    return DialogueLine(
        character_id=draw(st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz')),
        text=draw(st.sampled_from([
            "We must stop them!",
            "I won't let you win.",
            "Look out behind you!",
            "This is our moment.",
            "Together we can do this."
        ])),
        emotion=draw(st.sampled_from(['determined', 'angry', 'worried', 'hopeful', 'calm', None]))
    )


@st.composite
def panel_narrative_strategy(draw):
    """Generate random panel narrative."""
    return PanelNarrative(
        panel_id=draw(st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz0123456789')),
        visual_analysis=draw(visual_analysis_strategy()),
        scene_description=draw(st.sampled_from([
            "A dark alley in the city at night",
            "Bright sunny rooftop overlooking the skyline",
            "Underground laboratory with glowing equipment",
            None
        ])),
        action_description=draw(st.sampled_from([
            "Hero leaps across the gap between buildings",
            "Villain raises a glowing weapon",
            "Characters run through the crowded street",
            "Two figures clash in mid-air"
        ])),
        dialogue=draw(st.lists(dialogue_line_strategy(), min_size=0, max_size=3)),
        character_updates=None,
        audio_description=""
    )


class TestAudioDescriptionSpatialDetails:
    """Property 6: Audio Description Spatial Details
    
    For any panel describing action or movement, the generated audio description
    SHALL include specific details about character positions, directions, and
    spatial relationships.
    
    **Feature: comic-audio-narrator, Property 6: Audio Description Spatial Details**
    **Validates: Requirements 9.1**
    """

    @settings(deadline=None, max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(panel_narrative=panel_narrative_strategy(), character=character_strategy())
    def test_spatial_details_included_in_action_descriptions(self, panel_narrative, character):
        """Property: Action descriptions SHALL include spatial details.
        
        **Feature: comic-audio-narrator, Property 6: Audio Description Spatial Details**
        **Validates: Requirements 9.1**
        """
        generator = NarrativeGenerator()
        characters = {character.id: character}
        scenes = {}
        
        # Ensure visual analysis has spatial layout
        if panel_narrative.visual_analysis.spatial_layout:
            narrative = generator.generate_narrative(
                panel_narrative, characters, scenes
            )
            
            # Verify spatial keywords are present
            spatial_keywords = ['left', 'right', 'center', 'above', 'below', 
                              'behind', 'front', 'across', 'between', 'foreground',
                              'background', 'middle', 'position']
            
            has_spatial = any(keyword in narrative.lower() for keyword in spatial_keywords)
            
            # Validate using the generator's validation method
            validation = generator.validate_narrative(narrative)
            
            assert has_spatial or validation['has_spatial_details'], \
                f"Narrative should include spatial details: {narrative}"


class TestAudioDescriptionTenseAndVoice:
    """Property 7: Audio Description Tense and Voice
    
    For any visual element being narrated, the generated description SHALL use
    present tense and active voice.
    
    **Feature: comic-audio-narrator, Property 7: Audio Description Tense and Voice**
    **Validates: Requirements 9.2**
    """

    @settings(deadline=None, max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(panel_narrative=panel_narrative_strategy(), character=character_strategy())
    def test_present_tense_used_in_narratives(self, panel_narrative, character):
        """Property: Narratives SHALL use present tense.
        
        **Feature: comic-audio-narrator, Property 7: Audio Description Tense and Voice**
        **Validates: Requirements 9.2**
        """
        generator = NarrativeGenerator()
        characters = {character.id: character}
        scenes = {}
        
        narrative = generator.generate_narrative(
            panel_narrative, characters, scenes
        )
        
        # Check for common past tense words that should have been converted
        past_tense_patterns = [
            r'\bwalked\b', r'\bran\b', r'\bjumped\b', r'\bsat\b',
            r'\bstood\b', r'\bspoke\b', r'\bshouted\b', r'\bwhispered\b'
        ]
        
        for pattern in past_tense_patterns:
            matches = re.findall(pattern, narrative, re.IGNORECASE)
            assert len(matches) == 0, \
                f"Found past tense '{matches}' in narrative: {narrative}"

    @settings(deadline=None, max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(panel_narrative=panel_narrative_strategy(), character=character_strategy())
    def test_active_voice_preferred(self, panel_narrative, character):
        """Property: Narratives SHALL prefer active voice.
        
        **Feature: comic-audio-narrator, Property 7: Audio Description Tense and Voice**
        **Validates: Requirements 9.2**
        """
        generator = NarrativeGenerator()
        characters = {character.id: character}
        scenes = {}
        
        narrative = generator.generate_narrative(
            panel_narrative, characters, scenes
        )
        
        # Check for passive voice indicators
        passive_patterns = [
            r'\bwas\s+\w+ed\b',  # "was walked", "was seen"
            r'\bwere\s+\w+ed\b',  # "were taken"
            r'\bbeen\s+\w+ed\b',  # "been moved"
        ]
        
        passive_count = 0
        for pattern in passive_patterns:
            passive_count += len(re.findall(pattern, narrative, re.IGNORECASE))
        
        # Allow some passive voice but not excessive
        assert passive_count <= 2, \
            f"Too much passive voice ({passive_count} instances) in: {narrative}"


class TestAudioDescriptionContext:
    """Property 8: Audio Description Context
    
    For any object or environment being described, the generated description
    SHALL include relevant details that establish context and atmosphere.
    
    **Feature: comic-audio-narrator, Property 8: Audio Description Context**
    **Validates: Requirements 9.3**
    """

    @settings(deadline=None, max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(panel_narrative=panel_narrative_strategy(), character=character_strategy())
    def test_scene_descriptions_include_atmosphere(self, panel_narrative, character):
        """Property: Scene descriptions SHALL include atmosphere.
        
        **Feature: comic-audio-narrator, Property 8: Audio Description Context**
        **Validates: Requirements 9.3**
        """
        generator = NarrativeGenerator()
        characters = {character.id: character}
        scenes = {}
        
        # Only test when scene description is present
        if panel_narrative.scene_description:
            narrative = generator.generate_narrative(
                panel_narrative, characters, scenes
            )
            
            # Verify scene introduction is present
            assert 'scene' in narrative.lower() or panel_narrative.scene_description.lower() in narrative.lower(), \
                f"Scene description should be included: {narrative}"

    @settings(deadline=None, max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(panel_narrative=panel_narrative_strategy(), character=character_strategy())
    def test_mood_conveyed_in_narrative(self, panel_narrative, character):
        """Property: Narratives SHALL convey mood when available.
        
        **Feature: comic-audio-narrator, Property 8: Audio Description Context**
        **Validates: Requirements 9.3**
        """
        generator = NarrativeGenerator()
        characters = {character.id: character}
        scenes = {}
        
        # Only test when mood is present
        if panel_narrative.visual_analysis.mood:
            narrative = generator.generate_narrative(
                panel_narrative, characters, scenes
            )
            
            # Verify mood is mentioned
            mood = panel_narrative.visual_analysis.mood.lower()
            assert mood in narrative.lower() or 'mood' in narrative.lower(), \
                f"Mood '{mood}' should be conveyed in: {narrative}"


class TestDialogueIntegration:
    """Property 9: Dialogue Integration
    
    For any panel containing dialogue, the generated narrative SHALL integrate
    character dialogue naturally with action descriptions rather than separating them.
    
    **Feature: comic-audio-narrator, Property 9: Dialogue Integration**
    **Validates: Requirements 9.4**
    """

    @settings(deadline=None, max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(panel_narrative=panel_narrative_strategy(), character=character_strategy())
    def test_dialogue_integrated_with_action(self, panel_narrative, character):
        """Property: Dialogue SHALL be integrated with action descriptions.
        
        **Feature: comic-audio-narrator, Property 9: Dialogue Integration**
        **Validates: Requirements 9.4**
        """
        generator = NarrativeGenerator()
        characters = {character.id: character}
        
        # Add character to match dialogue
        if panel_narrative.dialogue:
            for line in panel_narrative.dialogue:
                characters[line.character_id] = character
        
        scenes = {}
        
        # Only test when dialogue is present
        if panel_narrative.dialogue and len(panel_narrative.dialogue) > 0:
            narrative = generator.generate_narrative(
                panel_narrative, characters, scenes
            )
            
            # Verify dialogue is present in narrative
            has_dialogue = any(
                line.text in narrative or 'says' in narrative.lower()
                for line in panel_narrative.dialogue
            )
            
            assert has_dialogue, \
                f"Dialogue should be integrated in narrative: {narrative}"

    @settings(deadline=None, max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(panel_narrative=panel_narrative_strategy(), character=character_strategy())
    def test_dialogue_attributed_to_characters(self, panel_narrative, character):
        """Property: Dialogue SHALL be attributed to characters.
        
        **Feature: comic-audio-narrator, Property 9: Dialogue Integration**
        **Validates: Requirements 9.4**
        """
        generator = NarrativeGenerator()
        characters = {character.id: character}
        
        # Add character to match dialogue
        if panel_narrative.dialogue:
            for line in panel_narrative.dialogue:
                characters[line.character_id] = character
        
        scenes = {}
        
        # Only test when dialogue is present
        if panel_narrative.dialogue and len(panel_narrative.dialogue) > 0:
            narrative = generator.generate_narrative(
                panel_narrative, characters, scenes
            )
            
            # Verify character attribution
            has_attribution = 'says' in narrative.lower() or character.name in narrative
            
            assert has_attribution, \
                f"Dialogue should be attributed to character: {narrative}"


class TestEmotionalConveyance:
    """Property 10: Emotional Conveyance
    
    For any panel expressing emotions or expressions, the generated description
    SHALL convey these through descriptive language matching professional audio
    description standards.
    
    **Feature: comic-audio-narrator, Property 10: Emotional Conveyance**
    **Validates: Requirements 9.5**
    """

    @settings(deadline=None, max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(panel_narrative=panel_narrative_strategy(), character=character_strategy())
    def test_emotions_conveyed_in_dialogue(self, panel_narrative, character):
        """Property: Emotions SHALL be conveyed in dialogue descriptions.
        
        **Feature: comic-audio-narrator, Property 10: Emotional Conveyance**
        **Validates: Requirements 9.5**
        """
        generator = NarrativeGenerator()
        characters = {character.id: character}
        
        # Add character to match dialogue
        if panel_narrative.dialogue:
            for line in panel_narrative.dialogue:
                characters[line.character_id] = character
        
        scenes = {}
        
        # Only test when dialogue with emotion is present
        dialogue_with_emotion = [
            line for line in panel_narrative.dialogue
            if line.emotion is not None
        ]
        
        if dialogue_with_emotion:
            narrative = generator.generate_narrative(
                panel_narrative, characters, scenes
            )
            
            # Verify emotion is conveyed
            has_emotion = any(
                line.emotion.lower() in narrative.lower()
                for line in dialogue_with_emotion
            )
            
            assert has_emotion, \
                f"Emotion should be conveyed in narrative: {narrative}"

    @settings(deadline=None, max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(panel_narrative=panel_narrative_strategy(), character=character_strategy())
    def test_mood_reflected_in_narrative(self, panel_narrative, character):
        """Property: Panel mood SHALL be reflected in narrative.
        
        **Feature: comic-audio-narrator, Property 10: Emotional Conveyance**
        **Validates: Requirements 9.5**
        """
        generator = NarrativeGenerator()
        characters = {character.id: character}
        scenes = {}
        
        # Only test when mood is present
        if panel_narrative.visual_analysis.mood:
            narrative = generator.generate_narrative(
                panel_narrative, characters, scenes
            )
            
            mood = panel_narrative.visual_analysis.mood.lower()
            
            # Verify mood is reflected
            assert mood in narrative.lower(), \
                f"Mood '{mood}' should be reflected in: {narrative}"
