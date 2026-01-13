"""Property-based tests for story continuity preservation.

Feature: comic-audio-narrator, Property 5: Story Continuity Preservation
Validates: Requirements 7.3
"""

from hypothesis import given, strategies as st, settings
import pytest

from src.bedrock_analysis.character_tracker import CharacterTracker
from src.bedrock_analysis.scene_tracker import SceneTracker
from src.bedrock_analysis.models import VoiceProfile


@st.composite
def voice_profile_strategy(draw):
    """Generate random voice profiles."""
    return VoiceProfile(
        voice_id=draw(st.text(min_size=1, max_size=20)),
        gender=draw(st.sampled_from(['male', 'female', 'neutral'])),
        age=draw(st.sampled_from(['child', 'young-adult', 'adult', 'senior'])),
        tone=draw(st.text(min_size=1, max_size=30))
    )


@st.composite
def character_data_strategy(draw):
    """Generate random character data."""
    return {
        'name': draw(st.text(min_size=1, max_size=50)),
        'visual_description': draw(st.text(min_size=1, max_size=200)),
        'personality': draw(st.text(min_size=1, max_size=100)),
        'voice_profile': draw(voice_profile_strategy()),
    }


@st.composite
def scene_data_strategy(draw):
    """Generate random scene data."""
    return {
        'location': draw(st.text(min_size=1, max_size=50)),
        'visual_description': draw(st.text(min_size=1, max_size=200)),
        'atmosphere': draw(st.one_of(st.none(), st.text(min_size=1, max_size=100))),
    }


class StoryState:
    """Tracks story state for continuity validation."""
    
    def __init__(self):
        self.character_states = {}
        self.scene_states = {}
        self.panel_sequence = []
    
    def add_panel(self, panel_num: int, characters: list, scene_id: str):
        """Record panel state."""
        self.panel_sequence.append({
            'panel': panel_num,
            'characters': characters,
            'scene': scene_id
        })
        
        # Update character states
        for char_id in characters:
            self.character_states[char_id] = panel_num
        
        # Update scene state
        self.scene_states[scene_id] = panel_num
    
    def get_character_state(self, char_id: str) -> int:
        """Get last panel where character appeared."""
        return self.character_states.get(char_id, -1)
    
    def get_scene_state(self, scene_id: str) -> int:
        """Get last panel where scene appeared."""
        return self.scene_states.get(scene_id, -1)


@settings(deadline=None)
@given(
    characters_data=st.lists(character_data_strategy(), min_size=2, max_size=5, unique_by=lambda x: x['name']),
    scenes_data=st.lists(scene_data_strategy(), min_size=2, max_size=3, unique_by=lambda x: x['location']),
    panel_count=st.integers(min_value=5, max_value=20)
)
def test_story_continuity_preservation(characters_data, scenes_data, panel_count):
    """Property: For any sequence of panels, the generated narrative SHALL maintain character state, scene context, and story flow across all panels.
    
    This property tests that story continuity is preserved throughout the comic.
    """
    char_tracker = CharacterTracker()
    scene_tracker = SceneTracker()
    story_state = StoryState()
    
    # Register all characters
    characters = []
    for char_data in characters_data:
        character = char_tracker.register_character(
            name=char_data['name'],
            visual_description=char_data['visual_description'],
            personality=char_data['personality'],
            voice_profile=char_data['voice_profile'],
            panel_number=0
        )
        characters.append(character)
    
    # Register all scenes
    scenes = []
    for scene_data in scenes_data:
        scene = scene_tracker.register_scene(
            location=scene_data['location'],
            visual_description=scene_data['visual_description'],
            panel_number=0,
            atmosphere=scene_data['atmosphere']
        )
        scenes.append(scene)
    
    # Simulate panel sequence
    for panel_num in range(panel_count):
        # Select characters for this panel
        char_indices = list(range(len(characters)))
        if char_indices:
            selected_chars = [characters[i] for i in char_indices[:max(1, len(char_indices) // 2)]]
            for char in selected_chars:
                char_tracker.record_appearance(
                    character_id=char.id,
                    panel_number=panel_num
                )
        
        # Select scene for this panel
        scene_idx = panel_num % len(scenes)
        scene = scenes[scene_idx]
        scene_tracker.set_scene_for_panel(scene.id, panel_num)
        
        # Record state
        story_state.add_panel(
            panel_num,
            [char.id for char in selected_chars],
            scene.id
        )
    
    # Verify continuity: all characters should have been seen
    for character in characters:
        last_seen = story_state.get_character_state(character.id)
        assert last_seen >= 0, f"Character {character.name} should appear at least once"
    
    # Verify continuity: all scenes should have been seen
    for scene in scenes:
        last_seen = story_state.get_scene_state(scene.id)
        assert last_seen >= 0, f"Scene {scene.location} should appear at least once"
    
    # Verify panel sequence is maintained
    assert len(story_state.panel_sequence) == panel_count


@settings(deadline=None)
@given(
    character_data=character_data_strategy(),
    scene_data=scene_data_strategy(),
    panel_numbers=st.lists(st.integers(min_value=0, max_value=100), min_size=3, max_size=10, unique=True)
)
def test_character_state_consistency(character_data, scene_data, panel_numbers):
    """Property: For any character appearing across panels, the character's state SHALL remain consistent.
    
    This property ensures that character state doesn't change unexpectedly.
    """
    char_tracker = CharacterTracker()
    
    # Register character
    character = char_tracker.register_character(
        name=character_data['name'],
        visual_description=character_data['visual_description'],
        personality=character_data['personality'],
        voice_profile=character_data['voice_profile'],
        panel_number=min(panel_numbers)
    )
    
    original_id = character.id
    original_voice_id = character.voice_profile.voice_id
    
    # Record appearances
    for panel_num in panel_numbers:
        char_tracker.record_appearance(
            character_id=character.id,
            panel_number=panel_num
        )
    
    # Verify character state consistency
    retrieved = char_tracker.get_character(original_id)
    assert retrieved is not None
    assert retrieved.id == original_id
    assert retrieved.voice_profile.voice_id == original_voice_id
    assert retrieved.last_seen == max(panel_numbers)


@settings(deadline=None)
@given(
    scene_data=scene_data_strategy(),
    panel_numbers=st.lists(st.integers(min_value=0, max_value=100), min_size=3, max_size=10, unique=True)
)
def test_scene_context_preservation(scene_data, panel_numbers):
    """Property: For any scene appearing across panels, the scene's context SHALL be preserved.
    
    This property ensures that scene context remains consistent throughout.
    """
    scene_tracker = SceneTracker()
    
    # Register scene
    scene = scene_tracker.register_scene(
        location=scene_data['location'],
        visual_description=scene_data['visual_description'],
        panel_number=min(panel_numbers),
        atmosphere=scene_data['atmosphere']
    )
    
    original_id = scene.id
    original_location = scene.location
    
    # Set scene for all panels
    for panel_num in panel_numbers:
        scene_tracker.set_scene_for_panel(scene.id, panel_num)
    
    # Verify scene context preservation
    retrieved = scene_tracker.get_scene(original_id)
    assert retrieved is not None
    assert retrieved.id == original_id
    assert retrieved.location == original_location
    assert retrieved.last_seen == max(panel_numbers)
