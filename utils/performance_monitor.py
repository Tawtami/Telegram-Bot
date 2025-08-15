#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced performance monitoring for Ostad Hatami Bot
"""

import time
import asyncio
import logging
import statistics
from typing import Dict, List, Any, Optional, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from config import config

# Expose ENGINE at module level so tests can patch it directly
try:
    from database.db import ENGINE as _DB_ENGINE
except Exception:
    _DB_ENGINE = None

# Module-level reference used by get_stats and tests
ENGINE = _DB_ENGINE

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a handler or operation"""

    handler_name: str
    total_requests: int = 0
    total_duration: float = 0.0
    min_duration: float = float("inf")
    max_duration: float = 0.0
    durations: deque = field(default_factory=lambda: deque(maxlen=1000))
    request_timestamps: deque = field(default_factory=lambda: deque(maxlen=3000))
    error_count: int = 0
    last_request: Optional[float] = None
    avg_duration: float = 0.0
    median_duration: float = 0.0
    p95_duration: float = 0.0
    p99_duration: float = 0.0

    def add_request(self, duration: float, timestamp: Optional[float] = None):
        """Add a request with its duration"""
        if timestamp is None:
            timestamp = time.time()

        self.total_requests += 1
        self.total_duration += duration
        self.last_request = timestamp

        # Update min/max
        if duration < self.min_duration:
            self.min_duration = duration
        if duration > self.max_duration:
            self.max_duration = duration

        # Add to durations list and timestamps
        self.durations.append(duration)
        self.request_timestamps.append(timestamp)

        # Update statistics
        self._update_statistics()

    def add_error(self):
        """Increment error count"""
        self.error_count += 1

    def _update_statistics(self):
        """Update calculated statistics"""
        if self.durations:
            durations_list = list(self.durations)
            self.avg_duration = statistics.mean(durations_list)

            if len(durations_list) >= 2:
                self.median_duration = statistics.median(durations_list)

                # Calculate percentiles indices to match tests' expectations
                sorted_durations = sorted(durations_list)
                n = len(sorted_durations)
                # For n=5, 0.95*n = 4.75 => index 4; 0.99*n = 4.95 => index 4
                # Use int() which floors, then clamp
                p95_index = max(0, min(n - 1, int(n * 0.95)))
                p99_index = max(0, min(n - 1, int(n * 0.99)))

                self.p95_duration = sorted_durations[p95_index]
                self.p99_duration = sorted_durations[p99_index]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "handler_name": self.handler_name,
            "total_requests": self.total_requests,
            "total_duration": round(self.total_duration, 4),
            "min_duration": (
                round(self.min_duration, 4) if self.min_duration != float("inf") else 0
            ),
            "max_duration": (
                round(self.max_duration, 4) if self.max_duration != float("-inf") else 0
            ),
            "avg_duration": round(self.avg_duration, 4),
            "median_duration": round(self.median_duration, 4),
            "p95_duration": round(self.p95_duration, 4),
            "p99_duration": round(self.p99_duration, 4),
            "error_count": self.error_count,
            "error_rate": (
                round((self.error_count / self.total_requests * 100), 2)
                if self.total_requests > 0
                else 0
            ),
            "last_request": self.last_request,
            "requests_per_minute": self._calculate_rpm(),
        }

    def _calculate_rpm(self) -> float:
        """Calculate requests per minute based on timestamps in the last 60s"""
        if not self.last_request or not self.request_timestamps:
            return 0.0

        cutoff_time = time.time() - 60.0
        # Remove timestamps older than 60s
        while self.request_timestamps and self.request_timestamps[0] < cutoff_time:
            self.request_timestamps.popleft()
        return float(len(self.request_timestamps))


@dataclass
class AlertThreshold:
    """Alert threshold configuration"""

    metric: str
    threshold: float
    operator: str  # 'gt', 'lt', 'eq'
    duration_seconds: int = 60  # Duration to check
    message: str = ""


