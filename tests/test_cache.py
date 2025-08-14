#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for cache.py
"""
import pytest
import time
import asyncio
from unittest.mock import patch, MagicMock
from utils.cache import CacheEntry, SimpleCache, CacheManager, cache_manager


class TestCacheEntry:
    """Test cases for CacheEntry class"""

    def test_init(self):
        """Test CacheEntry initialization"""
        entry = CacheEntry("test_value", 3600)
        assert entry.value == "test_value"
        assert entry.ttl == 3600
        assert entry.access_count == 0

    def test_is_expired_false(self):
        """Test is_expired when entry is not expired"""
        entry = CacheEntry("test_value", 3600)
        assert not entry.is_expired()

    def test_is_expired_true(self):
        """Test is_expired when entry is expired"""
        entry = CacheEntry("test_value", 0)
        assert entry.is_expired()

    def test_access(self):
        """Test access method updates access count and time"""
        entry = CacheEntry("test_value", 3600)
        original_count = entry.access_count
        entry.access()
        assert entry.access_count == original_count + 1

    def test_get_age(self):
        """Test get_age returns correct age in seconds"""
        entry = CacheEntry("test_value", 3600)
        age = entry.get_age()
        assert isinstance(age, (int, float))
        assert age >= 0


class TestSimpleCache:
    """Test cases for SimpleCache class"""

    @patch('utils.cache.config')
    def test_init_with_default_ttl(self, mock_config):
        """Test initialization with default TTL from config"""
        mock_config.performance.cache_ttl_seconds = 1800
        cache = SimpleCache()
        assert cache.ttl == 1800
        assert cache.max_size == 1000

    def test_init_with_custom_ttl_and_size(self):
        """Test initialization with custom TTL and max size"""
        cache = SimpleCache(ttl_seconds=7200, max_size=500)
        assert cache.ttl == 7200
        assert cache.max_size == 500

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        """Test basic set and get operations"""
        cache = SimpleCache(ttl_seconds=3600)
        await cache.set("key1", "value1")
        value = await cache.get("key1")
        assert value == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist"""
        cache = SimpleCache(ttl_seconds=3600)
        value = await cache.get("nonexistent")
        assert value is None
        assert cache.stats["misses"] == 1

    @pytest.mark.asyncio
    async def test_set_overwrites_existing(self):
        """Test that set overwrites existing key"""
        cache = SimpleCache(ttl_seconds=3600)
        await cache.set("key1", "value1")
        await cache.set("key1", "value2")
        value = await cache.get("key1")
        assert value == "value2"

    @pytest.mark.asyncio
    async def test_get_expired_entry(self):
        """Test that expired entries are removed and not returned"""
        cache = SimpleCache(ttl_seconds=0)
        await cache.set("key1", "value1")
        value = await cache.get("key1")
        assert value is None
        assert cache.stats["expired"] == 1

    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        """Test LRU eviction when max size is reached"""
        cache = SimpleCache(ttl_seconds=3600, max_size=2)
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")
        assert "key1" not in cache.cache
        assert cache.stats["evictions"] == 1

    @pytest.mark.asyncio
    async def test_delete_existing_key(self):
        """Test deleting an existing key"""
        cache = SimpleCache(ttl_seconds=3600)
        await cache.set("key1", "value1")
        result = await cache.delete("key1")
        assert result is True
        assert "key1" not in cache.cache

    @pytest.mark.asyncio
    async def test_clear(self):
        """Test clearing all cache entries"""
        cache = SimpleCache(ttl_seconds=3600)
        await cache.set("key1", "value1")
        await cache.clear()
        assert len(cache.cache) == 0

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting cache statistics"""
        cache = SimpleCache(ttl_seconds=3600)
        await cache.set("key1", "value1")
        await cache.get("key1")
        stats = await cache.get_stats()
        assert stats["hits"] == 1
        assert stats["size"] == 1

    @pytest.mark.asyncio
    async def test_exists_true(self):
        """Test exists returns True for existing non-expired key"""
        cache = SimpleCache(ttl_seconds=3600)
        await cache.set("key1", "value1")
        exists = await cache.exists("key1")
        assert exists is True

    @pytest.mark.asyncio
    async def test_touch_true(self):
        """Test touch returns True for existing non-expired key"""
        cache = SimpleCache(ttl_seconds=3600)
        await cache.set("key1", "value1")
        result = await cache.touch("key1")
        assert result is True

    @pytest.mark.asyncio
    async def test_get_with_metadata(self):
        """Test getting value with metadata"""
        cache = SimpleCache(ttl_seconds=3600)
        await cache.set("key1", "value1")
        metadata = await cache.get_with_metadata("key1")
        assert metadata is not None
        assert metadata["value"] == "value1"

    @pytest.mark.asyncio
    async def test_edge_case_none_value(self):
        """Test edge case with None value"""
        cache = SimpleCache(ttl_seconds=3600)
        await cache.set("key1", None)
        value = await cache.get("key1")
        assert value is None

    @pytest.mark.asyncio
    async def test_edge_case_empty_string_value(self):
        """Test edge case with empty string value"""
        cache = SimpleCache(ttl_seconds=3600)
        await cache.set("key1", "")
        value = await cache.get("key1")
        assert value == ""

    @pytest.mark.asyncio
    async def test_edge_case_unicode_key(self):
        """Test edge case with unicode key"""
        cache = SimpleCache(ttl_seconds=3600)
        unicode_key = "کلید_فارسی_۱۲۳"
        await cache.set(unicode_key, "unicode_value")
        value = await cache.get(unicode_key)
        assert value == "unicode_value"

    @pytest.mark.asyncio
    async def test_concurrent_access(self):
        """Test that cache handles concurrent access correctly"""
        cache = SimpleCache(ttl_seconds=3600)

        async def concurrent_operations():
            await cache.set(f"key_{asyncio.current_task().get_name()}", "value")
            await cache.get(f"key_{asyncio.current_task().get_name()}")

        tasks = [asyncio.create_task(concurrent_operations()) for _ in range(10)]
        await asyncio.gather(*tasks)
        assert len(await cache.get_keys()) == 10


class TestCacheManager:
    """Test cases for CacheManager class"""

    def test_init(self):
        """Test CacheManager initialization"""
        manager = CacheManager()
        assert manager.caches == {}
        assert isinstance(manager._default_cache, SimpleCache)

    def test_get_cache_new(self):
        """Test getting a new cache instance"""
        manager = CacheManager()
        cache = manager.get_cache("test_cache")
        assert isinstance(cache, SimpleCache)
        assert "test_cache" in manager.caches

    @pytest.mark.asyncio
    async def test_clear_all(self):
        """Test clearing all caches"""
        manager = CacheManager()
        cache1 = manager.get_cache("cache1")
        await cache1.set("key1", "value1")
        await manager.clear_all()
        assert len(await cache1.get_keys()) == 0

    @pytest.mark.asyncio
    async def test_get_all_stats(self):
        """Test getting statistics for all caches"""
        manager = CacheManager()
        cache1 = manager.get_cache("cache1")
        await cache1.set("key1", "value1")
        stats = await manager.get_all_stats()
        assert "cache1" in stats
        assert "default" in stats


class TestCacheManagerSingleton:
    """Test cases for the singleton cache_manager instance"""

    def test_singleton_instance(self):
        """Test that cache_manager is a singleton instance"""
        assert cache_manager is not None
        assert isinstance(cache_manager, CacheManager)

    @pytest.mark.asyncio
    async def test_singleton_operations(self):
        """Test that singleton instance can perform operations"""
        cache = cache_manager.get_cache("test")
        await cache.set("key1", "value1")
        value = await cache.get("key1")
        assert value == "value1"
