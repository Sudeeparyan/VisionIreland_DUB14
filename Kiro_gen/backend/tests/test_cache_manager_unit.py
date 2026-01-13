"""Unit tests for cache manager."""

import pytest
import time

from src.processing.cache_manager import CacheManager


class TestCacheManager:
    """Test suite for CacheManager"""

    @pytest.fixture
    def cache(self):
        """Create a CacheManager"""
        return CacheManager(max_size=100)

    def test_set_and_get(self, cache):
        """Test setting and getting cache values"""
        cache.set("bedrock", {"image": "test.jpg"}, {"analysis": "result"})
        
        result = cache.get("bedrock", {"image": "test.jpg"})
        assert result == {"analysis": "result"}

    def test_get_nonexistent_key(self, cache):
        """Test getting nonexistent key returns None"""
        result = cache.get("bedrock", {"image": "nonexistent.jpg"})
        assert result is None

    def test_cache_expiration(self, cache):
        """Test cache entry expiration"""
        cache.set("bedrock", {"image": "test.jpg"}, {"analysis": "result"}, ttl_seconds=1)
        
        result = cache.get("bedrock", {"image": "test.jpg"})
        assert result == {"analysis": "result"}
        
        time.sleep(1.1)
        result = cache.get("bedrock", {"image": "test.jpg"})
        assert result is None

    def test_cache_eviction_lru(self, cache):
        """Test LRU eviction when cache is full"""
        cache.max_size = 3
        
        cache.set("ns", {"key": 1}, "value1")
        cache.set("ns", {"key": 2}, "value2")
        cache.set("ns", {"key": 3}, "value3")
        
        # Access first entry to increase its access count
        cache.get("ns", {"key": 1})
        
        # Add fourth entry, should evict least recently used (key 2)
        cache.set("ns", {"key": 4}, "value4")
        
        assert cache.get("ns", {"key": 1}) == "value1"
        assert cache.get("ns", {"key": 2}) is None
        assert cache.get("ns", {"key": 3}) == "value3"
        assert cache.get("ns", {"key": 4}) == "value4"

    def test_clear_cache(self, cache):
        """Test clearing cache"""
        cache.set("ns", {"key": 1}, "value1")
        cache.set("ns", {"key": 2}, "value2")
        
        cache.clear()
        
        assert cache.get("ns", {"key": 1}) is None
        assert cache.get("ns", {"key": 2}) is None

    def test_get_stats(self, cache):
        """Test getting cache statistics"""
        cache.set("ns", {"key": 1}, "value1")
        cache.set("ns", {"key": 2}, "value2")
        
        stats = cache.get_stats()
        assert stats['total_entries'] == 2
        assert stats['max_size'] == 100
        assert stats['utilization'] == 0.02

    def test_cleanup_expired(self, cache):
        """Test cleaning up expired entries"""
        cache.set("ns", {"key": 1}, "value1", ttl_seconds=1)
        cache.set("ns", {"key": 2}, "value2", ttl_seconds=3600)
        
        time.sleep(1.1)
        
        removed = cache.cleanup_expired()
        assert removed == 1
        assert cache.get("ns", {"key": 1}) is None
        assert cache.get("ns", {"key": 2}) == "value2"

    def test_different_namespaces(self, cache):
        """Test different cache namespaces"""
        cache.set("bedrock", {"image": "test.jpg"}, "bedrock_result")
        cache.set("polly", {"text": "hello"}, "polly_result")
        
        assert cache.get("bedrock", {"image": "test.jpg"}) == "bedrock_result"
        assert cache.get("polly", {"text": "hello"}) == "polly_result"

    def test_cache_key_generation(self, cache):
        """Test cache key generation consistency"""
        data = {"image": "test.jpg", "model": "claude"}
        
        cache.set("bedrock", data, "result1")
        result = cache.get("bedrock", data)
        
        assert result == "result1"
