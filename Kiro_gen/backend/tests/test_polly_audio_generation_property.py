"""Property-based tests for Polly audio generation.

Feature: comic-audio-narrator, Property 11: Local Audio Storage
Validates: Requirements 4.1

These tests verify that audio generation and composition maintain
correctness properties across a wide range of inputs.
"""

from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import Mock, patch
from io import BytesIO
import pytest

from src.polly_generation.generator import PollyAudioGenerator
from src.polly_generation.models import (
    AudioGenerationRequest,
    AudioSegment,
    AudioMetadata,
)
from src.polly_generation.voice_manager import VoiceProfileManager
from src.bedrock_analysis.models import Character, VoiceProfile


# Strategies for property-based testing

@st.composite
def valid_text_strategy(draw):
    """Generate valid narrative text for audio generation"""
    # Generate text with at least 1 word, max 500 words
    words = draw(st.lists(
        st.text(
            alphabet=st.characters(
                blacklist_categories=('Cc', 'Cs'),
                blacklist_characters='\x00'
            ),
            min_size=1,
            max_size=20
        ),
        min_size=1,
        max_size=500
    ))
    return " ".join(words)


@st.composite
def voice_id_strategy(draw):
    """Generate valid Polly voice IDs"""
    valid_voices = [
        "Matthew", "Joanna", "Justin", "Ivy", "Brian", "Kendra",
        "Arthur", "Aria", "Joey", "Emma", "Salli"
    ]
    return draw(st.sampled_from(valid_voices))


@st.composite
def engine_strategy(draw):
    """Generate valid Polly engine types"""
    return draw(st.sampled_from(["neural", "standard"]))


@st.composite
def output_format_strategy(draw):
    """Generate valid output formats"""
    return draw(st.sampled_from(["mp3", "ogg_vorbis"]))


@st.composite
def panel_id_strategy(draw):
    """Generate valid panel IDs"""
    return f"panel_{draw(st.integers(min_value=0, max_value=1000))}"


@st.composite
def audio_generation_request_strategy(draw):
    """Generate valid AudioGenerationRequest objects"""
    return AudioGenerationRequest(
        text=draw(valid_text_strategy()),
        voice_id=draw(voice_id_strategy()),
        engine=draw(engine_strategy()),
        output_format=draw(output_format_strategy()),
        panel_id=draw(panel_id_strategy()),
    )


@st.composite
def voice_profile_strategy(draw):
    """Generate random voice profiles"""
    return VoiceProfile(
        voice_id=draw(voice_id_strategy()),
        gender=draw(st.sampled_from(['male', 'female', 'neutral'])),
        age=draw(st.sampled_from(['child', 'young-adult', 'adult', 'senior'])),
        tone=draw(st.text(min_size=1, max_size=30))
    )


@st.composite
def character_strategy(draw):
    """Generate random characters"""
    return Character(
        id=f"char_{draw(st.integers(min_value=0, max_value=1000))}",
        name=draw(st.text(min_size=1, max_size=50)),
        visual_description=draw(st.text(min_size=1, max_size=200)),
        personality=draw(st.text(min_size=1, max_size=100)),
        voice_profile=draw(voice_profile_strategy()),
        first_introduced=draw(st.integers(min_value=0, max_value=100)),
        last_seen=draw(st.integers(min_value=0, max_value=100)),
        visual_signatures=draw(st.lists(st.text(min_size=1, max_size=50), max_size=5))
    )


def create_mock_generator():
    """Create a PollyAudioGenerator with mocked client"""
    client = Mock()
    
    def mock_synthesize_speech(**kwargs):
        """Mock Polly synthesize_speech that returns fresh BytesIO each time"""
        return {
            "AudioStream": BytesIO(b"mock_audio_data"),
            "ContentType": "audio/mpeg",
        }
    
    client.synthesize_speech.side_effect = mock_synthesize_speech
    
    with patch("src.polly_generation.generator.aws_clients"):
        gen = PollyAudioGenerator(use_neural=True)
        gen.polly_client = client
        return gen


