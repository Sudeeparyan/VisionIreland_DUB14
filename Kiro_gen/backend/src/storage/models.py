"""Data models for storage and library management."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any
import json


@dataclass
class AudioMetadata:
    """Metadata associated with stored audio files."""
    title: str
    characters: List[str]
    scenes: List[str]
    generated_at: datetime
    model_used: str
    total_duration: float
    voice_profiles: Dict[str, Dict[str, str]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['generated_at'] = self.generated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AudioMetadata':
        """Create from dictionary (e.g., from JSON)."""
        data = data.copy()
        data['generated_at'] = datetime.fromisoformat(data['generated_at'])
        return cls(**data)


@dataclass
class StoredAudio:
    """Represents an audio file stored in the library."""
    id: str
    s3_key: str
    metadata: AudioMetadata
    file_size: int
    uploaded_at: datetime
    local_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            's3_key': self.s3_key,
            'metadata': self.metadata.to_dict(),
            'file_size': self.file_size,
            'uploaded_at': self.uploaded_at.isoformat(),
            'local_path': self.local_path,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StoredAudio':
        """Create from dictionary (e.g., from JSON)."""
        data = data.copy()
        data['metadata'] = AudioMetadata.from_dict(data['metadata'])
        data['uploaded_at'] = datetime.fromisoformat(data['uploaded_at'])
        return cls(**data)


@dataclass
class LibraryIndex:
    """Index of all stored audio files in the library."""
    items: List[StoredAudio] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    total_size: int = 0

    def add_item(self, item: StoredAudio) -> None:
        """Add an audio file to the index."""
        self.items.append(item)
        self.total_size += item.file_size
        self.last_updated = datetime.now()

    def remove_item(self, audio_id: str) -> Optional[StoredAudio]:
        """Remove an audio file from the index."""
        for i, item in enumerate(self.items):
            if item.id == audio_id:
                removed = self.items.pop(i)
                self.total_size -= removed.file_size
                self.last_updated = datetime.now()
                return removed
        return None

    def get_item(self, audio_id: str) -> Optional[StoredAudio]:
        """Get an audio file by ID."""
        for item in self.items:
            if item.id == audio_id:
                return item
        return None

    def search_by_title(self, title: str) -> List[StoredAudio]:
        """Search for audio files by title (case-insensitive substring match)."""
        title_lower = title.lower()
        return [item for item in self.items if title_lower in item.metadata.title.lower()]

    def search_by_character(self, character: str) -> List[StoredAudio]:
        """Search for audio files by character name."""
        return [item for item in self.items if character in item.metadata.characters]

    def search_by_scene(self, scene: str) -> List[StoredAudio]:
        """Search for audio files by scene name."""
        return [item for item in self.items if scene in item.metadata.scenes]

    def filter_by_date_range(self, start_date: datetime, end_date: datetime) -> List[StoredAudio]:
        """Filter audio files by upload date range."""
        return [
            item for item in self.items
            if start_date <= item.uploaded_at <= end_date
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'items': [item.to_dict() for item in self.items],
            'last_updated': self.last_updated.isoformat(),
            'total_size': self.total_size,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LibraryIndex':
        """Create from dictionary (e.g., from JSON)."""
        data = data.copy()
        data['items'] = [StoredAudio.from_dict(item) for item in data['items']]
        data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return cls(**data)
