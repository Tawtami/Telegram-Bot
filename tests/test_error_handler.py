#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for error_handler.py
"""
import pytest
import time
import asyncio
import logging
from unittest.mock import patch, MagicMock, AsyncMock
from utils.error_handler import (
    ErrorSeverity,
    ErrorCategory,
    ErrorInfo,
    ErrorHandler,
    error_handler,
    ptb_error_handler,
)


class TestErrorSeverity:
    """Test cases for ErrorSeverity enum"""

    def test_enum_values(self):
        """Test enum values are correct"""
        assert ErrorSeverity.LOW == "low"
        assert ErrorSeverity.MEDIUM == "medium"
        assert ErrorSeverity.HIGH == "high"
        assert ErrorSeverity.CRITICAL == "critical"


class TestErrorCategory:
    """Test cases for ErrorCategory enum"""

    def test_enum_values(self):
        """Test enum values are correct"""
        assert ErrorCategory.VALIDATION == "validation"
        assert ErrorCategory.NETWORK == "network"
        assert ErrorCategory.DATABASE == "database"
        assert ErrorCategory.AUTHENTICATION == "authentication"
        assert ErrorCategory.AUTHORIZATION == "authorization"
        assert ErrorCategory.SYSTEM == "system"
        assert ErrorCategory.USER_INPUT == "user_input"
        assert ErrorCategory.EXTERNAL_API == "external_api"
        assert ErrorCategory.UNKNOWN == "unknown"


class TestErrorInfo:
    """Test cases for ErrorInfo dataclass"""

    def test_init(self):
        """Test ErrorInfo initialization"""
        error_info = ErrorInfo(
            error_id="ERR_123",
            timestamp=1234567890.0,
            error_type="ValueError",
            error_message="Invalid input",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.VALIDATION,
            handler_name="test_handler",
            user_id=12345,
            stack_trace="traceback info",
            context={"key": "value"},
            resolved=False,
            resolution_time=None,
        )

        assert error_info.error_id == "ERR_123"
        assert error_info.timestamp == 1234567890.0
        assert error_info.error_type == "ValueError"
        assert error_info.error_message == "Invalid input"
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.category == ErrorCategory.VALIDATION
        assert error_info.handler_name == "test_handler"
        assert error_info.user_id == 12345
        assert error_info.stack_trace == "traceback info"
        assert error_info.context == {"key": "value"}
        assert error_info.resolved is False
        assert error_info.resolution_time is None

    def test_init_with_defaults(self):
        """Test ErrorInfo initialization with default values"""
        error_info = ErrorInfo(
            error_id="ERR_123",
            timestamp=1234567890.0,
            error_type="ValueError",
            error_message="Invalid input",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.VALIDATION,
        )

        assert error_info.handler_name is None
        assert error_info.user_id is None
        assert error_info.stack_trace is None
        assert error_info.context is None
        assert error_info.resolved is False
        assert error_info.resolution_time is None


class TestErrorHandler:
    """Test cases for ErrorHandler class"""

    def test_init(self):
        """Test ErrorHandler initialization"""
        handler = ErrorHandler()

        assert handler.errors == {}
        assert isinstance(handler.error_handlers, dict)
        assert isinstance(handler.recovery_strategies, dict)
        assert isinstance(handler.error_counters, dict)
        assert isinstance(handler._lock, asyncio.Lock)

    def test_register_default_handlers(self):
        """Test that default handlers are registered"""
        handler = ErrorHandler()

        # Check that default handlers are registered
        assert ErrorCategory.VALIDATION in handler.error_handlers
        assert ErrorCategory.NETWORK in handler.error_handlers
        assert ErrorCategory.DATABASE in handler.error_handlers
        assert ErrorCategory.AUTHENTICATION in handler.error_handlers
        assert ErrorCategory.SYSTEM in handler.error_handlers

    def test_generate_error_id(self):
        """Test error ID generation"""
        handler = ErrorHandler()

        error_id1 = handler._generate_error_id()
        error_id2 = handler._generate_error_id()

        assert error_id1.startswith("ERR_")
        assert error_id2.startswith("ERR_")
        assert error_id1 != error_id2

    def test_classify_error_validation(self):
        """Test error classification for validation errors"""
        handler = ErrorHandler()

        # ValueError
        severity, category = handler._classify_error(ValueError("Invalid input"))
        assert severity == ErrorSeverity.MEDIUM
        assert category == ErrorCategory.VALIDATION

        # Message contains "validation"
        severity, category = handler._classify_error(Exception("validation failed"))
        assert severity == ErrorSeverity.MEDIUM
        assert category == ErrorCategory.VALIDATION

    def test_classify_error_network(self):
        """Test error classification for network errors"""
        handler = ErrorHandler()

        # ConnectionError
        severity, category = handler._classify_error(ConnectionError("Connection failed"))
        assert severity == ErrorSeverity.HIGH
        assert category == ErrorCategory.NETWORK

        # Message contains "network"
        severity, category = handler._classify_error(Exception("network timeout"))
        assert severity == ErrorSeverity.HIGH
        assert category == ErrorCategory.NETWORK

    def test_classify_error_database(self):
        """Test error classification for database errors"""
        handler = ErrorHandler()

        # FileNotFoundError
        severity, category = handler._classify_error(FileNotFoundError("Database file not found"))
        assert severity == ErrorSeverity.HIGH
        assert category == ErrorCategory.DATABASE

        # Message contains "database"
        severity, category = handler._classify_error(Exception("database connection failed"))
        assert severity == ErrorSeverity.HIGH
        assert category == ErrorCategory.DATABASE

    def test_classify_error_authentication(self):
        """Test error classification for authentication errors"""
        handler = ErrorHandler()

        # PermissionError
        severity, category = handler._classify_error(PermissionError("Access denied"))
        assert severity == ErrorSeverity.HIGH
        assert category == ErrorCategory.AUTHENTICATION

        # Message contains "auth"
        severity, category = handler._classify_error(Exception("auth token expired"))
        assert severity == ErrorSeverity.HIGH
        assert category == ErrorCategory.AUTHENTICATION

    def test_classify_error_system(self):
        """Test error classification for system errors"""
        handler = ErrorHandler()

        # KeyboardInterrupt
        severity, category = handler._classify_error(KeyboardInterrupt())
        assert severity == ErrorSeverity.LOW
        assert category == ErrorCategory.SYSTEM

        # MemoryError
        severity, category = handler._classify_error(MemoryError("Out of memory"))
        assert severity == ErrorSeverity.CRITICAL
        assert category == ErrorCategory.SYSTEM

    def test_classify_error_unknown(self):
        """Test error classification for unknown errors"""
        handler = ErrorHandler()

        # Unknown exception
        severity, category = handler._classify_error(Exception("Unknown error"))
        assert severity == ErrorSeverity.MEDIUM
        assert category == ErrorCategory.UNKNOWN

    def test_get_log_level(self):
        """Test log level mapping"""
        handler = ErrorHandler()

        assert handler._get_log_level(ErrorSeverity.LOW) == logging.DEBUG
        assert handler._get_log_level(ErrorSeverity.MEDIUM) == logging.INFO
        assert handler._get_log_level(ErrorSeverity.HIGH) == logging.WARNING
        assert handler._get_log_level(ErrorSeverity.CRITICAL) == logging.ERROR

    @pytest.mark.asyncio
    async def test_handle_error_success(self):
        """Test successful error handling"""
        handler = ErrorHandler()

        error = ValueError("Test validation error")
        error_info = await handler.handle_error(error, handler_name="test_handler", user_id=123)

        assert error_info.error_type == "ValueError"
        assert error_info.error_message == "Test validation error"
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.category == ErrorCategory.VALIDATION
        assert error_info.handler_name == "test_handler"
        assert error_info.user_id == 123
        assert error_info.resolved is False

        # Check that error was stored
        assert error_info.error_id in handler.errors
        assert handler.error_counters["validation"] == 1

    @pytest.mark.asyncio
    async def test_handle_error_with_context(self):
        """Test error handling with context"""
        handler = ErrorHandler()

        context = {"user_action": "login", "ip_address": "192.168.1.1"}
        error = ConnectionError("Network timeout")
        error_info = await handler.handle_error(error, context=context)

        assert error_info.context == context
        assert error_info.severity == ErrorSeverity.HIGH
        assert error_info.category == ErrorCategory.NETWORK

    @pytest.mark.asyncio
    async def test_handle_error_multiple_errors(self):
        """Test handling multiple errors"""
        handler = ErrorHandler()

        error1 = ValueError("Error 1")
        error2 = ConnectionError("Error 2")

        await handler.handle_error(error1)
        await handler.handle_error(error2)

        assert len(handler.errors) == 2
        assert handler.error_counters["validation"] == 1
        assert handler.error_counters["network"] == 1

    @pytest.mark.asyncio
    async def test_register_error_handler(self):
        """Test registering custom error handler"""
        handler = ErrorHandler()

        handler_called = False

        async def custom_handler(error_info):
            nonlocal handler_called
            handler_called = True

        handler.register_error_handler(ErrorCategory.VALIDATION, custom_handler)

        # Trigger error
        await handler.handle_error(ValueError("Test"))

        assert handler_called

    @pytest.mark.asyncio
    async def test_register_recovery_strategy(self):
        """Test registering recovery strategy"""
        handler = ErrorHandler()

        strategy_called = False

        async def recovery_strategy(error_info):
            nonlocal strategy_called
            strategy_called = True

        handler.register_recovery_strategy(ErrorCategory.NETWORK, recovery_strategy)

        # Trigger network error
        await handler.handle_error(ConnectionError("Test"))

        assert strategy_called

    @pytest.mark.asyncio
    async def test_get_error_stats(self):
        """Test getting error statistics"""
        handler = ErrorHandler()

        # Create some errors
        await handler.handle_error(ValueError("Error 1"))
        await handler.handle_error(ConnectionError("Error 2"))
        await handler.handle_error(ValueError("Error 3"))

        stats = await handler.get_error_stats()

        assert stats["total_errors"] == 3
        assert stats["errors_by_category"]["validation"] == 2
        assert stats["errors_by_category"]["network"] == 1
        assert stats["errors_by_severity"]["medium"] == 2
        assert stats["errors_by_severity"]["high"] == 1
        assert len(stats["recent_errors"]) == 3

    @pytest.mark.asyncio
    async def test_get_error_stats_empty(self):
        """Test getting error stats when no errors exist"""
        handler = ErrorHandler()

        stats = await handler.get_error_stats()

        assert stats["total_errors"] == 0
        assert stats["errors_by_category"] == {}
        assert stats["errors_by_severity"] == {}
        assert stats["recent_errors"] == []

    @pytest.mark.asyncio
    async def test_resolve_error(self):
        """Test resolving an error"""
        handler = ErrorHandler()

        # Create an error
        error_info = await handler.handle_error(ValueError("Test error"))
        error_id = error_info.error_id

        # Resolve the error
        await handler.resolve_error(error_id, "Fixed by user")

        # Check that error is resolved
        resolved_error = await handler.get_error_details(error_id)
        assert resolved_error.resolved is True
        assert resolved_error.resolution_time is not None

    @pytest.mark.asyncio
    async def test_resolve_nonexistent_error(self):
        """Test resolving a non-existent error"""
        handler = ErrorHandler()

        # Try to resolve non-existent error
        await handler.resolve_error("nonexistent", "Test")

        # Should not crash

    @pytest.mark.asyncio
    async def test_get_error_details(self):
        """Test getting error details"""
        handler = ErrorHandler()

        # Create an error
        error_info = await handler.handle_error(ValueError("Test error"))
        error_id = error_info.error_id

        # Get details
        details = await handler.get_error_details(error_id)

        assert details is not None
        assert details.error_id == error_id
        assert details.error_message == "Test error"

    @pytest.mark.asyncio
    async def test_get_error_details_nonexistent(self):
        """Test getting details for non-existent error"""
        handler = ErrorHandler()

        details = await handler.get_error_details("nonexistent")

        assert details is None

    @pytest.mark.asyncio
    async def test_default_handlers(self):
        """Test default error handlers"""
        handler = ErrorHandler()

        # Test validation handler
        with patch('utils.error_handler.logger') as mock_logger:
            await handler._handle_validation_error(
                ErrorInfo(
                    "test",
                    time.time(),
                    "ValueError",
                    "test",
                    ErrorSeverity.MEDIUM,
                    ErrorCategory.VALIDATION,
                )
            )
            mock_logger.info.assert_called_once()

        # Test network handler
        with patch('utils.error_handler.logger') as mock_logger:
            await handler._handle_network_error(
                ErrorInfo(
                    "test",
                    time.time(),
                    "ConnectionError",
                    "test",
                    ErrorSeverity.HIGH,
                    ErrorCategory.NETWORK,
                )
            )
            mock_logger.warning.assert_called_once()

        # Test database handler
        with patch('utils.error_handler.logger') as mock_logger:
            await handler._handle_database_error(
                ErrorInfo(
                    "test",
                    time.time(),
                    "DatabaseError",
                    "test",
                    ErrorSeverity.HIGH,
                    ErrorCategory.DATABASE,
                )
            )
            mock_logger.error.assert_called_once()

        # Test auth handler
        with patch('utils.error_handler.logger') as mock_logger:
            await handler._handle_auth_error(
                ErrorInfo(
                    "test",
                    time.time(),
                    "AuthError",
                    "test",
                    ErrorSeverity.HIGH,
                    ErrorCategory.AUTHENTICATION,
                )
            )
            mock_logger.warning.assert_called_once()

        # Test system handler
        with patch('utils.error_handler.logger') as mock_logger:
            await handler._handle_system_error(
                ErrorInfo(
                    "test",
                    time.time(),
                    "SystemError",
                    "test",
                    ErrorSeverity.CRITICAL,
                    ErrorCategory.SYSTEM,
                )
            )
            mock_logger.error.assert_called_once()
            mock_logger.critical.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handler_failure(self):
        """Test that error handler failures don't crash the system"""
        handler = ErrorHandler()

        async def failing_handler(error_info):
            raise Exception("Handler failed")

        handler.register_error_handler(ErrorCategory.VALIDATION, failing_handler)

        # Should not crash
        with patch('utils.error_handler.logger') as mock_logger:
            await handler.handle_error(ValueError("Test"))
            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_recovery_strategy_failure(self):
        """Test that recovery strategy failures don't crash the system"""
        handler = ErrorHandler()

        async def failing_strategy(error_info):
            raise Exception("Recovery failed")

        handler.register_recovery_strategy(ErrorCategory.NETWORK, failing_strategy)

        # Should not crash
        with patch('utils.error_handler.logger') as mock_logger:
            await handler.handle_error(ConnectionError("Test"))
            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_error_handling(self):
        """Test concurrent error handling"""
        handler = ErrorHandler()

        async def create_error(i):
            await handler.handle_error(ValueError(f"Error {i}"))

        # Create multiple errors concurrently
        tasks = [create_error(i) for i in range(10)]
        await asyncio.gather(*tasks)

        assert len(handler.errors) == 10
        assert handler.error_counters["validation"] == 10


