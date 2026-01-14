"""Local storage management for audio files."""

import json
import logging
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

from .models import StoredAudio, AudioMetadata, LibraryIndex

logger = logging.getLogger(__name__)


class LocalStorageManager:
    """Manages audio file storage and retrieval on local device."""

    def __init__(self, storage_path: str):
        """Initialize local storage manager.
        
        Args:
            storage_path: Base directory path for storing audio files
        """
        self.storage_path = Path(storage_path)
        self.audio_dir = self.storage_path / 'audio'
        self.metadata_dir = self.storage_path / 'metadata'
        self.index_file = self.storage_path / 'library_index.json'
        
        # Create directories if they don't exist
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def save_audio(
        self,
        audio_id: str,
        audio_data: bytes,
        metadata: AudioMetadata
    ) -> StoredAudio:
        """Save audio file locally.
        
        Args:
            audio_id: Unique identifier for the audio file
            audio_data: Audio file content as bytes
            metadata: Audio metadata
            
        Returns:
            StoredAudio object with local path and metadata
        """
        audio_path = self.audio_dir / f"{audio_id}.mp3"
        
        try:
            with open(audio_path, 'wb') as f:
                f.write(audio_data)
            
            # Save metadata
            self._save_metadata(audio_id, metadata)
            
            stored_audio = StoredAudio(
                id=audio_id,
                s3_key='',  # No S3 key for local storage
                metadata=metadata,
                file_size=len(audio_data),
                uploaded_at=datetime.now(),
                local_path=str(audio_path)
            )
            
            logger.info(f"Successfully saved audio {audio_id} locally at {audio_path}")
            return stored_audio
            
        except IOError as e:
            logger.error(f"Failed to save audio {audio_id} locally: {e}")
            raise

    def load_audio(self, audio_id: str) -> Optional[bytes]:
        """Load audio file from local storage.
        
        Args:
            audio_id: Unique identifier for the audio file
            
        Returns:
            Audio file content as bytes, or None if not found
        """
        audio_path = self.audio_dir / f"{audio_id}.mp3"
        
        if not audio_path.exists():
            logger.warning(f"Audio {audio_id} not found locally at {audio_path}")
            return None
        
        try:
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            logger.info(f"Successfully loaded audio {audio_id} from local storage")
            return audio_data
        except IOError as e:
            logger.error(f"Failed to load audio {audio_id} from local storage: {e}")
            raise

    def delete_audio(self, audio_id: str) -> bool:
        """Delete audio file and metadata from local storage.
        
        Args:
            audio_id: Unique identifier for the audio file
            
        Returns:
            True if deletion successful, False if file not found
        """
        audio_path = self.audio_dir / f"{audio_id}.mp3"
        metadata_path = self.metadata_dir / f"{audio_id}.json"
        
        try:
            if audio_path.exists():
                audio_path.unlink()
            if metadata_path.exists():
                metadata_path.unlink()
            logger.info(f"Successfully deleted audio {audio_id} from local storage")
            return True
        except OSError as e:
            logger.error(f"Failed to delete audio {audio_id} from local storage: {e}")
            raise

    def _save_metadata(self, audio_id: str, metadata: AudioMetadata) -> None:
        """Save metadata as JSON file locally.
        
        Args:
            audio_id: Unique identifier for the audio file
            metadata: Audio metadata to store
        """
        metadata_path = self.metadata_dir / f"{audio_id}.json"
        
        try:
            with open(metadata_path, 'w') as f:
                json.dump(metadata.to_dict(), f, indent=2)
            logger.info(f"Successfully saved metadata for audio {audio_id}")
        except IOError as e:
            logger.error(f"Failed to save metadata for audio {audio_id}: {e}")
            raise

    def get_metadata(self, audio_id: str) -> Optional[AudioMetadata]:
        """Retrieve metadata for an audio file from local storage.
        
        Args:
            audio_id: Unique identifier for the audio file
            
        Returns:
            AudioMetadata object, or None if not found
        """
        metadata_path = self.metadata_dir / f"{audio_id}.json"
        
        if not metadata_path.exists():
            logger.warning(f"Metadata for audio {audio_id} not found locally")
            return None
        
        try:
            with open(metadata_path, 'r') as f:
                metadata_dict = json.load(f)
            return AudioMetadata.from_dict(metadata_dict)
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to retrieve metadata for audio {audio_id}: {e}")
            raise

    def get_storage_size(self) -> int:
        """Get total size of local audio storage in bytes.
        
        Returns:
            Total size of all audio files in bytes
        """
        total_size = 0
        try:
            for audio_file in self.audio_dir.glob('*.mp3'):
                total_size += audio_file.stat().st_size
            return total_size
        except OSError as e:
            logger.error(f"Failed to calculate storage size: {e}")
            raise

    def get_available_space(self) -> int:
        """Get available space on the device.
        
        Returns:
            Available space in bytes
        """
        try:
            stat = os.statvfs(self.storage_path)
            available = stat.f_bavail * stat.f_frsize
            return available
        except OSError as e:
            logger.error(f"Failed to get available space: {e}")
            raise

    def list_audio_files(self) -> list:
        """List all audio files in local storage.
        
        Returns:
            List of audio file paths
        """
        try:
            audio_files = list(self.audio_dir.glob('*.mp3'))
            return [str(f) for f in audio_files]
        except OSError as e:
            logger.error(f"Failed to list audio files: {e}")
            raise

    def save_library_index(self, library_index: LibraryIndex) -> None:
        """Save library index locally.
        
        Args:
            library_index: LibraryIndex object to store
        """
        try:
            with open(self.index_file, 'w') as f:
                json.dump(library_index.to_dict(), f, indent=2)
            logger.info("Successfully saved library index locally")
        except IOError as e:
            logger.error(f"Failed to save library index locally: {e}")
            raise

    def load_library_index(self) -> Optional[LibraryIndex]:
        """Load library index from local storage.
        
        Returns:
            LibraryIndex object, or None if not found
        """
        if not self.index_file.exists():
            logger.info("Library index not found locally, creating new index")
            return LibraryIndex()
        
        try:
            with open(self.index_file, 'r') as f:
                index_dict = json.load(f)
            return LibraryIndex.from_dict(index_dict)
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load library index locally: {e}")
            raise

    async def store_audio_with_fallback(
        self,
        audio_data: bytes,
        filename: str
    ) -> str:
        """Store audio file locally as a fallback option.
        
        Args:
            audio_data: Audio file content as bytes
            filename: Name for the audio file
            
        Returns:
            Local path where the audio was stored
        """
        # Ensure filename has .mp3 extension
        if not filename.endswith('.mp3'):
            filename = f"{filename}.mp3"
        
        audio_path = self.audio_dir / filename
        
        try:
            with open(audio_path, 'wb') as f:
                f.write(audio_data)
            
            logger.info(f"Successfully saved audio fallback to {audio_path}")
            return str(audio_path)
            
        except IOError as e:
            logger.error(f"Failed to save audio fallback to {audio_path}: {e}")
            raise
