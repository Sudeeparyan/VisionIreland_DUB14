"""S3 storage management for audio files and metadata."""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

from .models import StoredAudio, AudioMetadata, LibraryIndex

logger = logging.getLogger(__name__)


class S3StorageManager:
    """Manages audio file storage and retrieval from AWS S3."""

    def __init__(self, bucket_name: str, region: str = 'us-east-1'):
        """Initialize S3 storage manager.
        
        Args:
            bucket_name: S3 bucket name for storing audio files
            region: AWS region for S3 bucket
        """
        self.bucket_name = bucket_name
        self.region = region
        self.s3_client = boto3.client('s3', region_name=region)
        self.storage_class = 'STANDARD'

    def set_storage_class(self, storage_class: str) -> None:
        """Set storage class for new uploads.
        
        Args:
            storage_class: One of 'STANDARD', 'INTELLIGENT_TIERING', 'GLACIER'
        """
        valid_classes = ['STANDARD', 'INTELLIGENT_TIERING', 'GLACIER']
        if storage_class not in valid_classes:
            raise ValueError(f"Invalid storage class. Must be one of {valid_classes}")
        self.storage_class = storage_class

    def upload_audio(
        self,
        audio_id: str,
        audio_data: bytes,
        metadata: AudioMetadata,
        content_type: str = 'audio/mpeg'
    ) -> StoredAudio:
        """Upload audio file to S3.
        
        Args:
            audio_id: Unique identifier for the audio file
            audio_data: Audio file content as bytes
            metadata: Audio metadata
            content_type: MIME type of audio file
            
        Returns:
            StoredAudio object with S3 key and metadata
            
        Raises:
            ClientError: If S3 upload fails
        """
        s3_key = f"audio/{audio_id}/audio.mp3"
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=audio_data,
                ContentType=content_type,
                StorageClass=self.storage_class,
                Metadata={
                    'audio-id': audio_id,
                    'title': metadata.title[:256],  # S3 metadata has size limits
                }
            )
            
            stored_audio = StoredAudio(
                id=audio_id,
                s3_key=s3_key,
                metadata=metadata,
                file_size=len(audio_data),
                uploaded_at=datetime.now()
            )
            
            # Upload metadata as separate JSON file
            self._upload_metadata(audio_id, metadata)
            
            logger.info(f"Successfully uploaded audio {audio_id} to S3")
            return stored_audio
            
        except ClientError as e:
            logger.error(f"Failed to upload audio {audio_id} to S3: {e}")
            raise

    def download_audio(self, audio_id: str) -> Optional[bytes]:
        """Download audio file from S3.
        
        Args:
            audio_id: Unique identifier for the audio file
            
        Returns:
            Audio file content as bytes, or None if not found
        """
        s3_key = f"audio/{audio_id}/audio.mp3"
        
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            audio_data = response['Body'].read()
            logger.info(f"Successfully downloaded audio {audio_id} from S3")
            return audio_data
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"Audio {audio_id} not found in S3")
                return None
            logger.error(f"Failed to download audio {audio_id} from S3: {e}")
            raise

    def delete_audio(self, audio_id: str) -> bool:
        """Delete audio file and metadata from S3.
        
        Args:
            audio_id: Unique identifier for the audio file
            
        Returns:
            True if deletion successful, False if file not found
        """
        s3_key = f"audio/{audio_id}/audio.mp3"
        metadata_key = f"audio/{audio_id}/metadata.json"
        
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=metadata_key)
            logger.info(f"Successfully deleted audio {audio_id} from S3")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete audio {audio_id} from S3: {e}")
            raise

    def _upload_metadata(self, audio_id: str, metadata: AudioMetadata) -> None:
        """Upload metadata as JSON file to S3.
        
        Args:
            audio_id: Unique identifier for the audio file
            metadata: Audio metadata to store
        """
        metadata_key = f"audio/{audio_id}/metadata.json"
        metadata_json = json.dumps(metadata.to_dict(), indent=2)
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=metadata_key,
                Body=metadata_json.encode('utf-8'),
                ContentType='application/json'
            )
            logger.info(f"Successfully uploaded metadata for audio {audio_id}")
        except ClientError as e:
            logger.error(f"Failed to upload metadata for audio {audio_id}: {e}")
            raise

    def get_metadata(self, audio_id: str) -> Optional[AudioMetadata]:
        """Retrieve metadata for an audio file from S3.
        
        Args:
            audio_id: Unique identifier for the audio file
            
        Returns:
            AudioMetadata object, or None if not found
        """
        metadata_key = f"audio/{audio_id}/metadata.json"
        
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=metadata_key)
            metadata_json = response['Body'].read().decode('utf-8')
            metadata_dict = json.loads(metadata_json)
            return AudioMetadata.from_dict(metadata_dict)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"Metadata for audio {audio_id} not found in S3")
                return None
            logger.error(f"Failed to retrieve metadata for audio {audio_id}: {e}")
            raise

    def list_audio_files(self, prefix: str = 'audio/') -> list:
        """List all audio files in S3 bucket.
        
        Args:
            prefix: S3 key prefix to filter results
            
        Returns:
            List of S3 keys for audio files
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return []
            
            # Filter to only audio files (not metadata)
            audio_keys = [
                obj['Key'] for obj in response['Contents']
                if obj['Key'].endswith('audio.mp3')
            ]
            return audio_keys
        except ClientError as e:
            logger.error(f"Failed to list audio files from S3: {e}")
            raise

    def upload_library_index(self, library_index: LibraryIndex) -> None:
        """Upload library index to S3.
        
        Args:
            library_index: LibraryIndex object to store
        """
        index_key = 'library/index.json'
        index_json = json.dumps(library_index.to_dict(), indent=2)
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=index_key,
                Body=index_json.encode('utf-8'),
                ContentType='application/json'
            )
            logger.info("Successfully uploaded library index to S3")
        except ClientError as e:
            logger.error(f"Failed to upload library index to S3: {e}")
            raise

    def download_library_index(self) -> Optional[LibraryIndex]:
        """Download library index from S3.
        
        Returns:
            LibraryIndex object, or None if not found
        """
        index_key = 'library/index.json'
        
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=index_key)
            index_json = response['Body'].read().decode('utf-8')
            index_dict = json.loads(index_json)
            return LibraryIndex.from_dict(index_dict)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.info("Library index not found in S3, creating new index")
                return LibraryIndex()
            logger.error(f"Failed to download library index from S3: {e}")
            raise
