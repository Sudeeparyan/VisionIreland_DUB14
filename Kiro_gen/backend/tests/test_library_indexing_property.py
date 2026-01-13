"""Property-based tests for library indexing and retrieval."""

import pytest
from datetime import datetime, timedelta
from hypothesis import given, strategies as st

from src.storage.models import LibraryIndex, StoredAudio, AudioMetadata


def valid_audio_id_strategy():
    """Generate valid audio IDs (alphanumeric + underscore/dash)."""
    return st.text(
        alphabet='abcdefghijklmnopqrstuvwxyz0123456789_-',
        min_size=1,
        max_size=20
    )


def audio_metadata_strategy():
    """Generate valid AudioMetadata."""
    return st.builds(
        AudioMetadata,
        title=st.text(min_size=1, max_size=100),
        characters=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5),
        scenes=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5),
        generated_at=st.datetimes(),
        model_used=st.sampled_from(['Claude', 'Nova']),
        total_duration=st.floats(min_value=1.0, max_value=3600.0),
    )


def stored_audio_strategy():
    """Generate valid StoredAudio."""
    return st.builds(
        StoredAudio,
        id=valid_audio_id_strategy(),
        s3_key=st.text(min_size=1, max_size=100),
        metadata=audio_metadata_strategy(),
        file_size=st.integers(min_value=1000, max_value=100000000),
        uploaded_at=st.datetimes(),
    )


class TestLibraryIndexingProperties:
    """Property-based tests for LibraryIndex"""

    @given(stored_audio_strategy())
    def test_add_and_retrieve_preserves_data(self, audio):
        """Adding and retrieving audio preserves all data."""
        library = LibraryIndex()
        library.add_item(audio)
        
        retrieved = library.get_item(audio.id)
        assert retrieved is not None
        assert retrieved.id == audio.id
        assert retrieved.metadata.title == audio.metadata.title
        assert retrieved.file_size == audio.file_size

    @given(st.lists(stored_audio_strategy(), min_size=1, max_size=10, unique_by=lambda x: x.id))
    def test_library_size_tracking(self, audios):
        """Library total_size correctly tracks all added items."""
        library = LibraryIndex()
        expected_size = 0
        
        for audio in audios:
            library.add_item(audio)
            expected_size += audio.file_size
        
        assert library.total_size == expected_size

    @given(stored_audio_strategy())
    def test_serialization_roundtrip(self, audio):
        """Serialization and deserialization preserves data."""
        library = LibraryIndex()
        library.add_item(audio)
        
        serialized = library.to_dict()
        deserialized = LibraryIndex.from_dict(serialized)
        
        assert len(deserialized.items) == 1
        assert deserialized.items[0].id == audio.id
        assert deserialized.total_size == audio.file_size
