"""Unit tests for S3 audio storage management."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from src.storage.s3_manager import S3StorageManager
from src.storage.models import AudioMetadata, StoredAudio, LibraryIndex


class TestS3StorageManager:
    """Test suite for S3StorageManager"""

    @pytest.fixture
    def manager(self):
        """Create an S3StorageManager with mocked boto3 client"""
        with patch('src.storage.s3_manager.boto3.client'):
            return S3StorageManager('test-bucket', 'us-east-1')

    @pytest.fixture
    def sample_metadata(self):
        """Create sample audio metadata"""
        return AudioMetadata(
            title="Test Comic",
            characters=["Hero"],
            scenes=["City"],
            generated_at=datetime.now(),
            model_used="Claude",
            total_duration=120.5
        )

    def test_manager_initialization(self):
        """Test S3StorageManager initialization"""
        with patch('src.storage.s3_manager.boto3.client'):
            manager = S3StorageManager('test-bucket', 'us-west-2')
            assert manager.bucket_name == 'test-bucket'
            assert manager.region == 'us-west-2'
            assert manager.storage_class == 'STANDARD'

    def test_set_storage_class_valid(self, manager):
        """Test setting valid storage class"""
        manager.set_storage_class('INTELLIGENT_TIERING')
        assert manager.storage_class == 'INTELLIGENT_TIERING'

    def test_set_storage_class_invalid(self, manager):
        """Test setting invalid storage class raises error"""
        with pytest.raises(ValueError):
            manager.set_storage_class('INVALID_CLASS')

    def test_upload_audio_success(self, manager, sample_metadata):
        """Test successful audio upload"""
        manager.s3_client = Mock()
        audio_data = b"test_audio_data"
        
        result = manager.upload_audio("audio_1", audio_data, sample_metadata)
        
        assert result.id == "audio_1"
        assert result.s3_key == "audio/audio_1/audio.mp3"
        assert result.file_size == len(audio_data)
        manager.s3_client.put_object.assert_called()

    def test_upload_audio_failure(self, manager, sample_metadata):
        """Test audio upload failure handling"""
        manager.s3_client = Mock()
        manager.s3_client.put_object.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied'}}, 'PutObject'
        )
        
        with pytest.raises(ClientError):
            manager.upload_audio("audio_1", b"data", sample_metadata)

    def test_download_audio_success(self, manager):
        """Test successful audio download"""
        manager.s3_client = Mock()
        manager.s3_client.get_object.return_value = {
            'Body': Mock(read=Mock(return_value=b"audio_data"))
        }
        
        result = manager.download_audio("audio_1")
        
        assert result == b"audio_data"
        manager.s3_client.get_object.assert_called_once()

    def test_download_audio_not_found(self, manager):
        """Test download returns None when audio not found"""
        manager.s3_client = Mock()
        manager.s3_client.get_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey'}}, 'GetObject'
        )
        
        result = manager.download_audio("audio_1")
        
        assert result is None

    def test_delete_audio_success(self, manager):
        """Test successful audio deletion"""
        manager.s3_client = Mock()
        
        result = manager.delete_audio("audio_1")
        
        assert result is True
        assert manager.s3_client.delete_object.call_count == 2

    def test_list_audio_files(self, manager):
        """Test listing audio files"""
        manager.s3_client = Mock()
        manager.s3_client.list_objects_v2.return_value = {
            'Contents': [
                {'Key': 'audio/audio_1/audio.mp3'},
                {'Key': 'audio/audio_1/metadata.json'},
                {'Key': 'audio/audio_2/audio.mp3'},
            ]
        }
        
        result = manager.list_audio_files()
        
        assert len(result) == 2
        assert 'audio/audio_1/audio.mp3' in result
        assert 'audio/audio_2/audio.mp3' in result

    def test_upload_library_index(self, manager):
        """Test uploading library index"""
        manager.s3_client = Mock()
        index = LibraryIndex()
        
        manager.upload_library_index(index)
        
        manager.s3_client.put_object.assert_called_once()

    def test_download_library_index_success(self, manager):
        """Test downloading library index"""
        manager.s3_client = Mock()
        index_json = '{"items": [], "last_updated": "2024-01-01T00:00:00", "total_size": 0}'
        manager.s3_client.get_object.return_value = {
            'Body': Mock(read=Mock(return_value=index_json.encode('utf-8')))
        }
        
        result = manager.download_library_index()
        
        assert isinstance(result, LibraryIndex)

    def test_download_library_index_not_found(self, manager):
        """Test download creates new index when not found"""
        manager.s3_client = Mock()
        manager.s3_client.get_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey'}}, 'GetObject'
        )
        
        result = manager.download_library_index()
        
        assert isinstance(result, LibraryIndex)
        assert len(result.items) == 0