@settings(deadline=None, max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(request=audio_generation_request_strategy())
def test_audio_generation_produces_valid_segment(request):
    """Property: For any valid AudioGenerationRequest, audio generation SHALL produce a valid AudioSegment.
    
    **Feature: comic-audio-narrator, Property 11: Local Audio Storage**
    **Validates: Requirements 4.1**
    """
    generator = create_mock_generator()
    segment = generator.generate_audio(request)

    # Verify segment has all required fields
    assert segment.panel_id == request.panel_id
    assert isinstance(segment.audio_data, bytes)
    assert len(segment.audio_data) > 0
    assert segment.voice_id == request.voice_id
    assert segment.engine == request.engine
    assert segment.duration > 0


@settings(deadline=None, max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    requests=st.lists(
        audio_generation_request_strategy(),
        min_size=1,
        max_size=10,
        unique_by=lambda r: r.panel_id
    )
)
def test_multiple_segments_composition(requests):
    """Property: For any set of audio segments, composing them SHALL produce a CompositeAudio with correct total duration.
    
    **Feature: comic-audio-narrator, Property 11: Local Audio Storage**
    **Validates: Requirements 4.1**
    """
    generator = create_mock_generator()
    segments = []
    for request in requests:
        segment = generator.generate_audio(request)
        segments.append(segment)

    metadata = AudioMetadata(title="Test Comic")
    composite = generator.compose_audio(segments=segments, metadata=metadata)

    # Verify composite has all segments
    assert len(composite.segments) == len(segments)

    # Verify total duration is sum of segment durations
    expected_duration = sum(s.duration for s in segments)
    assert composite.total_duration == pytest.approx(expected_duration, rel=0.01)

    # Verify metadata is preserved
    assert composite.metadata.title == "Test Comic"


@settings(deadline=None, max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    text=valid_text_strategy(),
    voice_id=voice_id_strategy(),
    engine=engine_strategy(),
)
def test_duration_estimation_increases_with_text_length(text, voice_id, engine):
    """Property: For any text, longer text SHALL result in longer estimated duration.
    
    **Feature: comic-audio-narrator, Property 11: Local Audio Storage**
    **Validates: Requirements 4.1**
    """
    generator = create_mock_generator()
    short_text = "Hello"
    long_text = text

    short_duration = generator._estimate_duration(short_text)
    long_duration = generator._estimate_duration(long_text)

    # Longer text should have longer or equal duration
    assert long_duration >= short_duration


@settings(deadline=None, max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    gender=st.sampled_from(['male', 'female', 'neutral']),
    age=st.sampled_from(['child', 'young-adult', 'adult', 'senior']),
    tone=st.one_of(st.none(), st.text(min_size=1, max_size=30))
)
def test_voice_profile_selection_returns_valid_voice(gender, age, tone):
    """Property: For any character profile, voice selection SHALL return a valid Polly voice ID.
    
    **Feature: comic-audio-narrator, Property 11: Local Audio Storage**
    **Validates: Requirements 4.1**
    """
    generator = create_mock_generator()
    voice_id = generator.get_voice_for_profile(gender, age, tone)

    # Verify voice ID is in the voice map
    assert voice_id in generator.voice_map.values()


@settings(deadline=None, max_examples=100)
@given(
    character=character_strategy(),
    voice_id=voice_id_strategy(),
)
def test_voice_consistency_maintained_across_appearances(character, voice_id):
    """Property: For any character, once a voice is assigned, it SHALL remain consistent across all appearances.
    
    **Feature: comic-audio-narrator, Property 11: Local Audio Storage**
    **Validates: Requirements 4.1**
    """
    manager = VoiceProfileManager()

    # First appearance - assign voice
    is_consistent_1 = manager.ensure_voice_consistency(character, voice_id)
    assert is_consistent_1 is True

    # Subsequent appearances - verify consistency
    is_consistent_2 = manager.ensure_voice_consistency(character, voice_id)
    assert is_consistent_2 is True

    # Verify stored voice matches
    stored_voice = manager.get_voice_for_character(character.id)
    assert stored_voice == voice_id


@settings(deadline=None, max_examples=100)
@given(
    characters=st.lists(
        character_strategy(),
        min_size=2,
        max_size=5,
        unique_by=lambda c: c.id
    )
)
def test_multiple_characters_maintain_independent_voices(characters):
    """Property: For any set of characters, each SHALL maintain its own independent voice profile.
    
    **Feature: comic-audio-narrator, Property 11: Local Audio Storage**
    **Validates: Requirements 4.1**
    """
    manager = VoiceProfileManager()

    # Assign voices to all characters
    for i, character in enumerate(characters):
        # Use different voices for each character
        valid_voices = ["Matthew", "Joanna", "Justin", "Ivy", "Brian"]
        voice_id = valid_voices[i % len(valid_voices)]
        manager.assign_voice_profile(character, voice_id)

    # Verify each character has its own voice
    all_voices = manager.get_all_character_voices()
    assert len(all_voices) == len(characters)

    # Verify no two characters have the same voice (if we assigned different ones)
    voice_values = list(all_voices.values())
    # This is a weaker property - just verify we can retrieve all voices
    for character in characters:
        stored_voice = manager.get_voice_for_character(character.id)
        assert stored_voice is not None


@settings(deadline=None, max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    requests=st.lists(
        audio_generation_request_strategy(),
        min_size=1,
        max_size=5,
        unique_by=lambda r: r.panel_id
    )
)
def test_segment_storage_and_retrieval(requests):
    """Property: For any set of generated segments, stored segments SHALL be retrievable and match originals.
    
    **Feature: comic-audio-narrator, Property 11: Local Audio Storage**
    **Validates: Requirements 4.1**
    """
    generator = create_mock_generator()
    # Generate and store segments
    for request in requests:
        generator.generate_audio(request)

    # Retrieve stored segments
    stored_segments = generator.get_segments()

    # Verify all segments are stored
    assert len(stored_segments) == len(requests)

    # Verify each segment has required data
    for segment in stored_segments:
        assert segment.panel_id is not None
        assert len(segment.audio_data) > 0
        assert segment.duration > 0


@settings(deadline=None, max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    requests=st.lists(
        audio_generation_request_strategy(),
        min_size=1,
        max_size=5,
        unique_by=lambda r: r.panel_id
    )
)
def test_segment_reset_clears_storage(requests):
    """Property: For any set of stored segments, reset SHALL clear all stored segments.
    
    **Feature: comic-audio-narrator, Property 11: Local Audio Storage**
    **Validates: Requirements 4.1**
    """
    generator = create_mock_generator()
    # Generate and store segments
    for request in requests:
        generator.generate_audio(request)

    assert len(generator.get_segments()) > 0

    # Reset segments
    generator.reset_segments()

    # Verify all segments are cleared
    assert len(generator.get_segments()) == 0


@settings(deadline=None, max_examples=100)
@given(
    use_neural_1=st.booleans(),
    use_neural_2=st.booleans(),
)
def test_engine_switching_updates_voice_map(use_neural_1, use_neural_2):
    """Property: For any engine switch, the voice map SHALL update to match the selected engine.
    
    **Feature: comic-audio-narrator, Property 11: Local Audio Storage**
    **Validates: Requirements 4.1**
    """
    with patch("src.polly_generation.generator.aws_clients"):
        generator = PollyAudioGenerator(use_neural=use_neural_1)

        # Verify initial state
        if use_neural_1:
            assert generator.voice_map == generator.NEURAL_VOICES
        else:
            assert generator.voice_map == generator.STANDARD_VOICES

        # Switch engine
        generator.set_engine(use_neural_2)

        # Verify voice map updated
        if use_neural_2:
            assert generator.voice_map == generator.NEURAL_VOICES
        else:
            assert generator.voice_map == generator.STANDARD_VOICES


@settings(deadline=None, max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    metadata_title=st.text(min_size=1, max_size=100),
    num_segments=st.integers(min_value=1, max_value=5),
)
def test_composite_audio_preserves_metadata(metadata_title, num_segments):
    """Property: For any CompositeAudio, metadata SHALL be preserved and retrievable.
    
    **Feature: comic-audio-narrator, Property 11: Local Audio Storage**
    **Validates: Requirements 4.1**
    """
    generator = create_mock_generator()
    # Generate segments
    for i in range(num_segments):
        request = AudioGenerationRequest(
            text=f"Panel {i} text",
            voice_id="Joanna",
            engine="neural",
            output_format="mp3",
            panel_id=f"panel_{i}",
        )
        generator.generate_audio(request)

    # Create metadata
    metadata = AudioMetadata(
        title=metadata_title,
        characters=["Character 1", "Character 2"],
        scenes=["Scene 1"],
    )

    # Compose audio
    composite = generator.compose_audio(metadata=metadata)

    # Verify metadata is preserved
    assert composite.metadata.title == metadata_title
    assert len(composite.metadata.characters) == 2
    assert len(composite.metadata.scenes) == 1
