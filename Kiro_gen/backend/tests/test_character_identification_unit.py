"""Unit tests for character identification and tracking.

Tests the character identification workflow including:
- Character extraction from visual analysis
- Voice profile assignment
- Character registration and tracking
- Character appearance recording
"""

import pytest
from src.bedrock_analysis.character_identifier import CharacterIdentifier
from src.bedrock_analysis.character_tracker import CharacterTracker
from src.bedrock_analysis.models import VoiceProfile


class TestCharacterIdentifier:
    """Tests for CharacterIdentifier class."""

    def test_identify_characters_from_string_descriptions(self):
        """Test identifying characters from simple string descriptions."""
        identifier = CharacterIdentifier()
        
        visual_analysis = {
            'characters': [
                'A tall man with red cape and blue suit',
                'A young woman with black hair and green eyes'
            ]
        }
        
        characters = identifier.identify_characters_from_analysis(visual_analysis, 1)
        
        assert len(characters) == 2
        assert characters[0][0] == 'A'  # First character name extracted
        assert characters[1][0] == 'A'  # Second character name extracted

    def test_identify_characters_from_dict_format(self):
        """Test identifying characters from structured dict format."""
        identifier = CharacterIdentifier()
        
        visual_analysis = {
            'characters': [
                {
                    'name': 'Superman',
                    'visual_description': 'Tall man with red cape and blue suit',
                    'personality': 'heroic',
                    'visual_signatures': ['red cape', 'blue suit']
                },
                {
                    'name': 'Wonder Woman',
                    'visual_description': 'Woman with golden lasso and tiara',
                    'personality': 'heroic',
                    'visual_signatures': ['golden lasso', 'tiara']
                }
            ]
        }
        
        characters = identifier.identify_characters_from_analysis(visual_analysis, 1)
        
        assert len(characters) == 2
        assert characters[0][0] == 'Superman'
        assert characters[1][0] == 'Wonder Woman'
        assert characters[0][1].personality == 'heroic'
        assert characters[1][1].personality == 'heroic'

    def test_character_voice_profile_assignment_heroic(self):
        """Test voice profile assignment for heroic characters."""
        identifier = CharacterIdentifier()
        
        visual_analysis = {
            'characters': [
                {
                    'name': 'Hero',
                    'visual_description': 'Brave man with strong build',
                    'personality': 'heroic'
                }
            ]
        }
        
        characters = identifier.identify_characters_from_analysis(visual_analysis, 1)
        
        assert len(characters) == 1
        character = characters[0][1]
        assert character.voice_profile.tone == 'heroic'
        assert character.voice_profile.gender == 'male'

    def test_character_voice_profile_assignment_comedic(self):
        """Test voice profile assignment for comedic characters."""
        identifier = CharacterIdentifier()
        
        visual_analysis = {
            'characters': [
                {
                    'name': 'Jester',
                    'visual_description': 'Funny woman with silly outfit',
                    'personality': 'comedic'
                }
            ]
        }
        
        characters = identifier.identify_characters_from_analysis(visual_analysis, 1)
        
        assert len(characters) == 1
        character = characters[0][1]
        assert character.voice_profile.tone == 'comedic'
        assert character.voice_profile.gender == 'female'

    def test_character_voice_profile_assignment_child(self):
        """Test voice profile assignment for child characters."""
        identifier = CharacterIdentifier()
        
        visual_analysis = {
            'characters': [
                {
                    'name': 'Child',
                    'visual_description': 'Young boy with small stature',
                    'personality': 'innocent'
                }
            ]
        }
        
        characters = identifier.identify_characters_from_analysis(visual_analysis, 1)
        
        assert len(characters) == 1
        character = characters[0][1]
        assert character.voice_profile.age == 'child'

    def test_character_voice_profile_assignment_elderly(self):
        """Test voice profile assignment for elderly characters."""
        identifier = CharacterIdentifier()
        
        visual_analysis = {
            'characters': [
                {
                    'name': 'Elder',
                    'visual_description': 'Old man with grey beard and wrinkles',
                    'personality': 'wise'
                }
            ]
        }
        
        characters = identifier.identify_characters_from_analysis(visual_analysis, 1)
        
        assert len(characters) == 1
        character = characters[0][1]
        assert character.voice_profile.age == 'senior'

    def test_visual_signatures_extraction(self):
        """Test extraction of distinctive visual features."""
        identifier = CharacterIdentifier()
        
        visual_analysis = {
            'characters': [
                {
                    'name': 'Scarred Warrior',
                    'visual_description': 'Man with red scar on face and black cape',
                    'personality': 'mysterious'
                }
            ]
        }
        
        characters = identifier.identify_characters_from_analysis(visual_analysis, 1)
        
        assert len(characters) == 1
        character = characters[0][1]
        # Should extract color and distinctive features
        assert len(character.visual_signatures) > 0

    def test_character_counter_increments(self):
        """Test that character IDs increment properly."""
        identifier = CharacterIdentifier()
        
        visual_analysis = {
            'characters': [
                {'name': 'Char1', 'visual_description': 'First character'},
                {'name': 'Char2', 'visual_description': 'Second character'},
                {'name': 'Char3', 'visual_description': 'Third character'}
            ]
        }
        
        characters = identifier.identify_characters_from_analysis(visual_analysis, 1)
        
        assert len(characters) == 3
        assert characters[0][1].id == 'char_0'
        assert characters[1][1].id == 'char_1'
        assert characters[2][1].id == 'char_2'

    def test_character_first_introduced_panel_number(self):
        """Test that first_introduced is set correctly."""
        identifier = CharacterIdentifier()
        
        visual_analysis = {
            'characters': [
                {'name': 'Character', 'visual_description': 'A character'}
            ]
        }
        
        characters = identifier.identify_characters_from_analysis(visual_analysis, 5)
        
        assert len(characters) == 1
        assert characters[0][1].first_introduced == 5

    def test_reset_clears_counter(self):
        """Test that reset clears the character counter."""
        identifier = CharacterIdentifier()
        
        # Create some characters
        visual_analysis = {
            'characters': [
                {'name': 'Char1', 'visual_description': 'First'},
                {'name': 'Char2', 'visual_description': 'Second'}
            ]
        }
        
        characters1 = identifier.identify_characters_from_analysis(visual_analysis, 1)
        assert characters1[0][1].id == 'char_0'
        assert characters1[1][1].id == 'char_1'
        
        # Reset
        identifier.reset()
        
        # Create new characters - should start from 0 again
        characters2 = identifier.identify_characters_from_analysis(visual_analysis, 1)
        assert characters2[0][1].id == 'char_0'
        assert characters2[1][1].id == 'char_1'


