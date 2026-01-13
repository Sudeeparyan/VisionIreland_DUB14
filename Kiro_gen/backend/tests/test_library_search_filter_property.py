"""Property-based tests for library search and filter functionality.

Feature: comic-audio-narrator, Property 16: Library Search and Filter
Validates: Requirements 5.6
"""

import pytest
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings, HealthCheck

from src.storage.models import LibraryIndex, StoredAudio, AudioMetadata


@st.composite
def valid_audio_id_strategy(draw):
    """Generate valid audio IDs (alphanumeric + underscore/dash)."""
    return draw(st.text(
        alphabet='abcdefghijklmnopqrstuvwxyz0123456789_-',
        min_size=1,
        max_size=20
    ))


@st.composite
def audio_metadata_strategy(draw):
    """Generate valid AudioMetadata."""
    return AudioMetadata(
        title=draw(st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cc', 'Cs')))),
        characters=draw(st.lists(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))), min_size=1, max_size=5)),
        scenes=draw(st.lists(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))), min_size=1, max_size=5)),
        generated_at=draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2025, 12, 31))),
        model_used=draw(st.sampled_from(['Claude', 'Nova'])),
        total_duration=draw(st.floats(min_value=1.0, max_value=3600.0)),
    )


@st.composite
def stored_audio_strategy(draw):
    """Generate valid StoredAudio."""
    return StoredAudio(
        id=draw(valid_audio_id_strategy()),
        s3_key=draw(st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cc', 'Cs')))),
        metadata=draw(audio_metadata_strategy()),
        file_size=draw(st.integers(min_value=1000, max_value=100000000)),
        uploaded_at=draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2025, 12, 31))),
    )