class TestErrorHandlerSingleton:
    """Test cases for the singleton error_handler instance"""

    def test_singleton_instance(self):
        """Test that error_handler is a singleton instance"""
        assert error_handler is not None
        assert isinstance(error_handler, ErrorHandler)

    @pytest.mark.asyncio
    async def test_singleton_operations(self):
        """Test that singleton instance can perform operations"""
        error = ValueError("Test error")
        error_info = await error_handler.handle_error(error)

        assert error_info.error_type == "ValueError"
        assert error_info.category == ErrorCategory.VALIDATION


class TestPTBErrorHandler:
    """Test cases for ptb_error_handler function"""

    @pytest.mark.asyncio
    async def test_ptb_error_handler_with_error(self):
        """Test ptb_error_handler with error in context"""
        mock_update = MagicMock()
        mock_context = MagicMock()
        mock_context.error = ValueError("PTB error")

        with patch('utils.error_handler.error_handler') as mock_error_handler:
            await ptb_error_handler(mock_update, mock_context)

            mock_error_handler.handle_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_ptb_error_handler_without_error(self):
        """Test ptb_error_handler without error in context"""
        mock_update = MagicMock()
        mock_context = MagicMock()
        mock_context.error = None

        with patch('utils.error_handler.error_handler') as mock_error_handler:
            await ptb_error_handler(mock_update, mock_context)

            mock_error_handler.handle_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_ptb_error_handler_failure(self):
        """Test ptb_error_handler when it fails"""
        mock_update = MagicMock()
        mock_context = MagicMock()
        mock_context.error = ValueError("PTB error")

        with patch('utils.error_handler.error_handler') as mock_error_handler:
            mock_error_handler.handle_error.side_effect = Exception("Handler failed")

            with patch('utils.error_handler.logger') as mock_logger:
                await ptb_error_handler(mock_update, mock_context)

                mock_logger.error.assert_called_once()
