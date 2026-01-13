"""Unit tests for metadata persistence."""

import pytest
import json
from datetime import datetime

from src.storage.metadata import MetadataManager


class TestMetadataManager:
    """Test suite for MetadataManager"""

    @pytest.fixture
    def sample_metadata(self):
        """Create sample metadata"""
        return {
            'title': 'Test Comic',
            'characters': ['Hero', 'Villain'],
            'scenes': ['City', 'Forest'],
            'generated_at': datetime.now(),
            'model_used': 'Claude',
            'total_duration': 120.5
        }

    def test_serialize_metadata(self, sample_metadata):
        """Test serializing metadata to JSON"""
        result = MetadataManager.serialize_metadata(sample_metadata)
        
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed['title'] == 'Test Comic'
        assert parsed['characters'] == ['Hero', 'Villain']

    def test_deserialize_metadata(self, sample_metadata):
        """Test deserializing metadata from JSON"""
        json_str = MetadataManager.serialize_metadata(sample_metadata)
        result = MetadataManager.deserialize_metadata(json_str)
        
        assert result['title'] == 'Test Comic'
        assert result['characters'] == ['Hero', 'Villain']
        assert isinstance(result['generated_at'], datetime)

    def test_validate_metadata_valid(self, sample_metadata):
        """Test validating valid metadata"""
        result = MetadataManager.validate_metadata(sample_metadata)
        assert result is True

    def test_validate_metadata_missing_field(self, sample_metadata):
        """Test validation fails with missing field"""
        del sample_metadata['title']
        result = MetadataManager.validate_metadata(sample_metadata)
        assert result is False

    def test_validate_metadata_invalid_type(self, sample_metadata):
        """Test validation fails with invalid type"""
        sample_metadata['characters'] = 'not a list'
        result = MetadataManager.validate_metadata(sample_metadata)
        assert result is False

    def test_merge_metadata(self, sample_metadata):
        """Test merging metadata"""
        updates = {
            'characters': ['NewChar'],
            'model_used': 'Nova'
        }
        
        result = MetadataManager.merge_metadata(sample_metadata, updates)
        
        assert 'Hero' in result['characters']
        assert 'NewChar' in result['characters']
        assert result['model_used'] == 'Nova'

    def test_extract_metadata_summary(self, sample_metadata):
        """Test extracting metadata summary"""
        result = MetadataManager.extract_metadata_summary(sample_metadata)
        
        assert 'Test Comic' in result
        assert '2' in result  # 2 characters
        assert '120.5' in result  # duration

    def test_serialize_deserialize_roundtrip(self, sample_metadata):
        """Test serialize/deserialize roundtrip preserves data"""
        serialized = MetadataManager.serialize_metadata(sample_metadata)
        deserialized = MetadataManager.deserialize_metadata(serialized)
        
        assert deserialized['title'] == sample_metadata['title']
        assert deserialized['characters'] == sample_metadata['characters']
        assert deserialized['total_duration'] == sample_metadata['total_duration']
