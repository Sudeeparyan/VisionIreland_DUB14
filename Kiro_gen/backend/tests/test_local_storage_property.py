"""Property-based tests for local audio storage.

Feature: comic-audio-narrator, Property 11: Local Audio Storage
Validates: Requirements 4.1
"""

from hypothesis import given, strategies as st, settings, HealthCheck
import tempfile
from datetime import datetime

from src.storage.local_manager import LocalStorageManager
from src.storage.models import AudioMetadata


@st.composite
def metadata_strategy(draw):
    """Generate random audio metadata"""
    return AudioMetadata(
        title=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cc', 'Cs')))),
        characters=draw(st.lists(st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))), max_size=3)),
        scenes=draw(st.lists(st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))), max_size=3)),
        generated_at=datetime.now(),
        model_used="Claude",
        total_duration=draw(st.floats(min_value=1.0, max_value=3600.0))
    )


@st.composite
def valid_audio_id_strategy(draw):
    """Generate valid audio IDs (alphanumeric + underscore/dash only)"""
    return draw(st.text(
        alphabet='abcdefghijklmnopqrstuvwxyz0123456789_-',
        min_size=1,
        max_size=20
    ))


@settings(deadline=None, max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    audio_id=valid_audio_id_strategy(),
    audio_data=st.binary(min_size=100, max_size=100000),
    metadata=metadata_strategy()
)
def test_save_load_preserves_audio_data(audio_id, audio_data, metadata):
    """Property: Saved audio data SHALL be retrievable unchanged.
    
    **Feature: comic-audio-narrator, Property 11: Local Audio Storage**
    **Validates: Requirements 4.1**
    """
    tmpdir = tempfile.mkdtemp()
    manager = LocalStorageManager(tmpdir)
    
    manager.save_audio(audio_id, audio_data, metadata)
    loaded = manager.load_audio(audio_id)
    
    assert loaded == audio_data


@settings(deadline=None, max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    audio_id=valid_audio_id_strategy(),
    audio_data=st.binary(min_size=100, max_size=100000),
    metadata=metadata_strategy()
)
def test_save_load_preserves_metadata(audio_id, audio_data, metadata):
    """Property: Saved metadata SHALL be retrievable unchanged.
    
    **Feature: comic-audio-narrator, Property 11: Local Audio Storage**
    **Validates: Requirements 4.1**
    """
    tmpdir = tempfile.mkdtemp()
    manager = LocalStorageManager(tmpdir)
    
    manager.save_audio(audio_id, audio_data, metadata)
    loaded = manager.get_metadata(audio_id)
    
    assert loaded.title == metadata.title
    assert loaded.characters == metadata.characters
    assert loaded.scenes == metadata.scenes


@settings(deadline=None, max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    audio_ids=st.lists(valid_audio_id_strategy(), min_size=1, max_size=5, unique=True),
    audio_data=st.binary(min_size=100, max_size=100000),
    metadata=metadata_strategy()
)
def test_multiple_files_stored_independently(audio_ids, audio_data, metadata):
    """Property: Multiple audio files SHALL be stored independently.
    
    **Feature: comic-audio-narrator, Property 11: Local Audio Storage**
    **Validates: Requirements 4.1**
    """
    tmpdir = tempfile.mkdtemp()
    manager = LocalStorageManager(tmpdir)
    
    for audio_id in audio_ids:
        manager.save_audio(audio_id, audio_data, metadata)
    
    for audio_id in audio_ids:
        loaded = manager.load_audio(audio_id)
        assert loaded == audio_data
