#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for rate_limiter.py
"""
import pytest
import time
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from utils.rate_limiter import (
    rate_limit_handler, RateLimitConfig, RateLimitEntry, RateLimiter, 
    MultiLevelRateLimiter, rate_limiter, multi_rate_limiter
)


class TestRateLimitConfig:
    """Test cases for RateLimitConfig dataclass"""

    def test_init(self):
        """Test RateLimitConfig initialization"""
        config = RateLimitConfig(
            max_requests=100,
            window_seconds=60,
            burst_size=10,
            penalty_seconds=30
        )
        
        assert config.max_requests == 100
        assert config.window_seconds == 60
        assert config.burst_size == 10
        assert config.penalty_seconds == 30

    def test_init_with_defaults(self):
        """Test RateLimitConfig initialization with default values"""
        config = RateLimitConfig(max_requests=50, window_seconds=30)
        
        assert config.max_requests == 50
        assert config.window_seconds == 30
        assert config.burst_size == 0
        assert config.penalty_seconds == 0


class TestRateLimitEntry:
    """Test cases for RateLimitEntry class"""

    def test_init(self):
        """Test RateLimitEntry initialization"""
        config = RateLimitConfig(max_requests=10, window_seconds=60)
        entry = RateLimitEntry(config)
        
        assert entry.config == config
        assert len(entry.requests) == 0
        assert entry.violations == 0
        assert entry.last_violation == 0.0
        assert entry.blocked_until == 0.0

    def test_is_blocked_false(self):
        """Test is_blocked when user is not blocked"""
        config = RateLimitConfig(max_requests=10, window_seconds=60)
        entry = RateLimitEntry(config)
        
        assert not entry.is_blocked()

    def test_is_blocked_true(self):
        """Test is_blocked when user is blocked"""
        config = RateLimitConfig(max_requests=10, window_seconds=60, penalty_seconds=30)
        entry = RateLimitEntry(config)
        
        # Set blocked_until to future time
        entry.blocked_until = time.time() + 60
        
        assert entry.is_blocked()

    def test_add_request_allowed(self):
        """Test add_request when request is allowed"""
        config = RateLimitConfig(max_requests=2, window_seconds=60)
        entry = RateLimitEntry(config)
        
        # First request should be allowed
        assert entry.add_request(time.time())
        assert len(entry.requests) == 1
        
        # Second request should be allowed
        assert entry.add_request(time.time())
        assert len(entry.requests) == 2

    def test_add_request_blocked(self):
        """Test add_request when request is blocked"""
        config = RateLimitConfig(max_requests=2, window_seconds=60)
        entry = RateLimitEntry(config)
        
        # Add two requests (at limit)
        entry.add_request(time.time())
        entry.add_request(time.time())
        
        # Third request should be blocked
        assert not entry.add_request(time.time())
        assert entry.violations == 1

    def test_add_request_with_penalty(self):
        """Test add_request with penalty configuration"""
        config = RateLimitConfig(max_requests=1, window_seconds=60, penalty_seconds=30)
        entry = RateLimitEntry(config)
        
        # First request allowed
        assert entry.add_request(time.time())
        
        # Second request blocked and penalty applied
        assert not entry.add_request(time.time())
        assert entry.violations == 1
        assert entry.blocked_until > time.time()

    def test_add_request_window_expiry(self):
        """Test add_request with window expiry"""
        config = RateLimitConfig(max_requests=1, window_seconds=1)
        entry = RateLimitEntry(config)
        
        # Add request
        entry.add_request(time.time())
        assert len(entry.requests) == 1
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Should be able to add another request
        assert entry.add_request(time.time())
        assert len(entry.requests) == 1  # Old request removed

    def test_get_stats(self):
        """Test get_stats method"""
        config = RateLimitConfig(max_requests=10, window_seconds=60)
        entry = RateLimitEntry(config)
        
        # Add some requests
        entry.add_request(time.time())
        entry.add_request(time.time())
        
        stats = entry.get_stats()
        
        assert stats["current_requests"] == 2
        assert stats["max_requests"] == 10
        assert stats["window_seconds"] == 60
        assert stats["violations"] == 0
        assert stats["is_blocked"] is False
        assert "time_until_reset" in stats


class TestRateLimiter:
    """Test cases for RateLimiter class"""

    @patch('utils.rate_limiter.config')
    def test_init_with_default_config(self, mock_config):
        """Test initialization with default config"""
        mock_config.performance.max_requests_per_minute = 30
        
        limiter = RateLimiter()
        
        assert limiter.default_config.max_requests == 30
        assert limiter.default_config.window_seconds == 60
        assert limiter.limits == {}
        assert limiter.stats["total_requests"] == 0

    def test_init_with_custom_config(self):
        """Test initialization with custom config"""
        custom_config = RateLimitConfig(max_requests=50, window_seconds=30)
        limiter = RateLimiter(custom_config)
        
        assert limiter.default_config == custom_config

    @pytest.mark.asyncio
    async def test_is_allowed_success(self):
        """Test successful rate limit check"""
        limiter = RateLimiter()
        
        result = await limiter.is_allowed("user123")
        
        assert result is True
        assert "user123" in limiter.limits

    @pytest.mark.asyncio
    async def test_is_allowed_blocked(self):
        """Test rate limit check when user is blocked"""
        config = RateLimitConfig(max_requests=1, window_seconds=60)
        limiter = RateLimiter(config)
        
        # First request allowed
        assert await limiter.is_allowed("user123")
        
        # Second request blocked
        assert not await limiter.is_allowed("user123")

    @pytest.mark.asyncio
    async def test_is_allowed_empty_user_id(self):
        """Test rate limit check with empty user ID"""
        limiter = RateLimiter()
        
        result = await limiter.is_allowed("")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_is_allowed_error_handling(self):
        """Test error handling in is_allowed"""
        limiter = RateLimiter()
        
        # Mock the sync method to raise an exception
        with patch.object(limiter, '_is_allowed_sync', side_effect=Exception("Test error")):
            with patch('utils.rate_limiter.logger') as mock_logger:
                result = await limiter.is_allowed("user123")
                
                # Should allow request on error
                assert result is True
                mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_allowed_custom_config(self):
        """Test rate limit check with custom config"""
        default_config = RateLimitConfig(max_requests=10, window_seconds=60)
        custom_config = RateLimitConfig(max_requests=1, window_seconds=60)
        
        limiter = RateLimiter(default_config)
        
        # First request with custom config
        assert await limiter.is_allowed("user123", custom_config)
        
        # Second request should be blocked
        assert not await limiter.is_allowed("user123", custom_config)

    @pytest.mark.asyncio
    async def test_is_allowed_config_update(self):
        """Test that config updates are applied"""
        config1 = RateLimitConfig(max_requests=1, window_seconds=60)
        config2 = RateLimitConfig(max_requests=2, window_seconds=60)
        
        limiter = RateLimiter(config1)
        
        # First request with config1
        assert await limiter.is_allowed("user123", config1)
        
        # Second request blocked with config1
        assert not await limiter.is_allowed("user123", config1)
        
        # First request with config2 should be allowed
        assert await limiter.is_allowed("user123", config2)

    @pytest.mark.asyncio
    async def test_get_user_stats(self):
        """Test getting user statistics"""
        limiter = RateLimiter()
        
        # Create a user entry
        await limiter.is_allowed("user123")
        
        stats = await limiter.get_user_stats("user123")
        
        assert stats is not None
        assert stats["current_requests"] == 1

    @pytest.mark.asyncio
    async def test_get_user_stats_nonexistent(self):
        """Test getting stats for non-existent user"""
        limiter = RateLimiter()
        
        stats = await limiter.get_user_stats("nonexistent")
        
        assert stats is None

    @pytest.mark.asyncio
    async def test_get_global_stats(self):
        """Test getting global statistics"""
        limiter = RateLimiter()
        
        # Make some requests
        await limiter.is_allowed("user1")
        await limiter.is_allowed("user2")
        
        stats = await limiter.get_global_stats()
        
        assert stats["total_requests"] >= 0
        assert stats["allowed_requests"] >= 0
        assert stats["blocked_requests"] >= 0
        assert stats["unique_users"] >= 0
        assert stats["active_limits"] >= 0
        assert "block_rate_percent" in stats

    @pytest.mark.asyncio
    async def test_reset_user(self):
        """Test resetting user rate limit"""
        limiter = RateLimiter()
        
        # Create a user entry
        await limiter.is_allowed("user123")
        assert "user123" in limiter.limits
        
        # Reset user
        result = await limiter.reset_user("user123")
        
        assert result is True
        assert "user123" not in limiter.limits

    @pytest.mark.asyncio
    async def test_reset_nonexistent_user(self):
        """Test resetting non-existent user"""
        limiter = RateLimiter()
        
        result = await limiter.reset_user("nonexistent")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_cleanup_old_entries(self):
        """Test cleaning up old entries"""
        limiter = RateLimiter()
        
        # Create some entries
        await limiter.is_allowed("user1")
        await limiter.is_allowed("user2")
        
        # Clean up old entries
        cleaned = await limiter.cleanup_old_entries(max_age_hours=0)
        
        # Should clean up entries older than 0 hours
        assert cleaned >= 0

    @pytest.mark.asyncio
    async def test_set_user_limit(self):
        """Test setting custom user limit"""
        limiter = RateLimiter()
        custom_config = RateLimitConfig(max_requests=5, window_seconds=30)
        
        await limiter.set_user_limit("user123", custom_config)
        
        assert "user123" in limiter.limits
        assert limiter.limits["user123"].config == custom_config

    @pytest.mark.asyncio
    async def test_get_all_users(self):
        """Test getting all users"""
        limiter = RateLimiter()
        
        # Create some users
        await limiter.is_allowed("user1")
        await limiter.is_allowed("user2")
        
        users = await limiter.get_all_users()
        
        assert "user1" in users
        assert "user2" in users
        assert len(users) == 2

    @pytest.mark.asyncio
    async def test_start_cleanup_task(self):
        """Test starting cleanup task"""
        limiter = RateLimiter()
        
        await limiter.start_cleanup_task(interval_seconds=1)
        
        assert limiter._cleanup_task is not None
        assert not limiter._cleanup_task.done()

    @pytest.mark.asyncio
    async def test_stop_cleanup_task(self):
        """Test stopping cleanup task"""
        limiter = RateLimiter()
        
        # Start cleanup task
        await limiter.start_cleanup_task(interval_seconds=1)
        
        # Stop cleanup task
        await limiter.stop_cleanup_task()
        
        assert limiter._cleanup_task is None or limiter._cleanup_task.done()


class TestMultiLevelRateLimiter:
    """Test cases for MultiLevelRateLimiter class"""

    def test_init(self):
        """Test MultiLevelRateLimiter initialization"""
        limiter = MultiLevelRateLimiter()
        
        assert "default" in limiter.limiters
        assert "registration" in limiter.limiters
        assert "admin" in limiter.limiters

    @pytest.mark.asyncio
    async def test_is_allowed_default_level(self):
        """Test rate limit check at default level"""
        limiter = MultiLevelRateLimiter()
        
        result = await limiter.is_allowed("user123", "default")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_is_allowed_registration_level(self):
        """Test rate limit check at registration level"""
        limiter = MultiLevelRateLimiter()
        
        result = await limiter.is_allowed("user123", "registration")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_is_allowed_admin_level(self):
        """Test rate limit check at admin level"""
        limiter = MultiLevelRateLimiter()
        
        result = await limiter.is_allowed("user123", "admin")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_is_allowed_unknown_level(self):
        """Test rate limit check at unknown level (should fallback to default)"""
        limiter = MultiLevelRateLimiter()
        
        result = await limiter.is_allowed("user123", "unknown_level")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_get_stats_default_level(self):
        """Test getting stats for default level"""
        limiter = MultiLevelRateLimiter()
        
        stats = await limiter.get_stats("default")
        
        assert "total_requests" in stats
        assert "allowed_requests" in stats

    @pytest.mark.asyncio
    async def test_get_stats_unknown_level(self):
        """Test getting stats for unknown level (should fallback to default)"""
        limiter = MultiLevelRateLimiter()
        
        stats = await limiter.get_stats("unknown_level")
        
        assert "total_requests" in stats

    @pytest.mark.asyncio
    async def test_get_all_stats(self):
        """Test getting stats for all levels"""
        limiter = MultiLevelRateLimiter()
        
        all_stats = await limiter.get_all_stats()
        
        assert "default" in all_stats
        assert "registration" in all_stats
        assert "admin" in all_stats

    @pytest.mark.asyncio
    async def test_start_cleanup_tasks(self):
        """Test starting cleanup tasks for all levels"""
        limiter = MultiLevelRateLimiter()
        
        await limiter.start_cleanup_tasks()
        
        # Check that cleanup tasks are started for all limiters
        for limiter_instance in limiter.limiters.values():
            assert limiter_instance._cleanup_task is not None


class TestRateLimitHandler:
    """Test cases for rate_limit_handler decorator"""

    @pytest.mark.asyncio
    async def test_rate_limit_handler_success(self):
        """Test successful rate limit handler"""
        @rate_limit_handler("default")
        async def test_handler(update, context):
            return "success"
        
        mock_update = MagicMock()
        mock_update.effective_user.id = 123
        mock_context = MagicMock()
        
        result = await test_handler(mock_update, mock_context)
        
        assert result == "success"

    @pytest.mark.asyncio
    async def test_rate_limit_handler_blocked(self):
        """Test rate limit handler when user is blocked"""
        @rate_limit_handler("default")
        async def test_handler(update, context):
            return "success"
        
        mock_update = MagicMock()
        mock_update.effective_user.id = 123
        mock_context = MagicMock()
        
        # Mock the rate limiter to block the user
        with patch('utils.rate_limiter.multi_rate_limiter') as mock_limiter:
            mock_limiter.is_allowed.return_value = False
            
            result = await test_handler(mock_update, mock_context)
            
            # Should return None when blocked
            assert result is None

    @pytest.mark.asyncio
    async def test_rate_limit_handler_error(self):
        """Test rate limit handler when rate limiting fails"""
        @rate_limit_handler("default")
        async def test_handler(update, context):
            return "success"
        
        mock_update = MagicMock()
        mock_update.effective_user.id = 123
        mock_context = MagicMock()
        
        # Mock the rate limiter to raise an exception
        with patch('utils.rate_limiter.multi_rate_limiter') as mock_limiter:
            mock_limiter.is_allowed.side_effect = Exception("Rate limiter error")
            
            result = await test_handler(mock_update, mock_context)
            
            # Should fall through to handler on error
            assert result == "success"

    @pytest.mark.asyncio
    async def test_rate_limit_handler_no_user_id(self):
        """Test rate limit handler when no user ID is available"""
        @rate_limit_handler("default")
        async def test_handler(update, context):
            return "success"
        
        mock_update = MagicMock()
        mock_update.effective_user = None  # No effective user
        mock_context = MagicMock()
        
        result = await test_handler(mock_update, mock_context)
        
        # Should fall through to handler
        assert result == "success"


class TestRateLimiterSingleton:
    """Test cases for the singleton rate_limiter instance"""

    def test_singleton_instance(self):
        """Test that rate_limiter is a singleton instance"""
        assert rate_limiter is not None
        assert isinstance(rate_limiter, RateLimiter)

    @pytest.mark.asyncio
    async def test_singleton_operations(self):
        """Test that singleton instance can perform operations"""
        result = await rate_limiter.is_allowed("test_user")
        assert result is True


class TestMultiRateLimiterSingleton:
    """Test cases for the singleton multi_rate_limiter instance"""

    def test_singleton_instance(self):
        """Test that multi_rate_limiter is a singleton instance"""
        assert multi_rate_limiter is not None
        assert isinstance(multi_rate_limiter, MultiLevelRateLimiter)

    @pytest.mark.asyncio
    async def test_singleton_operations(self):
        """Test that singleton instance can perform operations"""
        result = await multi_rate_limiter.is_allowed("test_user", "default")
        assert result is True
