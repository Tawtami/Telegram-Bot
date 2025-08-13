#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced caching system for Ostad Hatami Bot
"""

import time
import asyncio
import logging
from typing import Any, Optional, Dict, List
from collections import OrderedDict
from config import config

logger = logging.getLogger(__name__)


class CacheEntry:
    """Cache entry with metadata"""

    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
        self.access_count = 0
        self.last_accessed = time.time()

    def is_expired(self) -> bool:
        """Check if entry is expired"""
        return time.time() - self.created_at > self.ttl

    def access(self):
        """Record access to this entry"""
        self.access_count += 1
        self.last_accessed = time.time()

    def get_age(self) -> float:
        """Get age of entry in seconds"""
        return time.time() - self.created_at


class SimpleCache:
    """Enhanced in-memory cache with TTL and LRU eviction"""

    def __init__(self, ttl_seconds: Optional[int] = None, max_size: int = 1000):
        self.ttl = ttl_seconds or config.performance.cache_ttl_seconds
        self.max_size = max_size
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = {"hits": 0, "misses": 0, "evictions": 0, "expired": 0}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with async locking"""
        async with self._lock:
            return self._get_sync(key)

    def _get_sync(self, key: str) -> Optional[Any]:
        """Synchronous get operation"""
        if key in self.cache:
            entry = self.cache[key]

            if entry.is_expired():
                # Remove expired entry
                del self.cache[key]
                self.stats["expired"] += 1
                self.stats["misses"] += 1
                return None

            # Record access and move to end (LRU)
            entry.access()
            self.cache.move_to_end(key)
            self.stats["hits"] += 1
            return entry.value

        self.stats["misses"] += 1
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with async locking"""
        async with self._lock:
            self._set_sync(key, value, ttl)

    def _set_sync(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Synchronous set operation"""
        # Remove existing entry if present
        if key in self.cache:
            del self.cache[key]

        # Check if we need to evict entries
        if len(self.cache) >= self.max_size:
            self._evict_lru()

        # Create new entry
        entry_ttl = ttl or self.ttl
        self.cache[key] = CacheEntry(value, entry_ttl)

    def _evict_lru(self):
        """Evict least recently used entry"""
        if self.cache:
            # Remove oldest entry (first in OrderedDict)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            self.stats["evictions"] += 1

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    async def clear(self) -> None:
        """Clear all cache entries"""
        async with self._lock:
            self.cache.clear()
            self.stats = {"hits": 0, "misses": 0, "evictions": 0, "expired": 0}

    async def clear_expired(self) -> int:
        """Clear expired entries and return count of cleared entries"""
        async with self._lock:
            expired_keys = [key for key, entry in self.cache.items() if entry.is_expired()]

            for key in expired_keys:
                del self.cache[key]
                self.stats["expired"] += 1

            return len(expired_keys)

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        async with self._lock:
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0

            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl,
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "evictions": self.stats["evictions"],
                "expired": self.stats["expired"],
                "hit_rate_percent": round(hit_rate, 2),
                "total_requests": total_requests,
            }

    async def get_keys(self) -> List[str]:
        """Get all cache keys"""
        async with self._lock:
            return list(self.cache.keys())

    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired"""
        async with self._lock:
            if key in self.cache:
                entry = self.cache[key]
                if not entry.is_expired():
                    return True
                else:
                    # Remove expired entry
                    del self.cache[key]
                    self.stats["expired"] += 1
            return False

    async def touch(self, key: str) -> bool:
        """Update access time for key (move to end of LRU)"""
        async with self._lock:
            if key in self.cache:
                entry = self.cache[key]
                if not entry.is_expired():
                    entry.access()
                    self.cache.move_to_end(key)
                    return True
                else:
                    del self.cache[key]
                    self.stats["expired"] += 1
            return False

    async def get_with_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value with metadata"""
        async with self._lock:
            if key in self.cache:
                entry = self.cache[key]

                if entry.is_expired():
                    del self.cache[key]
                    self.stats["expired"] += 1
                    return None

                entry.access()
                self.cache.move_to_end(key)
                self.stats["hits"] += 1

                return {
                    "value": entry.value,
                    "created_at": entry.created_at,
                    "last_accessed": entry.last_accessed,
                    "access_count": entry.access_count,
                    "age_seconds": entry.get_age(),
                    "ttl_seconds": entry.ttl,
                }

            self.stats["misses"] += 1
            return None


class CacheManager:
    """Global cache manager with multiple cache instances"""

    def __init__(self):
        self.caches: Dict[str, SimpleCache] = {}
        self._default_cache = SimpleCache()

    def get_cache(self, name: str = "default") -> SimpleCache:
        """Get or create cache instance"""
        if name not in self.caches:
            self.caches[name] = SimpleCache()
        return self.caches[name]

    async def clear_all(self):
        """Clear all caches"""
        for cache in self.caches.values():
            await cache.clear()
        await self._default_cache.clear()

    async def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all caches"""
        stats = {}
        for name, cache in self.caches.items():
            stats[name] = await cache.get_stats()
        stats["default"] = await self._default_cache.get_stats()
        return stats


# Global cache manager instance
cache_manager = CacheManager()
