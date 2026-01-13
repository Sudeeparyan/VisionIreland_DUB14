"""Metadata persistence utilities for audio files."""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MetadataManager:
    """Manages metadata persistence and retrieval."""

    @staticmethod
    def serialize_metadata(metadata_dict: Dict[str, Any]) -> str:
        """Serialize metadata to JSON string.
        
        Args:
            metadata_dict: Dictionary containing metadata
            
        Returns:
            JSON string representation of metadata
        """
        try:
            # Handle datetime objects
            def json_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Type {type(obj)} not serializable")
            
            return json.dumps(metadata_dict, default=json_serializer, indent=2)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize metadata: {e}")
            raise

    @staticmethod
    def deserialize_metadata(metadata_json: str) -> Dict[str, Any]:
        """Deserialize metadata from JSON string.
        
        Args:
            metadata_json: JSON string containing metadata
            
        Returns:
            Dictionary representation of metadata
        """
        try:
            metadata_dict = json.loads(metadata_json)
            
            # Convert ISO format datetime strings back to datetime objects
            if 'generated_at' in metadata_dict:
                metadata_dict['generated_at'] = datetime.fromisoformat(
                    metadata_dict['generated_at']
                )
            
            return metadata_dict
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to deserialize metadata: {e}")
            raise

    @staticmethod
    def validate_metadata(metadata_dict: Dict[str, Any]) -> bool:
        """Validate metadata structure and required fields.
        
        Args:
            metadata_dict: Dictionary containing metadata
            
        Returns:
            True if metadata is valid, False otherwise
        """
        required_fields = ['title', 'characters', 'scenes', 'generated_at', 'model_used', 'total_duration']
        
        for field in required_fields:
            if field not in metadata_dict:
                logger.warning(f"Missing required metadata field: {field}")
                return False
        
        # Validate field types
        if not isinstance(metadata_dict['title'], str):
            logger.warning("Metadata 'title' must be a string")
            return False
        
        if not isinstance(metadata_dict['characters'], list):
            logger.warning("Metadata 'characters' must be a list")
            return False
        
        if not isinstance(metadata_dict['scenes'], list):
            logger.warning("Metadata 'scenes' must be a list")
            return False
        
        if not isinstance(metadata_dict['total_duration'], (int, float)):
            logger.warning("Metadata 'total_duration' must be a number")
            return False
        
        return True

    @staticmethod
    def merge_metadata(base_metadata: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Merge metadata updates into base metadata.
        
        Args:
            base_metadata: Base metadata dictionary
            updates: Updates to apply
            
        Returns:
            Merged metadata dictionary
        """
        merged = base_metadata.copy()
        
        # Merge characters list (avoid duplicates)
        if 'characters' in updates:
            existing_chars = set(merged.get('characters', []))
            new_chars = set(updates['characters'])
            merged['characters'] = list(existing_chars | new_chars)
        
        # Merge scenes list (avoid duplicates)
        if 'scenes' in updates:
            existing_scenes = set(merged.get('scenes', []))
            new_scenes = set(updates['scenes'])
            merged['scenes'] = list(existing_scenes | new_scenes)
        
        # Update other fields
        for key, value in updates.items():
            if key not in ['characters', 'scenes']:
                merged[key] = value
        
        return merged

    @staticmethod
    def extract_metadata_summary(metadata_dict: Dict[str, Any]) -> str:
        """Extract a human-readable summary of metadata.
        
        Args:
            metadata_dict: Dictionary containing metadata
            
        Returns:
            Summary string
        """
        title = metadata_dict.get('title', 'Unknown')
        num_characters = len(metadata_dict.get('characters', []))
        num_scenes = len(metadata_dict.get('scenes', []))
        duration = metadata_dict.get('total_duration', 0)
        
        return (
            f"Title: {title}\n"
            f"Characters: {num_characters}\n"
            f"Scenes: {num_scenes}\n"
            f"Duration: {duration:.1f}s"
        )
