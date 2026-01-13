"""Caching layer to minimize API calls to Bedrock and Polly."""

from dataclasses import dataclass, field
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a cached value."""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    ttl_seconds: int = 3600  # 1 hour default

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        expiry = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now() > expiry

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'key': self.key,
            'value': self.value,
            'created_at': self.created_at.isoformat(),
            'ttl_seconds': self.ttl_seconds,
        }


class CacheManager:
    """Manages caching of API responses."""

    def __init__(self, max_size: int = 1000):
        """Initialize cache manager.
        
        Args:
            max_size: Maximum number of cache entries
        """
        self.max_size = max_size
        self.cache: Dict[str, CacheEntry] = {}
        self.access_count: Dict[str, int] = {}

    def _generate_key(self, namespace: str, data: Any) -> str:
        """Generate cache key from namespace and data.
        
        Args:
            namespace: Cache namespace (e.g., 'bedrock_analysis', 'polly_voice')
            data: Data to hash
            
        Returns:
            Cache key
        """
        data_str = json.dumps(data, sort_keys=True, default=str)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()
        return f"{namespace}:{data_hash}"

    def get(self, namespace: str, data: Any) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            namespace: Cache namespace
            data: Data to look up
            
        Returns:
            Cached value or None if not found or expired
        """
        key = self._generate_key(namespace, data)
        entry = self.cache.get(key)

        if not entry:
            return None

        if entry.is_expired():
            del self.cache[key]
            self.access_count.pop(key, None)
            logger.debug(f"Cache entry expired: {key}")
            return None

        self.access_count[key] = self.access_count.get(key, 0) + 1
        logger.debug(f"Cache hit: {key}")
        return entry.value

    def set(self, namespace: str, data: Any, value: Any, ttl_seconds: int = 3600) -> None:
        """Set value in cache.
        
        Args:
            namespace: Cache namespace
            data: Data to cache
            value: Value to cache
            ttl_seconds: Time to live in seconds
        """
        key = self._generate_key(namespace, data)

        # Evict least recently used entry if cache is full
        if len(self.cache) >= self.max_size:
            self._evict_lru()

        entry = CacheEntry(key=key, value=value, ttl_seconds=ttl_seconds)
        self.cache[key] = entry
        self.access_count[key] = 0
        logger.debug(f"Cache set: {key}")

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self.cache:
            return

        lru_key = min(self.access_count, key=self.access_count.get)
        del self.cache[lru_key]
        del self.access_count[lru_key]
        logger.debug(f"Evicted LRU cache entry: {lru_key}")

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.access_count.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> dict:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        total_entries = len(self.cache)
        expired_entries = sum(1 for entry in self.cache.values() if entry.is_expired())

        return {
            'total_entries': total_entries,
            'expired_entries': expired_entries,
            'max_size': self.max_size,
            'utilization': total_entries / self.max_size if self.max_size > 0 else 0,
        }

    def cleanup_expired(self) -> int:
        """Remove all expired entries.
        
        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]

        for key in expired_keys:
            del self.cache[key]
            self.access_count.pop(key, None)

        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        return len(expired_keys)
