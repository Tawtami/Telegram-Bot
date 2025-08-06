#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced rate limiting system for Ostad Hatami Bot
"""

import time
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass
from config import config

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""

    max_requests: int
    window_seconds: int
    burst_size: int = 0  # Allow burst requests
    penalty_seconds: int = 0  # Penalty for violations


class RateLimitEntry:
    """Rate limit entry with request history"""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests = deque()
        self.violations = 0
        self.last_violation = 0
        self.blocked_until = 0

    def is_blocked(self) -> bool:
        """Check if user is currently blocked"""
        return time.time() < self.blocked_until

    def add_request(self, timestamp: float) -> bool:
        """Add a request and check if it's allowed"""
        now = timestamp

        # Check if user is blocked
        if self.is_blocked():
            return False

        # Remove old requests outside the window
        while self.requests and now - self.requests[0] > self.config.window_seconds:
            self.requests.popleft()

        # Check if request is allowed
        if len(self.requests) >= self.config.max_requests:
            self.violations += 1
            self.last_violation = now

            # Apply penalty if configured
            if self.config.penalty_seconds > 0:
                self.blocked_until = now + self.config.penalty_seconds

            return False

        # Add request
        self.requests.append(now)
        return True

    def get_stats(self) -> Dict:
        """Get rate limit statistics"""
        now = time.time()

        # Clean old requests
        while self.requests and now - self.requests[0] > self.config.window_seconds:
            self.requests.popleft()

        return {
            "current_requests": len(self.requests),
            "max_requests": self.config.max_requests,
            "window_seconds": self.config.window_seconds,
            "violations": self.violations,
            "is_blocked": self.is_blocked(),
            "blocked_until": self.blocked_until,
            "time_until_reset": max(
                0,
                (
                    self.config.window_seconds - (now - self.requests[0])
                    if self.requests
                    else 0
                ),
            ),
        }


class RateLimiter:
    """Enhanced rate limiter with multiple strategies and monitoring"""

    def __init__(self, default_config: Optional[RateLimitConfig] = None):
        self.default_config = default_config or RateLimitConfig(
            max_requests=config.performance.max_requests_per_minute, window_seconds=60
        )
        self.limits: Dict[str, RateLimitEntry] = {}
        self.stats = {
            "total_requests": 0,
            "allowed_requests": 0,
            "blocked_requests": 0,
            "unique_users": 0,
        }
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

    async def is_allowed(
        self, user_id: str, config: Optional[RateLimitConfig] = None
    ) -> bool:
        """Check if request is allowed for user"""
        async with self._lock:
            return self._is_allowed_sync(user_id, config)

    def _is_allowed_sync(
        self, user_id: str, config: Optional[RateLimitConfig] = None
    ) -> bool:
        """Synchronous check if request is allowed"""
        self.stats["total_requests"] += 1

        # Get or create rate limit entry
        if user_id not in self.limits:
            self.limits[user_id] = RateLimitEntry(config or self.default_config)
            self.stats["unique_users"] = len(self.limits)

        entry = self.limits[user_id]
        timestamp = time.time()

        # Check if request is allowed
        if entry.add_request(timestamp):
            self.stats["allowed_requests"] += 1
            return True
        else:
            self.stats["blocked_requests"] += 1
            return False

    async def get_user_stats(self, user_id: str) -> Optional[Dict]:
        """Get rate limit statistics for a specific user"""
        async with self._lock:
            if user_id in self.limits:
                return self.limits[user_id].get_stats()
            return None

    async def get_global_stats(self) -> Dict:
        """Get global rate limiting statistics"""
        async with self._lock:
            return {
                "total_requests": self.stats["total_requests"],
                "allowed_requests": self.stats["allowed_requests"],
                "blocked_requests": self.stats["blocked_requests"],
                "unique_users": self.stats["unique_users"],
                "active_limits": len(self.limits),
                "block_rate_percent": round(
                    (
                        (
                            self.stats["blocked_requests"]
                            / self.stats["total_requests"]
                            * 100
                        )
                        if self.stats["total_requests"] > 0
                        else 0
                    ),
                    2,
                ),
            }

    async def reset_user(self, user_id: str) -> bool:
        """Reset rate limit for a specific user"""
        async with self._lock:
            if user_id in self.limits:
                del self.limits[user_id]
                return True
            return False

    async def cleanup_old_entries(self, max_age_hours: int = 24) -> int:
        """Clean up old rate limit entries"""
        async with self._lock:
            now = time.time()
            max_age_seconds = max_age_hours * 3600

            old_entries = [
                user_id
                for user_id, entry in self.limits.items()
                if now - entry.last_violation > max_age_seconds and not entry.requests
            ]

            for user_id in old_entries:
                del self.limits[user_id]

            return len(old_entries)

    async def set_user_limit(self, user_id: str, config: RateLimitConfig) -> None:
        """Set custom rate limit for a specific user"""
        async with self._lock:
            self.limits[user_id] = RateLimitEntry(config)

    async def get_all_users(self) -> List[str]:
        """Get list of all users with rate limits"""
        async with self._lock:
            return list(self.limits.keys())

    async def start_cleanup_task(self, interval_seconds: int = 3600):
        """Start periodic cleanup task"""
        if self._cleanup_task and not self._cleanup_task.done():
            return

        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(interval_seconds)
                    cleaned = await self.cleanup_old_entries()
                    if cleaned > 0:
                        logger.info(f"Cleaned up {cleaned} old rate limit entries")
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in rate limiter cleanup: {e}")

        self._cleanup_task = asyncio.create_task(cleanup_loop())

    async def stop_cleanup_task(self):
        """Stop periodic cleanup task"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass


class MultiLevelRateLimiter:
    """Multi-level rate limiter for different types of requests"""

    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {}

        # Default limiters
        self.limiters["default"] = RateLimiter()
        self.limiters["registration"] = RateLimiter(
            RateLimitConfig(
                max_requests=5,  # 5 registration attempts per hour
                window_seconds=3600,
                penalty_seconds=1800,  # 30 minute penalty
            )
        )
        self.limiters["admin"] = RateLimiter(
            RateLimitConfig(
                max_requests=100, window_seconds=60  # 100 admin requests per minute
            )
        )

    async def is_allowed(self, user_id: str, level: str = "default") -> bool:
        """Check if request is allowed for user at specified level"""
        if level not in self.limiters:
            level = "default"
        return await self.limiters[level].is_allowed(user_id)

    async def get_stats(self, level: str = "default") -> Dict:
        """Get statistics for specified level"""
        if level not in self.limiters:
            level = "default"
        return await self.limiters[level].get_global_stats()

    async def get_all_stats(self) -> Dict[str, Dict]:
        """Get statistics for all levels"""
        stats = {}
        for level, limiter in self.limiters.items():
            stats[level] = await limiter.get_global_stats()
        return stats

    async def start_cleanup_tasks(self):
        """Start cleanup tasks for all limiters"""
        for limiter in self.limiters.values():
            await limiter.start_cleanup_task()


# Global rate limiter instances
rate_limiter = RateLimiter()
multi_rate_limiter = MultiLevelRateLimiter()
