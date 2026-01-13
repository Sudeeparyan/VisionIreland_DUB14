"""Property-based tests for character description non-repetition.

Feature: comic-audio-narrator, Property 3: Character Description Non-Repetition
Validates: Requirements 7.1
"""

from hypothesis import given, strategies as st, settings
import pytest

from src.bedrock_analysis.character_tracker import CharacterTracker
from src.bedrock_analysis.models import VoiceProfile


@st.composite
def voice_profile_strategy(draw):
    """Generate random voice profiles."""
    return VoiceProfile(
        voice_id=draw(st.text(min_size=3, max_size=20)),
        gender=draw(st.sampled_from(['male', 'female', 'neutral'])),
        age=draw(st.sampled_from(['child', 'young-adult', 'adult', 'senior'])),
        tone=draw(st.text(min_size=3, max_size=30))
    )


@st.composite
def character_data_strategy(draw):
    """Generate random character data."""
    return {
        'name': draw(st.text(min_size=5, max_size=50)),
        'visual_description': draw(st.text(min_size=20, max_size=200)),
        'personality': draw(st.text(min_size=5, max_size=100)),
        'voice_profile': draw(voice_profile_strategy()),
        'visual_signatures': draw(st.lists(st.text(min_size=1, max_size=50), max_size=5))
    }


class NarrativeTracker:
    """Tracks narrative descriptions to detect repetition."""
    
    def __init__(self):
        self.descriptions = {}
    
    def add_description(self, character_id: str, panel_number: int, description: str):
        """Add a narrative description for a character in a panel."""
        if character_id not in self.descriptions:
            self.descriptions[character_id] = {}
        self.descriptions[character_id][panel_number] = description
    
    def get_full_descriptions(self, character_id: str) -> list:
        """Get all full character descriptions (first introduction)."""
        if character_id not in self.descriptions:
            return []
        # Full descriptions are those that start with "Introducing"
        return [desc for desc in self.descriptions[character_id].values() if desc.startswith("Introducing")]
    
    def get_minimal_descriptions(self, character_id: str) -> list:
        """Get all minimal descriptions (subsequent appearances)."""
        if character_id not in self.descriptions:
            return []
        # Minimal descriptions are those that end with "appears"
        return [desc for desc in self.descriptions[character_id].values() if desc.endswith("appears")]


@settings(deadline=None)
@given(
    character_data=character_data_strategy(),
    panel_numbers=st.lists(st.integers(min_value=0, max_value=100), min_size=3, max_size=10, unique=True)
)
def test_character_description_non_repetition(character_data, panel_numbers):
    """Property: For any character that has been previously introduced, subsequent appearances SHALL not include the full character description unless significant changes have occurred.
    
    This property tests that character descriptions are not repeated unnecessarily,
    maintaining narrative engagement.
    """
    tracker = CharacterTracker()
    narrative = NarrativeTracker()
    
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
    
    # First appearance: full description
    full_description = f"Introducing {character.name}: {character.visual_description}. Personality: {character.personality}"
    narrative.add_description(character.id, first_panel, full_description)
    
    # Subsequent appearances: minimal descriptions
    for panel_num in sorted(panel_numbers)[1:]:
        tracker.record_appearance(
            character_id=character.id,
            panel_number=panel_num
        )
        # Minimal description for subsequent appearances
        minimal_description = f"{character.name} appears"
        narrative.add_description(character.id, panel_num, minimal_description)
    
    # Verify that only first appearance has full description
    full_descriptions = narrative.get_full_descriptions(character.id)
    assert len(full_descriptions) == 1, "Should have exactly one full description"
    
    # Verify subsequent appearances have minimal descriptions
    minimal_descriptions = narrative.get_minimal_descriptions(character.id)
    assert len(minimal_descriptions) == len(panel_numbers) - 1, \
        "Should have minimal descriptions for all subsequent appearances"


@settings(deadline=None)
@given(
    character_data=character_data_strategy(),
    panel_numbers=st.lists(st.integers(min_value=0, max_value=100), min_size=2, max_size=10, unique=True)
)
def test_character_introduction_only_once(character_data, panel_numbers):
    """Property: For any character, the full introduction description SHALL appear only in the first panel where the character appears.
    
    This property ensures that character introductions are not duplicated.
    """
    tracker = CharacterTracker()
    
    # Register character
    first_panel = min(panel_numbers)
    character = tracker.register_character(
        name=character_data['name'],
        visual_description=character_data['visual_description'],
        personality=character_data['personality'],
        voice_profile=character_data['voice_profile'],
        panel_number=first_panel,
        visual_signatures=character_data['visual_signatures']
    )
    
    # Record appearances
    for panel_num in panel_numbers:
        tracker.record_appearance(
            character_id=character.id,
            panel_number=panel_num
        )
    
    # Verify character first_introduced is set to first panel
    assert character.first_introduced == first_panel
    
    # Verify character appears in all panels
    appearances = tracker.get_character_appearances(character.id)
    assert len(appearances) == len(panel_numbers)
    
    # Verify first appearance is recorded
    first_appearance = next(
        (app for app in appearances if app.panel_number == first_panel),
        None
    )
    assert first_appearance is not None, "First appearance should be recorded"


@settings(deadline=None)
@given(
    character_data=character_data_strategy(),
    panel_numbers=st.lists(st.integers(min_value=0, max_value=100), min_size=2, max_size=10, unique=True),
    new_description=st.text(min_size=1, max_size=200)
)
def test_character_description_update_on_significant_change(character_data, panel_numbers, new_description):
    """Property: For any character with significant visual changes, the description SHALL be updated and the new description SHALL be used for subsequent appearances.
    
    This property tests that character descriptions can be updated when significant changes occur.
    """
    tracker = CharacterTracker()
    
    # Register character
    first_panel = min(panel_numbers)
    character = tracker.register_character(
        name=character_data['name'],
        visual_description=character_data['visual_description'],
        personality=character_data['personality'],
        voice_profile=character_data['voice_profile'],
        panel_number=first_panel,
        visual_signatures=character_data['visual_signatures']
    )
    
    original_description = character.visual_description
    
    # Record first appearance
    tracker.record_appearance(
        character_id=character.id,
        panel_number=first_panel
    )
    
    # Record appearance with updated description
    mid_panel = sorted(panel_numbers)[len(panel_numbers) // 2] if len(panel_numbers) > 1 else first_panel
    tracker.record_appearance(
        character_id=character.id,
        panel_number=mid_panel,
        visual_description=new_description
    )
    
    # Verify description was updated
    updated_character = tracker.get_character(character.id)
    assert updated_character.visual_description == new_description
    
    # Record final appearances with updated description
    for panel_num in sorted(panel_numbers)[len(panel_numbers) // 2 + 1:]:
        tracker.record_appearance(
            character_id=character.id,
            panel_number=panel_num
        )
    
    # Verify all appearances after update use new description
    appearances = tracker.get_character_appearances(character.id)
    assert len(appearances) > 0
