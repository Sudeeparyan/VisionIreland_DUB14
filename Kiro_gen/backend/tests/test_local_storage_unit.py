"""Unit tests for local audio storage management."""

import pytest
import tempfile
from datetime import datetime

from src.storage.local_manager import LocalStorageManager
from src.storage.models import AudioMetadata, LibraryIndex


class TestLocalStorageManager:
    """Test suite for LocalStorageManager"""

    @pytest.fixture
    def manager(self):
        """Create a LocalStorageManager with temporary directory"""
        tmpdir = tempfile.mkdtemp()
        return LocalStorageManager(tmpdir)

    @pytest.fixture
    def sample_metadata(self):
        """Create sample audio metadata"""
        return AudioMetadata(
            title="Test Comic",
            characters=["Hero", "Villain"],
            scenes=["City"],
            generated_at=datetime.now(),
            model_used="Claude",
            total_duration=120.5
        )

    def test_save_and_load_audio(self, manager, sample_metadata):
        """Test saving and loading audio preserves data"""
        audio_data = b"test_audio_data"
        manager.save_audio("audio_1", audio_data, sample_metadata)
        
        loaded = manager.load_audio("audio_1")
        assert loaded == audio_data

    def test_save_and_load_metadata(self, manager, sample_metadata):
        """Test saving and loading metadata"""
        manager.save_audio("audio_1", b"data", sample_metadata)
        
        loaded = manager.get_metadata("audio_1")
        assert loaded.title == "Test Comic"
        assert loaded.characters == ["Hero", "Villain"]

    def test_delete_audio(self, manager, sample_metadata):
        """Test deleting audio removes file"""
        manager.save_audio("audio_1", b"data", sample_metadata)
        manager.delete_audio("audio_1")
        
        assert manager.load_audio("audio_1") is None

    def test_list_audio_files(self, manager, sample_metadata):
        """Test listing audio files"""
        manager.save_audio("audio_1", b"data", sample_metadata)
        manager.save_audio("audio_2", b"data", sample_metadata)
        
        files = manager.list_audio_files()
        assert len(files) == 2

    def test_storage_size(self, manager, sample_metadata):
        """Test calculating storage size"""
        manager.save_audio("audio_1", b"12345", sample_metadata)
        manager.save_audio("audio_2", b"12345", sample_metadata)
        
        size = manager.get_storage_size()
        assert size == 10

    def test_library_index_save_load(self, manager):
        """Test saving and loading library index"""
        index = LibraryIndex()
        manager.save_library_index(index)
        
        loaded = manager.load_library_index()
        assert loaded is not None
