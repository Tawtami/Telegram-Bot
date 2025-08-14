#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for performance_monitor.py
"""
import pytest
import time
import asyncio
import statistics
from unittest.mock import patch, MagicMock, AsyncMock
from collections import deque
from utils.performance_monitor import (
    PerformanceMetrics, AlertThreshold, PerformanceMonitor, monitor
)


class TestPerformanceMetrics:
    """Test cases for PerformanceMetrics class"""

    def test_init(self):
        """Test PerformanceMetrics initialization"""
        metrics = PerformanceMetrics("test_handler")
        
        assert metrics.handler_name == "test_handler"
        assert metrics.total_requests == 0
        assert metrics.total_duration == 0.0
        assert metrics.min_duration == float("inf")
        assert metrics.max_duration == 0.0
        assert isinstance(metrics.durations, deque)
        assert isinstance(metrics.request_timestamps, deque)
        assert metrics.error_count == 0
        assert metrics.last_request is None
        assert metrics.avg_duration == 0.0
        assert metrics.median_duration == 0.0
        assert metrics.p95_duration == 0.0
        assert metrics.p99_duration == 0.0

    def test_add_request(self):
        """Test adding a request"""
        metrics = PerformanceMetrics("test_handler")
        
        # Add first request
        metrics.add_request(1.5)
        
        assert metrics.total_requests == 1
        assert metrics.total_duration == 1.5
        assert metrics.min_duration == 1.5
        assert metrics.max_duration == 1.5
        assert len(metrics.durations) == 1
        assert len(metrics.request_timestamps) == 1
        assert metrics.last_request is not None
        
        # Add second request
        metrics.add_request(2.5)
        
        assert metrics.total_requests == 2
        assert metrics.total_duration == 4.0
        assert metrics.min_duration == 1.5
        assert metrics.max_duration == 2.5
        assert len(metrics.durations) == 2

    def test_add_request_with_timestamp(self):
        """Test adding request with custom timestamp"""
        metrics = PerformanceMetrics("test_handler")
        custom_timestamp = 1234567890.0
        
        metrics.add_request(1.0, custom_timestamp)
        
        assert metrics.last_request == custom_timestamp
        assert metrics.request_timestamps[0] == custom_timestamp

    def test_add_request_updates_statistics(self):
        """Test that adding requests updates statistics"""
        metrics = PerformanceMetrics("test_handler")
        
        # Add multiple requests
        durations = [1.0, 2.0, 3.0, 4.0, 5.0]
        for duration in durations:
            metrics.add_request(duration)
        
        # Check statistics
        assert metrics.avg_duration == statistics.mean(durations)
        assert metrics.median_duration == statistics.median(durations)
        assert metrics.p95_duration == 4.0  # 5th element (0.95 * 5 = 4.75, index 4)
        assert metrics.p99_duration == 5.0  # 5th element (0.99 * 5 = 4.95, index 4)

    def test_add_request_edge_cases(self):
        """Test edge cases for adding requests"""
        metrics = PerformanceMetrics("test_handler")
        
        # Test zero duration
        metrics.add_request(0.0)
        assert metrics.min_duration == 0.0
        assert metrics.max_duration == 0.0
        
        # Test negative duration (should work but might not be realistic)
        metrics.add_request(-1.0)
        assert metrics.min_duration == -1.0
        assert metrics.max_duration == 0.0

    def test_add_error(self):
        """Test adding an error"""
        metrics = PerformanceMetrics("test_handler")
        
        assert metrics.error_count == 0
        
        metrics.add_error()
        assert metrics.error_count == 1
        
        metrics.add_error()
        assert metrics.error_count == 2

    def test_to_dict(self):
        """Test conversion to dictionary"""
        metrics = PerformanceMetrics("test_handler")
        metrics.add_request(1.5)
        metrics.add_error()
        
        result = metrics.to_dict()
        
        assert result["handler_name"] == "test_handler"
        assert result["total_requests"] == 1
        assert result["total_duration"] == 1.5
        assert result["min_duration"] == 1.5
        assert result["max_duration"] == 1.5
        assert result["error_count"] == 1
        assert result["error_rate"] == 100.0  # 1 error / 1 request * 100
        assert "last_request" in result
        assert "requests_per_minute" in result

    def test_to_dict_with_infinity(self):
        """Test to_dict with infinity values"""
        metrics = PerformanceMetrics("test_handler")
        
        result = metrics.to_dict()
        
        # min_duration should be 0 when infinity
        assert result["min_duration"] == 0

    def test_calculate_rpm_no_requests(self):
        """Test RPM calculation with no requests"""
        metrics = PerformanceMetrics("test_handler")
        
        rpm = metrics._calculate_rpm()
        assert rpm == 0.0

    def test_calculate_rpm_with_requests(self):
        """Test RPM calculation with requests"""
        metrics = PerformanceMetrics("test_handler")
        
        # Add requests in the last minute
        current_time = time.time()
        metrics.add_request(1.0, current_time)
        metrics.add_request(1.0, current_time - 30)  # 30 seconds ago
        
        rpm = metrics._calculate_rpm()
        assert rpm == 2.0

    def test_calculate_rpm_old_requests(self):
        """Test RPM calculation with old requests"""
        metrics = PerformanceMetrics("test_handler")
        
        # Add old requests
        old_time = time.time() - 120  # 2 minutes ago
        metrics.add_request(1.0, old_time)
        
        rpm = metrics._calculate_rpm()
        assert rpm == 0.0  # Old requests should be filtered out


class TestAlertThreshold:
    """Test cases for AlertThreshold class"""

    def test_init(self):
        """Test AlertThreshold initialization"""
        threshold = AlertThreshold(
            metric="avg_duration",
            threshold=2.0,
            operator="gt",
            duration_seconds=300,
            message="High response time"
        )
        
        assert threshold.metric == "avg_duration"
        assert threshold.threshold == 2.0
        assert threshold.operator == "gt"
        assert threshold.duration_seconds == 300
        assert threshold.message == "High response time"

    def test_init_with_defaults(self):
        """Test AlertThreshold initialization with defaults"""
        threshold = AlertThreshold("test_metric", 10.0, "lt")
        
        assert threshold.metric == "test_metric"
        assert threshold.threshold == 10.0
        assert threshold.operator == "lt"
        assert threshold.duration_seconds == 60  # Default
        assert threshold.message == ""  # Default


class TestPerformanceMonitor:
    """Test cases for PerformanceMonitor class"""

    def test_init(self):
        """Test PerformanceMonitor initialization"""
        monitor = PerformanceMonitor()
        
        assert isinstance(monitor.metrics, dict)
        assert isinstance(monitor.user_activity, dict)
        assert isinstance(monitor.system_metrics, dict)
        assert isinstance(monitor.counters, dict)
        assert isinstance(monitor.hourly_counters, dict)
        assert isinstance(monitor.alerts, list)
        assert isinstance(monitor.alert_handlers, list)
        assert isinstance(monitor._lock, asyncio.Lock)
        assert monitor._start_time > 0
        
        # Check default thresholds
        assert len(monitor.thresholds) == 3
        assert any(t.metric == "avg_duration" for t in monitor.thresholds)
        assert any(t.metric == "error_rate" for t in monitor.thresholds)
        assert any(t.metric == "requests_per_minute" for t in monitor.thresholds)

    @pytest.mark.asyncio
    async def test_log_request_time(self):
        """Test logging request time"""
        monitor = PerformanceMonitor()
        
        await monitor.log_request_time("test_handler", 1.5, user_id=123)
        
        # Check handler metrics
        assert "test_handler" in monitor.metrics
        metrics = monitor.metrics["test_handler"]
        assert metrics.total_requests == 1
        assert metrics.total_duration == 1.5
        
        # Check user activity
        assert 123 in monitor.user_activity
        user_data = monitor.user_activity[123]
        assert user_data["request_count"] == 1
        assert user_data["total_duration"] == 1.5

    @pytest.mark.asyncio
    async def test_log_request_time_slow_request(self):
        """Test logging slow request (triggers warning)"""
        monitor = PerformanceMonitor()
        
        with patch('utils.performance_monitor.logger') as mock_logger:
            await monitor.log_request_time("slow_handler", 2.5)
            
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args[0][0]
            assert "Slow request" in call_args
            assert "slow_handler" in call_args

    @pytest.mark.asyncio
    async def test_log_request_time_fast_request(self):
        """Test logging fast request (no warning)"""
        monitor = PerformanceMonitor()
        
        with patch('utils.performance_monitor.logger') as mock_logger:
            await monitor.log_request_time("fast_handler", 0.5)
            
            # Should not log warning for fast requests
            mock_logger.warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_log_request_time_existing_user(self):
        """Test logging request time for existing user"""
        monitor = PerformanceMonitor()
        
        # First request
        await monitor.log_request_time("test_handler", 1.0, user_id=123)
        
        # Second request
        await monitor.log_request_time("test_handler", 2.0, user_id=123)
        
        user_data = monitor.user_activity[123]
        assert user_data["request_count"] == 2
        assert user_data["total_duration"] == 3.0

    @pytest.mark.asyncio
    async def test_log_error(self):
        """Test logging error"""
        monitor = PerformanceMonitor()
        
        # Add some metrics first
        await monitor.log_request_time("test_handler", 1.0)
        
        with patch('utils.performance_monitor.logger') as mock_logger:
            await monitor.log_error("ValueError", "test_handler", user_id=123)
            
            # Check error count increased
            metrics = monitor.metrics["test_handler"]
            assert metrics.error_count == 1
            
            # Check error was logged
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "ValueError" in call_args
            assert "test_handler" in call_args

    @pytest.mark.asyncio
    async def test_log_error_no_handler(self):
        """Test logging error without handler"""
        monitor = PerformanceMonitor()
        
        with patch('utils.performance_monitor.logger') as mock_logger:
            await monitor.log_error("ValueError")
            
            # Should still log the error
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "unknown" in call_args

    @pytest.mark.asyncio
    async def test_log_user_activity(self):
        """Test logging user activity"""
        monitor = PerformanceMonitor()
        
        await monitor.log_user_activity(123, "login")
        
        assert 123 in monitor.user_activity
        user_data = monitor.user_activity[123]
        assert user_data["activities"]["login"] == 1
        assert "first_seen" in user_data
        assert "last_seen" in user_data

    @pytest.mark.asyncio
    async def test_log_user_activity_existing_user(self):
        """Test logging activity for existing user"""
        monitor = PerformanceMonitor()
        
        # First activity
        await monitor.log_user_activity(123, "login")
        
        # Second activity
        await monitor.log_user_activity(123, "logout")
        
        user_data = monitor.user_activity[123]
        assert user_data["activities"]["login"] == 1
        assert user_data["activities"]["logout"] == 1

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting comprehensive statistics"""
        monitor = PerformanceMonitor()
        
        # Add some data
        await monitor.log_request_time("handler1", 1.0, user_id=123)
        await monitor.log_request_time("handler2", 2.0, user_id=456)
        await monitor.log_error("ValueError", "handler1")
        
        stats = await monitor.get_stats()
        
        # Check system stats
        assert stats["system"]["total_requests"] == 2
        assert stats["system"]["total_errors"] == 1
        assert stats["system"]["total_users"] == 2
        assert "uptime_hours" in stats["system"]
        assert "avg_response_time" in stats["system"]
        assert "error_rate_percent" in stats["system"]
        
        # Check handlers
        assert "handler1" in stats["handlers"]
        assert "handler2" in stats["handlers"]
        
        # Check counters
        assert isinstance(stats["counters"], dict)
        
        # Check hourly
        assert isinstance(stats["hourly"], dict)
        
        # Check alerts
        assert isinstance(stats["alerts"], list)
        
        # Check timestamp
        assert "timestamp" in stats

    @pytest.mark.asyncio
    async def test_get_stats_no_data(self):
        """Test getting stats with no data"""
        monitor = PerformanceMonitor()
        
        stats = await monitor.get_stats()
        
        assert stats["system"]["total_requests"] == 0
        assert stats["system"]["total_errors"] == 0
        assert stats["system"]["total_users"] == 0
        assert stats["system"]["avg_response_time"] == 0
        assert stats["system"]["error_rate_percent"] == 0

    @pytest.mark.asyncio
    async def test_get_stats_db_health_check(self):
        """Test database health check in stats"""
        monitor = PerformanceMonitor()
        
        # Mock database connection
        with patch('utils.performance_monitor.ENGINE') as mock_engine:
            mock_conn = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn
            
            stats = await monitor.get_stats()
            
            assert "db" in stats
            assert stats["db"]["ok"] is True

    @pytest.mark.asyncio
    async def test_get_stats_db_health_check_failure(self):
        """Test database health check failure in stats"""
        monitor = PerformanceMonitor()
        
        # Mock database connection failure
        with patch('utils.performance_monitor.ENGINE') as mock_engine:
            mock_engine.connect.side_effect = Exception("Connection failed")
            
            stats = await monitor.get_stats()
            
            assert "db" in stats
            assert stats["db"]["ok"] is False
            assert "error" in stats["db"]

    @pytest.mark.asyncio
    async def test_get_handler_stats(self):
        """Test getting handler statistics"""
        monitor = PerformanceMonitor()
        
        # Add some data
        await monitor.log_request_time("test_handler", 1.5)
        
        stats = await monitor.get_handler_stats("test_handler")
        
        assert stats is not None
        assert stats["handler_name"] == "test_handler"
        assert stats["total_requests"] == 1
        assert stats["total_duration"] == 1.5

    @pytest.mark.asyncio
    async def test_get_handler_stats_nonexistent(self):
        """Test getting stats for non-existent handler"""
        monitor = PerformanceMonitor()
        
        stats = await monitor.get_handler_stats("nonexistent")
        
        assert stats is None

    @pytest.mark.asyncio
    async def test_get_user_stats(self):
        """Test getting user statistics"""
        monitor = PerformanceMonitor()
        
        # Add some data
        await monitor.log_request_time("test_handler", 2.0, user_id=123)
        
        stats = await monitor.get_user_stats(123)
        
        assert stats is not None
        assert stats["request_count"] == 1
        assert stats["total_duration"] == 2.0
        assert stats["avg_duration"] == 2.0

    @pytest.mark.asyncio
    async def test_get_user_stats_nonexistent(self):
        """Test getting stats for non-existent user"""
        monitor = PerformanceMonitor()
        
        stats = await monitor.get_user_stats(999)
        
        assert stats is None

    @pytest.mark.asyncio
    async def test_get_user_stats_zero_requests(self):
        """Test getting user stats with zero requests"""
        monitor = PerformanceMonitor()
        
        # Add user without requests
        await monitor.log_user_activity(123, "login")
        
        stats = await monitor.get_user_stats(123)
        
        assert stats is not None
        assert stats["request_count"] == 0
        assert stats["avg_duration"] == 0

    @pytest.mark.asyncio
    async def test_check_alerts(self):
        """Test checking for alerts"""
        monitor = PerformanceMonitor()
        
        # Add some data that should trigger alerts
        await monitor.log_request_time("slow_handler", 3.0)  # Exceeds 2.0 threshold
        
        # Mock alert handler
        alert_handler_called = False
        
        async def mock_alert_handler(alert):
            nonlocal alert_handler_called
            alert_handler_called = True
        
        await monitor.add_alert_handler(mock_alert_handler)
        
        await monitor.check_alerts()
        
        # Check that alert was created
        assert len(monitor.alerts) > 0
        
        # Check that alert handler was called
        assert alert_handler_called

    @pytest.mark.asyncio
    async def test_check_alerts_no_triggers(self):
        """Test checking alerts with no triggers"""
        monitor = PerformanceMonitor()
        
        # Add data that doesn't trigger alerts
        await monitor.log_request_time("fast_handler", 0.5)  # Below 2.0 threshold
        
        await monitor.check_alerts()
        
        # Should not create new alerts
        assert len(monitor.alerts) == 0

    @pytest.mark.asyncio
    async def test_check_alerts_handler_error(self):
        """Test alert checking when handler raises exception"""
        monitor = PerformanceMonitor()
        
        # Add data that triggers alert
        await monitor.log_request_time("slow_handler", 3.0)
        
        # Mock alert handler that raises exception
        async def failing_alert_handler(alert):
            raise Exception("Handler failed")
        
        await monitor.add_alert_handler(failing_alert_handler)
        
        with patch('utils.performance_monitor.logger') as mock_logger:
            await monitor.check_alerts()
            
            # Should log error from failing handler
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "Error in alert handler" in call_args

    @pytest.mark.asyncio
    async def test_add_alert_handler(self):
        """Test adding alert handler"""
        monitor = PerformanceMonitor()
        
        async def test_handler(alert):
            pass
        
        await monitor.add_alert_handler(test_handler)
        
        assert test_handler in monitor.alert_handlers

    @pytest.mark.asyncio
    async def test_clear_old_data(self):
        """Test clearing old data"""
        monitor = PerformanceMonitor()
        
        # Add some old data
        old_time = time.time() - (25 * 3600)  # 25 hours ago
        monitor.user_activity[123] = {"last_seen": old_time}
        monitor.alerts.append({"timestamp": old_time})
        
        await monitor.clear_old_data(max_age_hours=24)
        
        # Old data should be cleared
        assert 123 not in monitor.user_activity
        assert len(monitor.alerts) == 0

    @pytest.mark.asyncio
    async def test_reset_stats(self):
        """Test resetting statistics"""
        monitor = PerformanceMonitor()
        
        # Add some data
        await monitor.log_request_time("test_handler", 1.0, user_id=123)
        await monitor.log_error("ValueError", "test_handler")
        
        # Reset stats
        await monitor.reset_stats()
        
        # All data should be cleared
        assert len(monitor.metrics) == 0
        assert len(monitor.user_activity) == 0
        assert len(monitor.alerts) == 0
        
        # Start time should be updated
        assert monitor._start_time > 0

    def test_increment_counter(self):
        """Test incrementing counter"""
        monitor = PerformanceMonitor()
        
        monitor.increment_counter("test_counter")
        assert monitor.counters["test_counter"] == 1
        
        monitor.increment_counter("test_counter", 5)
        assert monitor.counters["test_counter"] == 6

    def test_increment_hourly(self):
        """Test incrementing hourly counter"""
        monitor = PerformanceMonitor()
        
        monitor.increment_hourly("test_hourly")
        
        current_hour = int(time.time() // 3600)
        assert monitor.hourly_counters["test_hourly"][current_hour] == 1

    def test_increment_hourly_multiple(self):
        """Test incrementing hourly counter multiple times"""
        monitor = PerformanceMonitor()
        
        monitor.increment_hourly("test_hourly", 3)
        
        current_hour = int(time.time() // 3600)
        assert monitor.hourly_counters["test_hourly"][current_hour] == 3


class TestPerformanceMonitorSingleton:
    """Test cases for the singleton monitor instance"""

    def test_singleton_instance(self):
        """Test that monitor is a singleton instance"""
        assert monitor is not None
        assert isinstance(monitor, PerformanceMonitor)

    @pytest.mark.asyncio
    async def test_singleton_operations(self):
        """Test that singleton instance can perform operations"""
        await monitor.log_request_time("test_handler", 1.0)
        
        stats = await monitor.get_stats()
        assert "test_handler" in stats["handlers"]


class TestPerformanceMonitorEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.asyncio
    async def test_concurrent_access(self):
        """Test concurrent access to performance monitor"""
        monitor = PerformanceMonitor()
        
        async def concurrent_operations():
            for i in range(10):
                await monitor.log_request_time(f"handler_{i}", 1.0, user_id=i)
                await monitor.log_error("TestError", f"handler_{i}")
        
        # Create multiple concurrent operations
        tasks = [concurrent_operations() for _ in range(5)]
        await asyncio.gather(*tasks)
        
        # Should handle concurrent access without errors
        stats = await monitor.get_stats()
        assert stats["system"]["total_requests"] == 50  # 5 tasks * 10 requests each

    @pytest.mark.asyncio
    async def test_large_numbers(self):
        """Test handling of large numbers"""
        monitor = PerformanceMonitor()
        
        # Add very large duration
        large_duration = 999999.99
        await monitor.log_request_time("test_handler", large_duration)
        
        stats = await monitor.get_handler_stats("test_handler")
        assert stats["max_duration"] == large_duration

    @pytest.mark.asyncio
    async def test_zero_duration(self):
        """Test handling of zero duration"""
        monitor = PerformanceMonitor()
        
        await monitor.log_request_time("test_handler", 0.0)
        
        stats = await monitor.get_handler_stats("test_handler")
        assert stats["min_duration"] == 0.0
        assert stats["max_duration"] == 0.0

    @pytest.mark.asyncio
    async def test_negative_duration(self):
        """Test handling of negative duration (edge case)"""
        monitor = PerformanceMonitor()
        
        await monitor.log_request_time("test_handler", -1.0)
        
        stats = await monitor.get_handler_stats("test_handler")
        assert stats["min_duration"] == -1.0
        assert stats["max_duration"] == -1.0

    def test_deque_limits(self):
        """Test that deques respect their size limits"""
        metrics = PerformanceMetrics("test_handler")
        
        # Add more than 1000 durations
        for i in range(1500):
            metrics.add_request(float(i))
        
        # Should respect maxlen=1000
        assert len(metrics.durations) == 1000
        assert len(metrics.request_timestamps) <= 3000  # maxlen=3000
