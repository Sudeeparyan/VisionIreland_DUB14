"""Property-based tests for cache manager."""

import pytest
from hypothesis import given, strategies as st

from src.processing.cache_manager import CacheManager


class TestCacheManagerProperties:
    """Property-based tests for CacheManager"""

    @given(
        namespace=st.text(min_size=1, max_size=20),
        key_data=st.dictionaries(
            st.text(min_size=1, max_size=10),
            st.text(min_size=1, max_size=20),
            min_size=1,
            max_size=3
        ),
        value=st.text(min_size=1, max_size=100)
    )
    def test_set_and_get_preserves_value(self, namespace, key_data, value):
        """Setting and getting preserves the exact value."""
        cache = CacheManager()
        cache.set(namespace, key_data, value)
        
        result = cache.get(namespace, key_data)
        assert result == value

    @given(
        entries=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=10),
                st.text(min_size=1, max_size=20)
            ),
            min_size=1,
            max_size=10,
            unique_by=lambda x: x[0]  # Unique by namespace
        )
    )
    def test_multiple_entries_independent(self, entries):
        """Multiple cache entries are independent."""
        cache = CacheManager()
        
        for namespace, value in entries:
            cache.set(namespace, {"key": 1}, value)
        
        for namespace, expected_value in entries:
            result = cache.get(namespace, {"key": 1})
            assert result == expected_value

    @given(
        namespace=st.text(min_size=1, max_size=20),
        key_data=st.dictionaries(
            st.text(min_size=1, max_size=10),
            st.text(min_size=1, max_size=20),
            min_size=1,
            max_size=3
        )
    )
    def test_nonexistent_key_returns_none(self, namespace, key_data):
        """Getting nonexistent key always returns None."""
        cache = CacheManager()
        
        result = cache.get(namespace, key_data)
        assert result is None

    @given(
        entries=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=10),
                st.text(min_size=1, max_size=20)
            ),
            min_size=1,
            max_size=5,
            unique=True
        )
    )
    def test_clear_removes_all_entries(self, entries):
        """Clearing cache removes all entries."""
        cache = CacheManager()
        
        for namespace, value in entries:
            cache.set(namespace, {"key": 1}, value)
        
        cache.clear()
        
        for namespace, _ in entries:
            result = cache.get(namespace, {"key": 1})
            assert result is None
