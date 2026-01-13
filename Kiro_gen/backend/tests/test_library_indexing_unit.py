"""Unit tests for library indexing and retrieval."""

import pytest
from datetime import datetime, timedelta

from src.storage.models import LibraryIndex, StoredAudio, AudioMetadata


class TestLibraryIndexing:
    """Test suite for LibraryIndex"""

    @pytest.fixture
    def library(self):
        """Create a LibraryIndex"""
        return LibraryIndex()

    @pytest.fixture
    def sample_audio(self):
        """Create sample audio"""
        metadata = AudioMetadata(
            title="Test Comic",
            characters=["Hero", "Villain"],
            scenes=["City"],
            generated_at=datetime.now(),
            model_used="Claude",
            total_duration=120.5
        )
        return StoredAudio(
            id="audio_1",
            s3_key="audio/audio_1/audio.mp3",
            metadata=metadata,
            file_size=1000,
            uploaded_at=datetime.now()
        )

    def test_add_item_to_library(self, library, sample_audio):
        """Test adding item to library"""
        library.add_item(sample_audio)
        
        assert len(library.items) == 1
        assert library.total_size == 1000

    def test_get_item_by_id(self, library, sample_audio):
        """Test retrieving item by ID"""
        library.add_item(sample_audio)
        
        result = library.get_item("audio_1")
        assert result is not None
        assert result.id == "audio_1"

    def test_search_by_title(self, library, sample_audio):
        """Test searching by title"""
        library.add_item(sample_audio)
        
        results = library.search_by_title("Test")
        assert len(results) == 1
        assert results[0].id == "audio_1"

    def test_search_by_character(self, library, sample_audio):
        """Test searching by character"""
        library.add_item(sample_audio)
        
        results = library.search_by_character("Hero")
        assert len(results) == 1

    def test_search_by_scene(self, library, sample_audio):
        """Test searching by scene"""
        library.add_item(sample_audio)
        
        results = library.search_by_scene("City")
        assert len(results) == 1

    def test_filter_by_date_range(self, library, sample_audio):
        """Test filtering by date range"""
        library.add_item(sample_audio)
        
        start = datetime.now() - timedelta(hours=1)
        end = datetime.now() + timedelta(hours=1)
        results = library.filter_by_date_range(start, end)
        
        assert len(results) == 1

    def test_remove_item(self, library, sample_audio):
        """Test removing item from library"""
        library.add_item(sample_audio)
        removed = library.remove_item("audio_1")
        
        assert removed is not None
        assert len(library.items) == 0

    def test_library_serialization(self, library, sample_audio):
        """Test library serialization to dict"""
        library.add_item(sample_audio)
        
        result = library.to_dict()
        assert 'items' in result
        assert 'last_updated' in result
        assert 'total_size' in result
        assert result['total_size'] == 1000

    def test_library_deserialization(self, library, sample_audio):
        """Test library deserialization from dict"""
        library.add_item(sample_audio)
        
        serialized = library.to_dict()
        deserialized = LibraryIndex.from_dict(serialized)
        
        assert len(deserialized.items) == 1
        assert deserialized.total_size == 1000
