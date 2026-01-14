"""Library management for audio narratives with indexing and search capabilities."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import LibraryIndex, StoredAudio, AudioMetadata
from .local_manager import LocalStorageManager
from .s3_manager import S3StorageManager

logger = logging.getLogger(__name__)


class LibraryManager:
    """Manages the audio narrative library with indexing, search, and filtering."""

    def __init__(
        self, local_manager: LocalStorageManager, s3_manager: Optional[S3StorageManager] = None
    ):
        """Initialize library manager.

        Args:
            local_manager: Local storage manager instance
            s3_manager: Optional S3 storage manager instance
        """
        self.local_manager = local_manager
        self.s3_manager = s3_manager
        self.library_index = self._load_library_index()

    def _load_library_index(self) -> LibraryIndex:
        """Load library index from storage.

        Returns:
            LibraryIndex object
        """
        # Try to load from local storage first
        index = self.local_manager.load_library_index()

        if index is None and self.s3_manager:
            # Fallback to S3 if local not available
            index = self.s3_manager.download_library_index()

        if index is None:
            # Create new index if none found
            index = LibraryIndex()
            logger.info("Created new library index")

        return index

    async def store_audio(
        self, 
        audio_segments: list, 
        metadata: AudioMetadata
    ) -> StoredAudio:
        """Store audio segments and add to library index.
        
        This method combines the audio segments, saves to storage, and adds to the library index.
        
        Args:
            audio_segments: List of audio segments to store
            metadata: Audio metadata for the stored file
            
        Returns:
            StoredAudio object with storage details
        """
        import uuid
        
        # Generate unique ID for this audio
        audio_id = str(uuid.uuid4())
        
        # Compose audio segments into single file
        composed_audio = b''
        for segment in audio_segments:
            if hasattr(segment, 'audio_data'):
                composed_audio += segment.audio_data
            elif isinstance(segment, bytes):
                composed_audio += segment
        
        # Try S3 first if available
        stored_audio = None
        if self.s3_manager:
            try:
                # S3 upload is synchronous, don't use await
                stored_audio = self.s3_manager.upload_audio(
                    audio_id=audio_id,
                    audio_data=composed_audio,
                    metadata=metadata
                )
                logger.info(f"Successfully stored audio {audio_id} to S3")
            except Exception as e:
                logger.warning(f"S3 storage failed, falling back to local: {e}")
        
        # Fallback to local storage if S3 failed or not available
        if stored_audio is None:
            stored_audio = self.local_manager.save_audio(
                audio_id=audio_id,
                audio_data=composed_audio,
                metadata=metadata
            )
            logger.info(f"Successfully stored audio {audio_id} locally")
        
        # Add to library index
        self.add_audio_to_library(stored_audio)
        
        return stored_audio

    def add_audio_to_library(self, stored_audio: StoredAudio) -> None:
        """Add audio file to the library index.

        Args:
            stored_audio: StoredAudio object to add to library
        """
        self.library_index.add_item(stored_audio)
        self._save_library_index()
        logger.info(f"Added audio {stored_audio.id} to library")

    def remove_audio_from_library(self, audio_id: str) -> Optional[StoredAudio]:
        """Remove audio file from the library index.

        Args:
            audio_id: ID of audio to remove

        Returns:
            Removed StoredAudio object, or None if not found
        """
        removed = self.library_index.remove_item(audio_id)
        if removed:
            self._save_library_index()
            logger.info(f"Removed audio {audio_id} from library")
        return removed

    def get_audio_from_library(self, audio_id: str) -> Optional[StoredAudio]:
        """Get audio file from the library index.

        Args:
            audio_id: ID of audio to retrieve

        Returns:
            StoredAudio object, or None if not found
        """
        return self.library_index.get_item(audio_id)

    def search_by_title(self, title: str) -> List[StoredAudio]:
        """Search library by title.

        Args:
            title: Title to search for (case-insensitive substring match)

        Returns:
            List of matching StoredAudio objects
        """
        return self.library_index.search_by_title(title)

    def search_by_character(self, character: str) -> List[StoredAudio]:
        """Search library by character name.

        Args:
            character: Character name to search for

        Returns:
            List of matching StoredAudio objects
        """
        return self.library_index.search_by_character(character)

    def search_by_scene(self, scene: str) -> List[StoredAudio]:
        """Search library by scene name.

        Args:
            scene: Scene name to search for

        Returns:
            List of matching StoredAudio objects
        """
        return self.library_index.search_by_scene(scene)

    def filter_by_date_range(self, start_date: datetime, end_date: datetime) -> List[StoredAudio]:
        """Filter library by upload date range.

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of matching StoredAudio objects
        """
        return self.library_index.filter_by_date_range(start_date, end_date)

    def get_all_audio(self) -> List[StoredAudio]:
        """Get all audio files in the library.

        Returns:
            List of all StoredAudio objects
        """
        return self.library_index.items.copy()

    async def get_library_index(self) -> List[StoredAudio]:
        """Get all audio files in the library (async version for API compatibility).

        Returns:
            List of all StoredAudio objects
        """
        return self.get_all_audio()

    def get_library_stats(self) -> Dict[str, Any]:
        """Get library statistics.

        Returns:
            Dictionary with library statistics
        """
        total_items = len(self.library_index.items)
        total_size_mb = self.library_index.total_size / (1024 * 1024)

        # Calculate total duration
        total_duration = sum(item.metadata.total_duration for item in self.library_index.items)

        # Get unique characters and scenes
        all_characters = set()
        all_scenes = set()
        for item in self.library_index.items:
            all_characters.update(item.metadata.characters)
            all_scenes.update(item.metadata.scenes)

        return {
            "total_items": total_items,
            "total_size_mb": round(total_size_mb, 2),
            "total_duration_seconds": round(total_duration, 2),
            "total_duration_minutes": round(total_duration / 60, 2),
            "unique_characters": len(all_characters),
            "unique_scenes": len(all_scenes),
            "last_updated": self.library_index.last_updated.isoformat(),
        }

    def rebuild_index(self) -> None:
        """Rebuild library index from storage.

        This scans local and S3 storage to rebuild the index from scratch.
        """
        logger.info("Rebuilding library index from storage")

        # Create new index
        new_index = LibraryIndex()

        # Scan local storage
        local_files = self.local_manager.list_audio_files()
        for file_path in local_files:
            # Extract audio ID from filename
            audio_id = file_path.split("/")[-1].replace(".mp3", "")
            metadata = self.local_manager.get_metadata(audio_id)

            if metadata:
                # Get file size
                file_size = len(self.local_manager.load_audio(audio_id) or b"")

                stored_audio = StoredAudio(
                    id=audio_id,
                    s3_key="",
                    metadata=metadata,
                    file_size=file_size,
                    uploaded_at=metadata.generated_at,
                    local_path=file_path,
                )
                new_index.add_item(stored_audio)

        # Scan S3 storage if available
        if self.s3_manager:
            s3_files = self.s3_manager.list_audio_files()
            for s3_key in s3_files:
                # Extract audio ID from S3 key
                audio_id = s3_key.split("/")[1]
                metadata = self.s3_manager.get_metadata(audio_id)

                if metadata:
                    # Check if already added from local storage
                    if not new_index.get_item(audio_id):
                        stored_audio = StoredAudio(
                            id=audio_id,
                            s3_key=s3_key,
                            metadata=metadata,
                            file_size=0,  # Would need to get object info for size
                            uploaded_at=metadata.generated_at,
                        )
                        new_index.add_item(stored_audio)

        # Replace current index
        self.library_index = new_index
        self._save_library_index()

        logger.info(f"Rebuilt library index with {len(new_index.items)} items")

    def _save_library_index(self) -> None:
        """Save library index to storage."""
        try:
            # Save to local storage first
            self.local_manager.save_library_index(self.library_index)
            logger.info("Library index saved to local storage")
        except Exception as e:
            logger.error(f"Failed to save library index locally: {e}")
            raise

        # Save to S3 if available (best-effort, don't fail if S3 is unavailable)
        if self.s3_manager:
            try:
                self.s3_manager.upload_library_index(self.library_index)
                logger.info("Library index saved to S3")
            except Exception as e:
                logger.warning(f"Failed to save library index to S3 (local backup saved): {e}")

    def sync_with_s3(self) -> None:
        """Synchronize local library index with S3.

        This downloads the S3 index and merges it with the local index.
        """
        if not self.s3_manager:
            logger.warning("S3 manager not available for sync")
            return

        try:
            s3_index = self.s3_manager.download_library_index()
            if s3_index:
                # Merge S3 index with local index
                for item in s3_index.items:
                    if not self.library_index.get_item(item.id):
                        self.library_index.add_item(item)

                self._save_library_index()
                logger.info("Successfully synced library index with S3")
        except Exception as e:
            logger.error(f"Failed to sync library index with S3: {e}")
            raise

    def export_library_metadata(self) -> Dict[str, Any]:
        """Export library metadata for backup or analysis.

        Returns:
            Dictionary with complete library metadata
        """
        return {
            "library_stats": self.get_library_stats(),
            "items": [item.to_dict() for item in self.library_index.items],
            "exported_at": datetime.now().isoformat(),
        }

    async def download_from_s3(self, audio_id: str) -> Optional[str]:
        """Download audio file from S3 and save locally.

        Args:
            audio_id: ID of audio to download

        Returns:
            Local file path where audio was saved, or None if download failed
        """
        if not self.s3_manager:
            logger.warning("S3 manager not available for download")
            return None

        # Get the audio item from library to check S3 key
        audio_item = self.library_index.get_item(audio_id)
        if not audio_item:
            logger.warning(f"Audio {audio_id} not found in library index")
            return None

        if not audio_item.s3_key:
            logger.warning(f"Audio {audio_id} has no S3 key")
            return None

        try:
            # Download audio data from S3
            audio_data = self.s3_manager.download_audio(audio_id)
            if not audio_data:
                logger.error(f"Failed to download audio {audio_id} from S3")
                return None

            # Save locally
            local_path = self.local_manager.audio_dir / f"{audio_id}.mp3"
            with open(local_path, 'wb') as f:
                f.write(audio_data)

            # Update the library index with local path
            audio_item.local_path = str(local_path)
            self._save_library_index()

            logger.info(f"Successfully downloaded audio {audio_id} from S3 to {local_path}")
            return str(local_path)

        except Exception as e:
            logger.error(f"Error downloading audio {audio_id} from S3: {e}")
            return None

    async def delete_audio(self, audio_id: str) -> bool:
        """Delete audio file from library and storage.

        Args:
            audio_id: ID of audio to delete

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            # Remove from library index
            removed = self.remove_audio_from_library(audio_id)
            if not removed:
                return False

            # Delete from local storage
            try:
                self.local_manager.delete_audio(audio_id)
            except Exception as e:
                logger.warning(f"Failed to delete local audio {audio_id}: {e}")

            # Delete from S3 if available
            if self.s3_manager:
                try:
                    self.s3_manager.delete_audio(audio_id)
                except Exception as e:
                    logger.warning(f"Failed to delete S3 audio {audio_id}: {e}")

            return True

        except Exception as e:
            logger.error(f"Error deleting audio {audio_id}: {e}")
            return False

    def validate_library_integrity(self) -> Dict[str, Any]:
        """Validate library integrity by checking file existence.

        Returns:
            Dictionary with validation results
        """
        results = {
            "total_items": len(self.library_index.items),
            "valid_items": 0,
            "missing_local": [],
            "missing_s3": [],
            "metadata_errors": [],
        }

        for item in self.library_index.items:
            try:
                # Check local file if path specified
                if item.local_path:
                    if not self.local_manager.load_audio(item.id):
                        results["missing_local"].append(item.id)
                        continue

                # Check S3 file if key specified
                if item.s3_key and self.s3_manager:
                    if not self.s3_manager.download_audio(item.id):
                        results["missing_s3"].append(item.id)
                        continue

                # Check metadata
                if not item.metadata or not item.metadata.title:
                    results["metadata_errors"].append(item.id)
                    continue

                results["valid_items"] += 1

            except Exception as e:
                logger.error(f"Error validating item {item.id}: {e}")
                results["metadata_errors"].append(item.id)

        results["integrity_score"] = (
            results["valid_items"] / results["total_items"] if results["total_items"] > 0 else 1.0
        )

        return results