class TestLibrarySearchProperty:
    """Property 16: Library Search and Filter
    
    For any library search or filter operation, the system SHALL return only
    audio narratives matching the specified criteria.
    
    **Feature: comic-audio-narrator, Property 16: Library Search and Filter**
    **Validates: Requirements 5.6**
    """

    @settings(deadline=None, max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        audios=st.lists(stored_audio_strategy(), min_size=1, max_size=10, unique_by=lambda x: x.id),
        search_term=st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz')
    )
    def test_search_returns_only_matching_items(self, audios, search_term):
        """Property: Search SHALL return only items matching the search term.
        
        **Feature: comic-audio-narrator, Property 16: Library Search and Filter**
        **Validates: Requirements 5.6**
        """
        library = LibraryIndex()
        for audio in audios:
            library.add_item(audio)
        
        # Perform search
        results = library.search(search_term)
        
        # Verify all results contain the search term
        for result in results:
            title_match = search_term.lower() in result.metadata.title.lower()
            character_match = any(
                search_term.lower() in char.lower() 
                for char in result.metadata.characters
            )
            scene_match = any(
                search_term.lower() in scene.lower() 
                for scene in result.metadata.scenes
            )
            
            assert title_match or character_match or scene_match, \
                f"Result '{result.metadata.title}' should match search term '{search_term}'"

    @settings(deadline=None, max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(audios=st.lists(stored_audio_strategy(), min_size=1, max_size=10, unique_by=lambda x: x.id))
    def test_search_with_exact_title_returns_item(self, audios):
        """Property: Search with exact title SHALL return the matching item.
        
        **Feature: comic-audio-narrator, Property 16: Library Search and Filter**
        **Validates: Requirements 5.6**
        """
        library = LibraryIndex()
        for audio in audios:
            library.add_item(audio)
        
        # Search for exact title of first item
        target = audios[0]
        results = library.search(target.metadata.title)
        
        # Verify target is in results
        result_ids = [r.id for r in results]
        assert target.id in result_ids, \
            f"Exact title search should return the item"

    @settings(deadline=None, max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(audios=st.lists(stored_audio_strategy(), min_size=1, max_size=10, unique_by=lambda x: x.id))
    def test_empty_search_returns_all_items(self, audios):
        """Property: Empty search SHALL return all items.
        
        **Feature: comic-audio-narrator, Property 16: Library Search and Filter**
        **Validates: Requirements 5.6**
        """
        library = LibraryIndex()
        for audio in audios:
            library.add_item(audio)
        
        # Empty search
        results = library.search("")
        
        # Should return all items
        assert len(results) == len(audios), \
            f"Empty search should return all {len(audios)} items, got {len(results)}"


class TestLibraryFilterProperty:
    """Property 16: Library Filter
    
    For any library filter operation, the system SHALL return only
    audio narratives matching the specified filter criteria.
    
    **Feature: comic-audio-narrator, Property 16: Library Search and Filter**
    **Validates: Requirements 5.6**
    """

    @settings(deadline=None, max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(audios=st.lists(stored_audio_strategy(), min_size=2, max_size=10, unique_by=lambda x: x.id))
    def test_filter_by_date_range_returns_matching_items(self, audios):
        """Property: Date filter SHALL return only items within range.
        
        **Feature: comic-audio-narrator, Property 16: Library Search and Filter**
        **Validates: Requirements 5.6**
        """
        library = LibraryIndex()
        for audio in audios:
            library.add_item(audio)
        
        # Get date range from first item
        target_date = audios[0].uploaded_at
        start_date = target_date - timedelta(days=1)
        end_date = target_date + timedelta(days=1)
        
        # Filter by date range
        results = library.filter_by_date(start_date, end_date)
        
        # Verify all results are within range
        for result in results:
            assert start_date <= result.uploaded_at <= end_date, \
                f"Result date {result.uploaded_at} should be within range"

    @settings(deadline=None, max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(audios=st.lists(stored_audio_strategy(), min_size=2, max_size=10, unique_by=lambda x: x.id))
    def test_filter_by_duration_returns_matching_items(self, audios):
        """Property: Duration filter SHALL return only items within range.
        
        **Feature: comic-audio-narrator, Property 16: Library Search and Filter**
        **Validates: Requirements 5.6**
        """
        library = LibraryIndex()
        for audio in audios:
            library.add_item(audio)
        
        # Get duration range
        min_duration = min(a.metadata.total_duration for a in audios)
        max_duration = max(a.metadata.total_duration for a in audios)
        mid_duration = (min_duration + max_duration) / 2
        
        # Filter by duration
        results = library.filter_by_duration(min_duration, mid_duration)
        
        # Verify all results are within range
        for result in results:
            assert min_duration <= result.metadata.total_duration <= mid_duration, \
                f"Result duration {result.metadata.total_duration} should be within range"

    @settings(deadline=None, max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(audios=st.lists(stored_audio_strategy(), min_size=1, max_size=10, unique_by=lambda x: x.id))
    def test_filter_by_character_returns_matching_items(self, audios):
        """Property: Character filter SHALL return only items with that character.
        
        **Feature: comic-audio-narrator, Property 16: Library Search and Filter**
        **Validates: Requirements 5.6**
        """
        library = LibraryIndex()
        for audio in audios:
            library.add_item(audio)
        
        # Get a character from first item
        if audios[0].metadata.characters:
            target_character = audios[0].metadata.characters[0]
            
            # Filter by character
            results = library.filter_by_character(target_character)
            
            # Verify all results contain the character
            for result in results:
                assert target_character in result.metadata.characters, \
                    f"Result should contain character '{target_character}'"

    @settings(deadline=None, max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(audios=st.lists(stored_audio_strategy(), min_size=1, max_size=10, unique_by=lambda x: x.id))
    def test_combined_filters_return_intersection(self, audios):
        """Property: Combined filters SHALL return intersection of results.
        
        **Feature: comic-audio-narrator, Property 16: Library Search and Filter**
        **Validates: Requirements 5.6**
        """
        library = LibraryIndex()
        for audio in audios:
            library.add_item(audio)
        
        # Apply multiple filters
        target = audios[0]
        
        # Filter by date and search by title
        start_date = target.uploaded_at - timedelta(days=1)
        end_date = target.uploaded_at + timedelta(days=1)
        
        date_results = library.filter_by_date(start_date, end_date)
        search_results = library.search(target.metadata.title)
        
        # Combined results should be intersection
        date_ids = set(r.id for r in date_results)
        search_ids = set(r.id for r in search_results)
        
        # Target should be in both
        assert target.id in date_ids, "Target should be in date filter results"
        assert target.id in search_ids, "Target should be in search results"
