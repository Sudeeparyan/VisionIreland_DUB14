"""Property-based tests for metadata persistence.

Feature: comic-audio-narrator, Property 13: Library Metadata Preservation
Validates: Requirements 4.5
"""

from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime
import json

from src.storage.metadata import MetadataManager


@st.composite
def metadata_strategy(draw):
    """Generate random metadata"""
    return {
        'title': draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cc', 'Cs')))),
        'characters': draw(st.lists(st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))), max_size=3)),
        'scenes': draw(st.lists(st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))), max_size=3)),
        'generated_at': datetime.now(),
        'model_used': 'Claude',
        'total_duration': draw(st.floats(min_value=1.0, max_value=3600.0))
    }


@settings(deadline=None, max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(metadata=metadata_strategy())
def test_serialize_deserialize_preserves_data(metadata):
    """Property: Serialized metadata SHALL be deserializable unchanged.
    
    **Feature: comic-audio-narrator, Property 13: Library Metadata Preservation**
    **Validates: Requirements 4.5**
    """
    serialized = MetadataManager.serialize_metadata(metadata)
    deserialized = MetadataManager.deserialize_metadata(serialized)
    
    assert deserialized['title'] == metadata['title']
    assert deserialized['characters'] == metadata['characters']
    assert deserialized['scenes'] == metadata['scenes']
    assert deserialized['total_duration'] == metadata['total_duration']


@settings(deadline=None, max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(metadata=metadata_strategy())
def test_serialized_metadata_is_valid_json(metadata):
    """Property: Serialized metadata SHALL be valid JSON.
    
    **Feature: comic-audio-narrator, Property 13: Library Metadata Preservation**
    **Validates: Requirements 4.5**
    """
    serialized = MetadataManager.serialize_metadata(metadata)
    
    # Should not raise
    parsed = json.loads(serialized)
    assert isinstance(parsed, dict)


@settings(deadline=None, max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(metadata=metadata_strategy())
def test_metadata_validation_passes_for_valid_data(metadata):
    """Property: Valid metadata SHALL pass validation.
    
    **Feature: comic-audio-narrator, Property 13: Library Metadata Preservation**
    **Validates: Requirements 4.5**
    """
    result = MetadataManager.validate_metadata(metadata)
    assert result is True