class TestCharacterTracking:
    """Tests for character tracking across panels."""

    def test_register_and_retrieve_character(self):
        """Test registering and retrieving a character."""
        tracker = CharacterTracker()
        
        voice_profile = VoiceProfile(
            voice_id='Joanna',
            gender='female',
            age='adult',
            tone='heroic'
        )
        
        character = tracker.register_character(
            name='Wonder Woman',
            visual_description='Woman with golden lasso',
            personality='heroic',
            voice_profile=voice_profile,
            panel_number=1
        )
        
        retrieved = tracker.get_character(character.id)
        assert retrieved is not None
        assert retrieved.name == 'Wonder Woman'
        assert retrieved.voice_profile.voice_id == 'Joanna'

    def test_get_character_by_name(self):
        """Test retrieving character by name."""
        tracker = CharacterTracker()
        
        voice_profile = VoiceProfile(
            voice_id='Matthew',
            gender='male',
            age='adult',
            tone='mysterious'
        )
        
        character = tracker.register_character(
            name='Batman',
            visual_description='Man in dark suit',
            personality='mysterious',
            voice_profile=voice_profile,
            panel_number=1
        )
        
        retrieved = tracker.get_character_by_name('Batman')
        assert retrieved is not None
        assert retrieved.id == character.id

    def test_record_character_appearance(self):
        """Test recording character appearance in panels."""
        tracker = CharacterTracker()
        
        voice_profile = VoiceProfile(
            voice_id='Joanna',
            gender='female',
            age='adult',
            tone='heroic'
        )
        
        character = tracker.register_character(
            name='Superhero',
            visual_description='Hero in cape',
            personality='heroic',
            voice_profile=voice_profile,
            panel_number=1
        )
        
        # Record appearances in multiple panels
        tracker.record_appearance(character.id, 1)
        tracker.record_appearance(character.id, 3)
        tracker.record_appearance(character.id, 5)
        
        appearances = tracker.get_character_appearances(character.id)
        assert len(appearances) == 3
        assert appearances[0].panel_number == 1
        assert appearances[1].panel_number == 3
        assert appearances[2].panel_number == 5

    def test_character_appearance_count(self):
        """Test counting character appearances."""
        tracker = CharacterTracker()
        
        voice_profile = VoiceProfile(
            voice_id='Joey',
            gender='male',
            age='adult',
            tone='comedic'
        )
        
        character = tracker.register_character(
            name='Comedian',
            visual_description='Funny character',
            personality='comedic',
            voice_profile=voice_profile,
            panel_number=1
        )
        
        for panel in range(1, 6):
            tracker.record_appearance(character.id, panel)
        
        count = tracker.get_character_appearance_count(character.id)
        assert count == 5

    def test_get_characters_in_panel(self):
        """Test retrieving all characters in a specific panel."""
        tracker = CharacterTracker()
        
        voice_profile1 = VoiceProfile(
            voice_id='Joanna',
            gender='female',
            age='adult',
            tone='heroic'
        )
        
        voice_profile2 = VoiceProfile(
            voice_id='Matthew',
            gender='male',
            age='adult',
            tone='mysterious'
        )
        
        char1 = tracker.register_character(
            name='Hero1',
            visual_description='First hero',
            personality='heroic',
            voice_profile=voice_profile1,
            panel_number=1
        )
        
        char2 = tracker.register_character(
            name='Hero2',
            visual_description='Second hero',
            personality='mysterious',
            voice_profile=voice_profile2,
            panel_number=1
        )
        
        # Both appear in panel 1
        tracker.record_appearance(char1.id, 1)
        tracker.record_appearance(char2.id, 1)
        
        # Only char1 appears in panel 2
        tracker.record_appearance(char1.id, 2)
        
        panel1_chars = tracker.get_characters_in_panel(1)
        assert len(panel1_chars) == 2
        
        panel2_chars = tracker.get_characters_in_panel(2)
        assert len(panel2_chars) == 1
        assert panel2_chars[0].name == 'Hero1'

    def test_is_character_introduced(self):
        """Test checking if character has been introduced."""
        tracker = CharacterTracker()
        
        voice_profile = VoiceProfile(
            voice_id='Joanna',
            gender='female',
            age='adult',
            tone='heroic'
        )
        
        character = tracker.register_character(
            name='Character',
            visual_description='A character',
            personality='heroic',
            voice_profile=voice_profile,
            panel_number=5
        )
        
        assert not tracker.is_character_introduced(character.id, 4)
        assert tracker.is_character_introduced(character.id, 5)
        assert tracker.is_character_introduced(character.id, 10)

    def test_get_new_characters_in_panel(self):
        """Test retrieving characters first appearing in a panel."""
        tracker = CharacterTracker()
        
        voice_profile1 = VoiceProfile(
            voice_id='Joanna',
            gender='female',
            age='adult',
            tone='heroic'
        )
        
        voice_profile2 = VoiceProfile(
            voice_id='Matthew',
            gender='male',
            age='adult',
            tone='mysterious'
        )
        
        char1 = tracker.register_character(
            name='FirstChar',
            visual_description='First character',
            personality='heroic',
            voice_profile=voice_profile1,
            panel_number=1
        )
        
        char2 = tracker.register_character(
            name='SecondChar',
            visual_description='Second character',
            personality='mysterious',
            voice_profile=voice_profile2,
            panel_number=3
        )
        
        new_in_panel1 = tracker.get_new_characters_in_panel(1)
        assert len(new_in_panel1) == 1
        assert new_in_panel1[0].name == 'FirstChar'
        
        new_in_panel3 = tracker.get_new_characters_in_panel(3)
        assert len(new_in_panel3) == 1
        assert new_in_panel3[0].name == 'SecondChar'

    def test_update_character_voice(self):
        """Test updating character voice profile."""
        tracker = CharacterTracker()
        
        voice_profile1 = VoiceProfile(
            voice_id='Joanna',
            gender='female',
            age='adult',
            tone='heroic'
        )
        
        character = tracker.register_character(
            name='Character',
            visual_description='A character',
            personality='heroic',
            voice_profile=voice_profile1,
            panel_number=1
        )
        
        # Update voice profile
        voice_profile2 = VoiceProfile(
            voice_id='Matthew',
            gender='male',
            age='adult',
            tone='mysterious'
        )
        
        success = tracker.update_character_voice(character.id, voice_profile2)
        assert success
        
        updated = tracker.get_character(character.id)
        assert updated.voice_profile.voice_id == 'Matthew'

    def test_add_visual_signature(self):
        """Test adding visual signatures to character."""
        tracker = CharacterTracker()
        
        voice_profile = VoiceProfile(
            voice_id='Joanna',
            gender='female',
            age='adult',
            tone='heroic'
        )
        
        character = tracker.register_character(
            name='Character',
            visual_description='A character',
            personality='heroic',
            voice_profile=voice_profile,
            panel_number=1,
            visual_signatures=['red cape']
        )
        
        assert len(character.visual_signatures) == 1
        
        success = tracker.add_visual_signature(character.id, 'blue suit')
        assert success
        
        updated = tracker.get_character(character.id)
        assert len(updated.visual_signatures) == 2
        assert 'blue suit' in updated.visual_signatures

    def test_get_character_summary(self):
        """Test getting character summary."""
        tracker = CharacterTracker()
        
        voice_profile = VoiceProfile(
            voice_id='Joanna',
            gender='female',
            age='adult',
            tone='heroic'
        )
        
        character = tracker.register_character(
            name='Hero',
            visual_description='A heroic character',
            personality='heroic',
            voice_profile=voice_profile,
            panel_number=1,
            visual_signatures=['cape', 'mask']
        )
        
        # Record appearances
        for panel in range(1, 4):
            tracker.record_appearance(character.id, panel)
        
        summary = tracker.get_character_summary(character.id)
        assert summary is not None
        assert summary['name'] == 'Hero'
        assert summary['appearance_count'] == 3
        assert summary['first_introduced'] == 1
        assert len(summary['visual_signatures']) == 2

    def test_tracker_reset(self):
        """Test resetting tracker for new comic."""
        tracker = CharacterTracker()
        
        voice_profile = VoiceProfile(
            voice_id='Joanna',
            gender='female',
            age='adult',
            tone='heroic'
        )
        
        character = tracker.register_character(
            name='Character',
            visual_description='A character',
            personality='heroic',
            voice_profile=voice_profile,
            panel_number=1
        )
        
        assert len(tracker.get_all_characters()) == 1
        
        tracker.reset()
        
        assert len(tracker.get_all_characters()) == 0
        assert tracker.character_counter == 0
