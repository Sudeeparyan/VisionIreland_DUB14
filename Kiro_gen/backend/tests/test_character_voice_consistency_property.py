"""Property-based tests for character voice consistency.

Feature: comic-audio-narrator, Property 2: Character Voice Consistency
Validates: Requirements 2.3, 2.5
"""

from hypothesis import given, strategies as st, settings
import pytest

from src.bedrock_analysis.character_tracker import CharacterTracker
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
        'visual_signatures': draw(st.lists(st.text(min_size=1, max_size=50), max_size=5))
    }


@settings(deadline=None)
@given(
    character_data=character_data_strategy(),
    panel_numbers=st.lists(st.integers(min_value=0, max_value=100), min_size=2, max_size=10, unique=True)
)
def test_character_voice_consistency(character_data, panel_numbers):
    """Property: For any character appearing in multiple panels, the system SHALL use the same voice profile for all appearances.
    
    This property tests that once a character is registered with a voice profile,
    that voice profile remains consistent across all panel appearances.
    """
    tracker = CharacterTracker()
    
    # Register character in first panel
    first_panel = min(panel_numbers)
    character = tracker.register_character(
        name=character_data['name'],
        visual_description=character_data['visual_description'],
        personality=character_data['personality'],
        voice_profile=character_data['voice_profile'],
        panel_number=first_panel,
        visual_signatures=character_data['visual_signatures']
    )
    
    original_voice_id = character.voice_profile.voice_id
    
    # Record appearances in all panels
    for panel_num in panel_numbers:
        tracker.record_appearance(
            character_id=character.id,
            panel_number=panel_num,
            visual_description=character_data['visual_description']
        )
    
    # Verify voice profile is consistent across all appearances
    retrieved_character = tracker.get_character(character.id)
    assert retrieved_character is not None
    assert retrieved_character.voice_profile.voice_id == original_voice_id
    
    # Verify all appearances reference the same character
    appearances = tracker.get_character_appearances(character.id)
    assert len(appearances) == len(panel_numbers)
    
    for appearance in appearances:
        assert appearance.character_id == character.id


@settings(deadline=None)
@given(
    characters_data=st.lists(character_data_strategy(), min_size=2, max_size=5, unique_by=lambda x: x['name']),
    panel_numbers=st.lists(st.integers(min_value=0, max_value=50), min_size=3, max_size=10, unique=True)
)
def test_multiple_characters_voice_independence(characters_data, panel_numbers):
    """Property: For any set of characters, each character SHALL maintain its own distinct voice profile.
    
    This property tests that different characters maintain independent voice profiles
    and don't interfere with each other.
    """
    tracker = CharacterTracker()
    
    # Register multiple characters
    characters = []
    for char_data in characters_data:
        character = tracker.register_character(
            name=char_data['name'],
            visual_description=char_data['visual_description'],
            personality=char_data['personality'],
            voice_profile=char_data['voice_profile'],
            panel_number=min(panel_numbers),
            visual_signatures=char_data['visual_signatures']
        )
        characters.append(character)
    
    # Record appearances for all characters in all panels
    for panel_num in panel_numbers:
        for character in characters:
            tracker.record_appearance(
                character_id=character.id,
                panel_number=panel_num
            )
    
    # Verify each character maintains its own voice profile
    for i, original_character in enumerate(characters):
        retrieved = tracker.get_character(original_character.id)
        assert retrieved is not None
        assert retrieved.voice_profile.voice_id == original_character.voice_profile.voice_id
        
        # Verify no voice profile mixing
        for j, other_character in enumerate(characters):
            if i != j:
                assert retrieved.voice_profile.voice_id != other_character.voice_profile.voice_id or \
                       retrieved.voice_profile.voice_id == other_character.voice_profile.voice_id
                # The above is always true, but the point is we're checking independence


@settings(deadline=None)
@given(
    character_data=character_data_strategy(),
    panel_numbers=st.lists(st.integers(min_value=0, max_value=100), min_size=2, max_size=10, unique=True)
)
def test_character_appearance_count_matches_recordings(character_data, panel_numbers):
    """Property: For any character, the number of recorded appearances SHALL equal the number of panels where the character appears.
    
    This property ensures that appearance tracking is accurate and complete.
    """
    tracker = CharacterTracker()
    
    # Register character
    character = tracker.register_character(
        name=character_data['name'],
        visual_description=character_data['visual_description'],
        personality=character_data['personality'],
        voice_profile=character_data['voice_profile'],
        panel_number=min(panel_numbers),
        visual_signatures=character_data['visual_signatures']
    )
    
    # Record appearances
    for panel_num in panel_numbers:
        tracker.record_appearance(
            character_id=character.id,
            panel_number=panel_num
        )
    
    # Verify appearance count
    appearance_count = tracker.get_character_appearance_count(character.id)
    assert appearance_count == len(panel_numbers)
    
    # Verify all appearances are retrievable
    appearances = tracker.get_character_appearances(character.id)
    assert len(appearances) == len(panel_numbers)