class PerformanceMonitor:
    """Enhanced performance monitoring with alerts and detailed metrics"""

    def __init__(self):
        self.metrics: Dict[str, PerformanceMetrics] = defaultdict(lambda: PerformanceMetrics(""))
        self.user_activity: Dict[int, Dict[str, Any]] = defaultdict(dict)
        self.system_metrics: Dict[str, Any] = {}
        self.counters: Dict[str, int] = defaultdict(int)
        self.hourly_counters: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        self.alerts: List[Dict[str, Any]] = []
        self.alert_handlers: List[Callable] = []
        self._lock = asyncio.Lock()
        self._start_time = time.time()

        # Alert thresholds
        self.thresholds = [
            AlertThreshold(
                "avg_duration",
                2.0,
                "gt",
                300,
                "Average response time exceeded 2 seconds",
            ),
            AlertThreshold("error_rate", 5.0, "gt", 300, "Error rate exceeded 5%"),
            AlertThreshold("requests_per_minute", 100, "gt", 60, "High request rate detected"),
        ]

    async def log_request_time(
        self, handler_name: str, duration: float, user_id: Optional[int] = None
    ):
        """Log request time with async locking"""
        async with self._lock:
            self._log_request_time_sync(handler_name, duration, user_id)

    def _log_request_time_sync(
        self, handler_name: str, duration: float, user_id: Optional[int] = None
    ):
        """Synchronous request time logging"""
        # Update handler metrics
        if handler_name not in self.metrics:
            self.metrics[handler_name] = PerformanceMetrics(handler_name)

        # Preserve negative durations (tests expect exact values), do not clamp
        self.metrics[handler_name].add_request(duration)

        # Log slow requests
        if duration > 1.0:
            logger.warning(f"Slow request: {handler_name} took {duration:.2f}s")

        # Update user activity
        if user_id:
            if user_id not in self.user_activity:
                self.user_activity[user_id] = {
                    "first_seen": time.time(),
                    "last_seen": time.time(),
                    "request_count": 0,
                    "total_duration": 0.0,
                }

            user_data = self.user_activity[user_id]
            user_data["last_seen"] = time.time()
            user_data["request_count"] += 1
            user_data["total_duration"] += duration

    async def log_error(
        self,
        error_type: str,
        handler_name: Optional[str] = None,
        user_id: Optional[int] = None,
    ):
        """Log error with async locking"""
        async with self._lock:
            self._log_error_sync(error_type, handler_name, user_id)

    def _log_error_sync(
        self,
        error_type: str,
        handler_name: Optional[str] = None,
        user_id: Optional[int] = None,
    ):
        """Synchronous error logging"""
        if handler_name and handler_name in self.metrics:
            self.metrics[handler_name].add_error()

        # Log error
        logger.error(f"Error [{error_type}] in {handler_name or 'unknown'}")

    async def log_user_activity(self, user_id: int, activity_type: str = "request"):
        """Log user activity"""
        async with self._lock:
            if user_id not in self.user_activity:
                self.user_activity[user_id] = {
                    "first_seen": time.time(),
                    "last_seen": time.time(),
                    "request_count": 0,
                    "total_duration": 0.0,
                    "activities": defaultdict(int),
                }

            self.user_activity[user_id]["last_seen"] = time.time()
            self.user_activity[user_id]["activities"][activity_type] += 1

    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        async with self._lock:
            # Calculate system-wide metrics
            total_requests = sum(m.total_requests for m in self.metrics.values())
            total_errors = sum(m.error_count for m in self.metrics.values())
            total_duration = sum(m.total_duration for m in self.metrics.values())

            # Calculate averages
            avg_response_time = total_duration / total_requests if total_requests > 0 else 0
            error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0

            # Get uptime
            uptime_seconds = time.time() - self._start_time
            uptime_hours = uptime_seconds / 3600

            # Get active users
            active_users = len(
                [
                    user_id
                    for user_id, data in self.user_activity.items()
                    if time.time() - data["last_seen"] < 3600  # Active in last hour
                ]
            )

            # Aggregate hourly counters (last hour)
            current_hour = int(time.time() // 3600)
            hourly_summary = {}
            for name, buckets in self.hourly_counters.items():
                hourly_summary[name] = buckets.get(current_hour, 0)

            stats = {
                "system": {
                    "uptime_hours": round(uptime_hours, 2),
                    "total_requests": total_requests,
                    "total_errors": total_errors,
                    "avg_response_time": round(avg_response_time, 4),
                    "error_rate_percent": round(error_rate, 2),
                    "active_users": active_users,
                    "total_users": len(self.user_activity),
                },
                "counters": dict(self.counters),
                "handlers": {name: metrics.to_dict() for name, metrics in self.metrics.items()},
                "hourly": hourly_summary,
                "alerts": self.alerts[-10:],  # Last 10 alerts
                "timestamp": time.time(),
            }
            # DB health light probe (supports test patching of module-level ENGINE)
            try:
                if ENGINE is not None:
                    with ENGINE.connect() as conn:
                        conn.exec_driver_sql("SELECT 1")
                    stats["db"] = {"ok": True}
                else:
                    stats["db"] = {"ok": False, "error": "ENGINE not available"}
            except Exception as e:
                stats["db"] = {"ok": False, "error": str(e)}
            return stats

    async def get_handler_stats(self, handler_name: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific handler"""
        async with self._lock:
            if handler_name in self.metrics:
                return self.metrics[handler_name].to_dict()
            return None

    async def get_user_stats(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific user"""
        async with self._lock:
            if user_id in self.user_activity:
                data = self.user_activity[user_id].copy()
                data["avg_duration"] = (
                    data["total_duration"] / data["request_count"]
                    if data["request_count"] > 0
                    else 0
                )
                return data
            return None

    async def check_alerts(self):
        """Check for alert conditions"""
        async with self._lock:
            for threshold in self.thresholds:
                for handler_name, metrics in self.metrics.items():
                    value = getattr(metrics, threshold.metric, 0)

                    # Check threshold condition
                    triggered = False
                    if threshold.operator == "gt" and value > threshold.threshold:
                        triggered = True
                    elif threshold.operator == "lt" and value < threshold.threshold:
                        triggered = True
                    elif threshold.operator == "eq" and value == threshold.threshold:
                        triggered = True

                    if triggered:
                        alert = {
                            "timestamp": time.time(),
                            "handler": handler_name,
                            "metric": threshold.metric,
                            "value": value,
                            "threshold": threshold.threshold,
                            "message": threshold.message,
                        }

                        self.alerts.append(alert)

                        # Call alert handlers
                        for handler in self.alert_handlers:
                            try:
                                await handler(alert)
                            except Exception as e:
                                logger.error(f"Error in alert handler: {e}")

    async def add_alert_handler(self, handler: Callable):
        """Add custom alert handler"""
        self.alert_handlers.append(handler)

    async def clear_old_data(self, max_age_hours: int = 24):
        """Clear old performance data"""
        async with self._lock:
            cutoff_time = time.time() - (max_age_hours * 3600)

            # Clear old user activity
            old_users = [
                user_id
                for user_id, data in self.user_activity.items()
                if data["last_seen"] < cutoff_time
            ]
            for user_id in old_users:
                del self.user_activity[user_id]

            # Clear old alerts
            self.alerts = [alert for alert in self.alerts if alert["timestamp"] > cutoff_time]

    async def reset_stats(self):
        """Reset all performance statistics"""
        async with self._lock:
            self.metrics.clear()
            self.user_activity.clear()
            self.alerts.clear()
            self._start_time = time.time()

    def increment_counter(self, name: str, increment: int = 1):
        self.counters[name] += increment

    def increment_hourly(self, name: str, increment: int = 1):
        hour = int(time.time() // 3600)
        self.hourly_counters[name][hour] += increment


# Global performance monitor instance
monitor = PerformanceMonitor()
