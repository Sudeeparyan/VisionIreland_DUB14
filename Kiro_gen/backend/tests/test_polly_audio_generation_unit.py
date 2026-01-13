"""Unit tests for Polly audio generation.

Tests core functionality of audio generation, voice profile assignment,
and audio composition.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from io import BytesIO

from src.polly_generation.generator import PollyAudioGenerator
from src.polly_generation.models import (
    AudioGenerationRequest,
    AudioSegment,
    AudioMetadata,
)
from src.polly_generation.voice_manager import VoiceProfileManager
from src.bedrock_analysis.models import Character, VoiceProfile


class TestPollyAudioGenerator:
    """Test suite for PollyAudioGenerator"""

    @pytest.fixture
    def mock_polly_client(self):
        """Create a mock Polly client"""
        client = Mock()
        # Mock successful audio generation
        mock_response = {
            "AudioStream": BytesIO(b"mock_audio_data_12345"),
            "ContentType": "audio/mpeg",
        }
        client.synthesize_speech.return_value = mock_response
        return client

    @pytest.fixture
    def generator(self, mock_polly_client):
        """Create a PollyAudioGenerator with mocked client"""
        with patch("src.polly_generation.generator.aws_clients") as mock_aws:
            mock_aws.polly = mock_polly_client
            gen = PollyAudioGenerator(use_neural=True)
            gen.polly_client = mock_polly_client
            return gen

    def test_generator_initialization_neural(self):
        """Test generator initializes with neural voices"""
        with patch("src.polly_generation.generator.aws_clients"):
            gen = PollyAudioGenerator(use_neural=True)
            assert gen.use_neural is True
            assert gen.voice_map == gen.NEURAL_VOICES

    def test_generator_initialization_standard(self):
        """Test generator initializes with standard voices"""
        with patch("src.polly_generation.generator.aws_clients"):
            gen = PollyAudioGenerator(use_neural=False)
            assert gen.use_neural is False
            assert gen.voice_map == gen.STANDARD_VOICES

    def test_generate_audio_success(self, generator, mock_polly_client):
        """Test successful audio generation"""
        request = AudioGenerationRequest(
            text="Hello, this is a test.",
            voice_id="Joanna",
            engine="neural",
            output_format="mp3",
            panel_id="panel_1",
        )

        segment = generator.generate_audio(request)

        assert segment.panel_id == "panel_1"
        assert segment.audio_data == b"mock_audio_data_12345"
        assert segment.voice_id == "Joanna"
        assert segment.engine == "neural"
        assert segment.duration > 0
        mock_polly_client.synthesize_speech.assert_called_once()

    def test_generate_audio_empty_text_raises_error(self, generator):
        """Test that empty text raises ValueError"""
        request = AudioGenerationRequest(
            text="",
            voice_id="Joanna",
            engine="neural",
            output_format="mp3",
        )

        with pytest.raises(ValueError, match="cannot be empty"):
            generator.generate_audio(request)

    def test_generate_audio_whitespace_text_raises_error(self, generator):
        """Test that whitespace-only text raises ValueError"""
        request = AudioGenerationRequest(
            text="   \n\t  ",
            voice_id="Joanna",
            engine="neural",
            output_format="mp3",
        )

        with pytest.raises(ValueError, match="cannot be empty"):
            generator.generate_audio(request)

    def test_generate_audio_invalid_format_raises_error(self, generator):
        """Test that invalid output format raises ValueError"""
        request = AudioGenerationRequest(
            text="Hello",
            voice_id="Joanna",
            engine="neural",
            output_format="wav",  # Invalid format
        )

        with pytest.raises(ValueError, match="Unsupported output format"):
            generator.generate_audio(request)

    def test_generate_audio_polly_error_handling(self, generator, mock_polly_client):
        """Test error handling when Polly API fails"""
        mock_polly_client.synthesize_speech.side_effect = Exception("Polly API error")

        request = AudioGenerationRequest(
            text="Hello",
            voice_id="Joanna",
            engine="neural",
            output_format="mp3",
        )

        with pytest.raises(RuntimeError, match="Polly audio generation failed"):
            generator.generate_audio(request)

    def test_duration_estimation(self, generator):
        """Test audio duration estimation"""
        # ~150 words per minute = 2.5 words per second
        text = " ".join(["word"] * 10)  # 10 words
        duration = generator._estimate_duration(text)
        assert duration == pytest.approx(4.0, rel=0.1)  # 10 / 2.5 = 4 seconds

    def test_duration_estimation_minimum(self, generator):
        """Test that duration has minimum of 0.5 seconds"""
        text = "a"  # 1 word
        duration = generator._estimate_duration(text)
        assert duration >= 0.5

    def test_get_voice_for_profile_male_adult(self, generator):
        """Test voice selection for male adult profile"""
        voice_id = generator.get_voice_for_profile("male", "adult")
        assert voice_id in generator.voice_map.values()

    def test_get_voice_for_profile_female_senior(self, generator):
        """Test voice selection for female senior profile"""
        voice_id = generator.get_voice_for_profile("female", "senior")
        assert voice_id in generator.voice_map.values()

    def test_get_voice_for_profile_neutral_defaults_to_male(self, generator):
        """Test that neutral gender defaults to male"""
        voice_id = generator.get_voice_for_profile("neutral", "adult")
        assert voice_id in generator.voice_map.values()

    def test_get_voice_for_profile_heroic_tone(self, generator):
        """Test voice selection with heroic tone"""
        voice_id = generator.get_voice_for_profile("male", "adult", tone="heroic")
        assert voice_id in generator.voice_map.values()

    def test_get_voice_for_profile_child_age(self, generator):
        """Test voice selection for child age"""
        voice_id = generator.get_voice_for_profile("female", "child")
        assert voice_id in generator.voice_map.values()

    def test_compose_audio_single_segment(self, generator, mock_polly_client):
        """Test composing audio from a single segment"""
        request = AudioGenerationRequest(
            text="Hello",
            voice_id="Joanna",
            engine="neural",
            output_format="mp3",
            panel_id="panel_1",
        )
        segment = generator.generate_audio(request)

        metadata = AudioMetadata(
            title="Test Comic",
            characters=["Character 1"],
            scenes=["Scene 1"],
        )

        composite = generator.compose_audio(
            segments=[segment], metadata=metadata, output_format="mp3"
        )

        assert len(composite.segments) == 1
        assert composite.total_duration == segment.duration
        assert composite.metadata.title == "Test Comic"

    def test_compose_audio_multiple_segments(self, generator, mock_polly_client):
        """Test composing audio from multiple segments"""
        segments = []
        for i in range(3):
            request = AudioGenerationRequest(
                text=f"Panel {i} text",
                voice_id="Joanna",
                engine="neural",
                output_format="mp3",
                panel_id=f"panel_{i}",
            )
            segment = generator.generate_audio(request)
            segments.append(segment)

        metadata = AudioMetadata(
            title="Test Comic",
            characters=["Character 1"],
            scenes=["Scene 1"],
        )

        composite = generator.compose_audio(
            segments=segments, metadata=metadata, output_format="mp3"
        )

        assert len(composite.segments) == 3
        assert composite.total_duration == pytest.approx(
            sum(s.duration for s in segments), rel=0.01
        )

    def test_compose_audio_no_segments_raises_error(self, generator):
        """Test that composing with no segments raises error"""
        with pytest.raises(ValueError, match="No audio segments"):
            generator.compose_audio(segments=[], metadata=None)

    def test_compose_audio_uses_stored_segments(self, generator, mock_polly_client):
        """Test that compose_audio uses stored segments if none provided"""
        request = AudioGenerationRequest(
            text="Hello",
            voice_id="Joanna",
            engine="neural",
            output_format="mp3",
            panel_id="panel_1",
        )
        generator.generate_audio(request)

        metadata = AudioMetadata(title="Test Comic")
        composite = generator.compose_audio(metadata=metadata)

        assert len(composite.segments) == 1

    def test_reset_segments(self, generator, mock_polly_client):
        """Test resetting stored segments"""
        request = AudioGenerationRequest(
            text="Hello",
            voice_id="Joanna",
            engine="neural",
            output_format="mp3",
            panel_id="panel_1",
        )
        generator.generate_audio(request)
        assert len(generator.segments) == 1

        generator.reset_segments()
        assert len(generator.segments) == 0

    def test_get_segments(self, generator, mock_polly_client):
        """Test retrieving stored segments"""
        request = AudioGenerationRequest(
            text="Hello",
            voice_id="Joanna",
            engine="neural",
            output_format="mp3",
            panel_id="panel_1",
        )
        generator.generate_audio(request)

        segments = generator.get_segments()
        assert len(segments) == 1
        assert segments[0].panel_id == "panel_1"

    def test_set_engine_neural_to_standard(self, generator):
        """Test switching from neural to standard engine"""
        assert generator.use_neural is True
        generator.set_engine(False)
        assert generator.use_neural is False
        assert generator.voice_map == generator.STANDARD_VOICES

    def test_set_engine_standard_to_neural(self, generator):
        """Test switching from standard to neural engine"""
        generator.set_engine(False)
        assert generator.use_neural is False
        generator.set_engine(True)
        assert generator.use_neural is True
        assert generator.voice_map == generator.NEURAL_VOICES


class TestVoiceProfileManager:
    """Test suite for VoiceProfileManager"""

    @pytest.fixture
    def manager(self):
        """Create a VoiceProfileManager instance"""
        return VoiceProfileManager()

    @pytest.fixture
    def sample_character(self):
        """Create a sample character"""
        voice_profile = VoiceProfile(
            voice_id="Joanna",
            gender="female",
            age="adult",
            tone="heroic",
        )
        return Character(
            id="char_1",
            name="Hero",
            visual_description="A brave hero",
            personality="Courageous",
            voice_profile=voice_profile,
            first_introduced=0,
            last_seen=10,
        )

    def test_assign_voice_profile(self, manager, sample_character):
        """Test assigning a voice profile to a character"""
        profile = manager.assign_voice_profile(sample_character, "Joanna")
        assert profile.voice_id == "Joanna"
        assert manager.character_voices["char_1"] == "Joanna"

    def test_get_voice_for_character(self, manager, sample_character):
        """Test retrieving voice for a character"""
        manager.assign_voice_profile(sample_character, "Joanna")
        voice_id = manager.get_voice_for_character("char_1")
        assert voice_id == "Joanna"

    def test_get_voice_for_unknown_character(self, manager):
        """Test retrieving voice for unknown character returns None"""
        voice_id = manager.get_voice_for_character("unknown")
        assert voice_id is None

    def test_get_voice_profile(self, manager, sample_character):
        """Test retrieving voice profile for a character"""
        manager.assign_voice_profile(sample_character, "Joanna")
        profile = manager.get_voice_profile("char_1")
        assert profile.voice_id == "Joanna"
        assert profile.gender == "female"

    def test_ensure_voice_consistency_first_appearance(self, manager, sample_character):
        """Test voice consistency check for first appearance"""
        is_consistent = manager.ensure_voice_consistency(sample_character, "Joanna")
        assert is_consistent is True
        assert manager.character_voices["char_1"] == "Joanna"

    def test_ensure_voice_consistency_matching(self, manager, sample_character):
        """Test voice consistency check with matching voice"""
        manager.assign_voice_profile(sample_character, "Joanna")
        is_consistent = manager.ensure_voice_consistency(sample_character, "Joanna")
        assert is_consistent is True

    def test_ensure_voice_consistency_mismatch(self, manager, sample_character):
        """Test voice consistency check with mismatched voice"""
        manager.assign_voice_profile(sample_character, "Joanna")
        is_consistent = manager.ensure_voice_consistency(sample_character, "Matthew")
        assert is_consistent is False

    def test_get_all_character_voices(self, manager, sample_character):
        """Test retrieving all character voice assignments"""
        manager.assign_voice_profile(sample_character, "Joanna")
        voices = manager.get_all_character_voices()
        assert voices["char_1"] == "Joanna"

    def test_reset(self, manager, sample_character):
        """Test resetting voice assignments"""
        manager.assign_voice_profile(sample_character, "Joanna")
        assert len(manager.character_voices) == 1
        manager.reset()
        assert len(manager.character_voices) == 0

    def test_validate_voice_id_valid(self, manager):
        """Test validating a valid voice ID"""
        assert manager.validate_voice_id("Joanna") is True
        assert manager.validate_voice_id("Matthew") is True

    def test_validate_voice_id_invalid(self, manager):
        """Test validating an invalid voice ID"""
        assert manager.validate_voice_id("InvalidVoice") is False
        assert manager.validate_voice_id("") is False
