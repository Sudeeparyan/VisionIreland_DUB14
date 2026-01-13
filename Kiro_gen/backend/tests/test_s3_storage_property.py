"""Property-based tests for S3 audio storage.

Feature: comic-audio-narrator, Property 12: S3 Audio Upload
Validates: Requirements 4.2
"""

from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime
from unittest.mock import Mock, patch
import json

from src.storage.s3_manager import S3StorageManager
from src.storage.models import AudioMetadata, LibraryIndex


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
def test_upload_preserves_audio_data(audio_id, audio_data, metadata):
    """Property: Uploaded audio data SHALL be retrievable unchanged.
    
    **Feature: comic-audio-narrator, Property 12: S3 Audio Upload**
    **Validates: Requirements 4.2**
    """
    with patch('src.storage.s3_manager.boto3.client'):
        manager = S3StorageManager('test-bucket')
        manager.s3_client = Mock()
        
        # Mock upload
        manager.upload_audio(audio_id, audio_data, metadata)
        
        # Mock download
        manager.s3_client.get_object.return_value = {
            'Body': Mock(read=Mock(return_value=audio_data))
        }
        
        downloaded = manager.download_audio(audio_id)
        assert downloaded == audio_data


@settings(deadline=None, max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    audio_id=valid_audio_id_strategy(),
    audio_data=st.binary(min_size=100, max_size=100000),
    metadata=metadata_strategy()
)
def test_upload_preserves_metadata(audio_id, audio_data, metadata):
    """Property: Uploaded metadata SHALL be retrievable unchanged.
    
    **Feature: comic-audio-narrator, Property 12: S3 Audio Upload**
    **Validates: Requirements 4.2**
    """
    with patch('src.storage.s3_manager.boto3.client'):
        manager = S3StorageManager('test-bucket')
        manager.s3_client = Mock()
        
        # Mock upload
        manager.upload_audio(audio_id, audio_data, metadata)
        
        # Mock metadata download
        metadata_json = json.dumps(metadata.to_dict())
        manager.s3_client.get_object.return_value = {
            'Body': Mock(read=Mock(return_value=metadata_json.encode('utf-8')))
        }
        
        retrieved = manager.get_metadata(audio_id)
        assert retrieved.title == metadata.title
        assert retrieved.characters == metadata.characters
        assert retrieved.scenes == metadata.scenes


@settings(deadline=None, max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    audio_ids=st.lists(valid_audio_id_strategy(), min_size=1, max_size=5, unique=True),
    audio_data=st.binary(min_size=100, max_size=100000),
    metadata=metadata_strategy()
)
def test_multiple_uploads_stored_independently(audio_ids, audio_data, metadata):
    """Property: Multiple audio uploads SHALL be stored independently.
    
    **Feature: comic-audio-narrator, Property 12: S3 Audio Upload**
    **Validates: Requirements 4.2**
    """
    with patch('src.storage.s3_manager.boto3.client'):
        manager = S3StorageManager('test-bucket')
        manager.s3_client = Mock()
        
        # Upload multiple files
        for audio_id in audio_ids:
            manager.upload_audio(audio_id, audio_data, metadata)
        
        # Verify each has unique S3 key
        calls = manager.s3_client.put_object.call_args_list
        s3_keys = [call[1]['Key'] for call in calls if 'audio.mp3' in call[1]['Key']]
        
        assert len(set(s3_keys)) == len(audio_ids)
