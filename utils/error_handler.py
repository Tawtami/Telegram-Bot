#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced error handling system for Ostad Hatami Bot
"""

import time
import asyncio
import logging
import traceback
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
from config import Config

# from .performance_monitor import monitor  # Will be initialized later
from collections import defaultdict

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories"""

    VALIDATION = "validation"
    NETWORK = "network"
    DATABASE = "database"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    SYSTEM = "system"
    USER_INPUT = "user_input"
    EXTERNAL_API = "external_api"
    UNKNOWN = "unknown"


@dataclass
class ErrorInfo:
    """Error information structure"""

    error_id: str
    timestamp: float
    error_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    handler_name: Optional[str] = None
    user_id: Optional[int] = None
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    resolved: bool = False
    resolution_time: Optional[float] = None


class ErrorHandler:
    """Enhanced error handling with classification and recovery"""

    def __init__(self):
        self.errors: Dict[str, ErrorInfo] = {}
        self.error_handlers: Dict[ErrorCategory, List[Callable]] = defaultdict(list)
        self.recovery_strategies: Dict[ErrorCategory, Callable] = {}
        self.error_counters: Dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()

        # Register default error handlers
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default error handlers"""
        # Validation errors
        self.register_error_handler(
            ErrorCategory.VALIDATION, self._handle_validation_error
        )

        # Network errors
        self.register_error_handler(ErrorCategory.NETWORK, self._handle_network_error)

        # Database errors
        self.register_error_handler(ErrorCategory.DATABASE, self._handle_database_error)

        # Authentication errors
        self.register_error_handler(
            ErrorCategory.AUTHENTICATION, self._handle_auth_error
        )

        # System errors
        self.register_error_handler(ErrorCategory.SYSTEM, self._handle_system_error)

    def _generate_error_id(self) -> str:
        """Generate unique error ID"""
        return f"ERR_{int(time.time())}_{len(self.errors)}"

    def _classify_error(self, error: Exception) -> tuple[ErrorSeverity, ErrorCategory]:
        """Classify error based on type and message"""
        error_type = type(error).__name__
        error_message = str(error).lower()

        # Classification logic
        if isinstance(error, ValueError) or "validation" in error_message:
            return ErrorSeverity.MEDIUM, ErrorCategory.VALIDATION

        elif isinstance(error, ConnectionError) or "network" in error_message:
            return ErrorSeverity.HIGH, ErrorCategory.NETWORK

        elif isinstance(error, FileNotFoundError) or "database" in error_message:
            return ErrorSeverity.HIGH, ErrorCategory.DATABASE

        elif isinstance(error, PermissionError) or "auth" in error_message:
            return ErrorSeverity.HIGH, ErrorCategory.AUTHENTICATION

        elif isinstance(error, KeyboardInterrupt):
            return ErrorSeverity.LOW, ErrorCategory.SYSTEM

        elif isinstance(error, MemoryError):
            return ErrorSeverity.CRITICAL, ErrorCategory.SYSTEM

        else:
            return ErrorSeverity.MEDIUM, ErrorCategory.UNKNOWN

    async def handle_error(
        self,
        error: Exception,
        handler_name: Optional[str] = None,
        user_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ErrorInfo:
        """Handle error with classification and logging"""
        async with self._lock:
            return await self._handle_error_sync(error, handler_name, user_id, context)

    async def _handle_error_sync(
        self,
        error: Exception,
        handler_name: Optional[str] = None,
        user_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ErrorInfo:
        """Synchronous error handling"""
        # Generate error info
        error_id = self._generate_error_id()
        timestamp = time.time()
        severity, category = self._classify_error(error)

        error_info = ErrorInfo(
            error_id=error_id,
            timestamp=timestamp,
            error_type=type(error).__name__,
            error_message=str(error),
            severity=severity,
            category=category,
            handler_name=handler_name,
            user_id=user_id,
            stack_trace=traceback.format_exc(),
            context=context or {},
        )

        # Store error
        self.errors[error_id] = error_info

        # Update counters
        self.error_counters[category.value] += 1

        # Log error
        log_level = self._get_log_level(severity)
        logger.log(
            log_level, f"Error [{error_id}]: {error} in {handler_name or 'unknown'}"
        )

        # Log to performance monitor
        # await monitor.log_error(error_info.error_type, handler_name, user_id)

        # Call category-specific handlers
        await self._call_error_handlers(error_info)

        # Attempt recovery
        await self._attempt_recovery(error_info)

        return error_info

    def _get_log_level(self, severity: ErrorSeverity) -> int:
        """Get log level based on severity"""
        return {
            ErrorSeverity.LOW: logging.DEBUG,
            ErrorSeverity.MEDIUM: logging.INFO,
            ErrorSeverity.HIGH: logging.WARNING,
            ErrorSeverity.CRITICAL: logging.ERROR,
        }.get(severity, logging.INFO)

    async def _call_error_handlers(self, error_info: ErrorInfo):
        """Call registered error handlers for the category"""
        handlers = self.error_handlers.get(error_info.category, [])
        for handler in handlers:
            try:
                await handler(error_info)
            except Exception as e:
                logger.error(f"Error in error handler: {e}")

    async def _attempt_recovery(self, error_info: ErrorInfo):
        """Attempt to recover from error"""
        recovery_strategy = self.recovery_strategies.get(error_info.category)
        if recovery_strategy:
            try:
                await recovery_strategy(error_info)
            except Exception as e:
                logger.error(f"Error in recovery strategy: {e}")

    async def handle_user_error(
        self,
        message_or_callback: Any,
        error_message: str,
        error_type: str = "user_error",
    ):
        """Handle user-facing errors with appropriate response"""
        try:
            # Log user error
            await self.handle_error(
                Exception(error_message),
                handler_name=error_type,
                context={"user_facing": True},
            )

            # Send user-friendly message
            if hasattr(message_or_callback, "answer"):
                await message_or_callback.answer(f"❌ {error_message}")
            elif hasattr(message_or_callback, "message"):
                await message_or_callback.message.answer(f"❌ {error_message}")
            elif hasattr(message_or_callback, "edit_text"):
                await message_or_callback.edit_text(f"❌ {error_message}")

        except Exception as e:
            logger.error(f"Error sending error message: {e}")

    async def handle_system_error(
        self, message_or_callback: Any, error: Exception, context: str
    ):
        """Handle system errors with error ID for tracking"""
        try:
            # Handle the error
            error_info = await self.handle_error(error, context)

            # Send user-friendly message with error ID
            error_msg = (
                f"خطای سیستمی رخ داده است. کد خطا: {error_info.error_id}\n"
                f"لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
            )

            if hasattr(message_or_callback, "answer"):
                await message_or_callback.answer(error_msg)
            elif hasattr(message_or_callback, "message"):
                await message_or_callback.message.answer(error_msg)
            elif hasattr(message_or_callback, "edit_text"):
                await message_or_callback.edit_text(error_msg)

        except Exception as e:
            logger.error(f"Error sending system error message: {e}")

    def register_error_handler(self, category: ErrorCategory, handler: Callable):
        """Register error handler for specific category"""
        self.error_handlers[category].append(handler)

    def register_recovery_strategy(self, category: ErrorCategory, strategy: Callable):
        """Register recovery strategy for specific category"""
        self.recovery_strategies[category] = strategy

    async def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        async with self._lock:
            total_errors = len(self.errors)
            errors_by_category = defaultdict(int)
            errors_by_severity = defaultdict(int)

            for error_info in self.errors.values():
                errors_by_category[error_info.category.value] += 1
                errors_by_severity[error_info.severity.value] += 1

            return {
                "total_errors": total_errors,
                "errors_by_category": dict(errors_by_category),
                "errors_by_severity": dict(errors_by_severity),
                "error_counters": dict(self.error_counters),
                "recent_errors": [
                    {
                        "id": error_info.error_id,
                        "type": error_info.error_type,
                        "category": error_info.category.value,
                        "severity": error_info.severity.value,
                        "timestamp": error_info.timestamp,
                        "resolved": error_info.resolved,
                    }
                    for error_info in sorted(
                        self.errors.values(), key=lambda x: x.timestamp, reverse=True
                    )[:10]
                ],
            }

    async def resolve_error(self, error_id: str, resolution_note: str = ""):
        """Mark error as resolved"""
        async with self._lock:
            if error_id in self.errors:
                self.errors[error_id].resolved = True
                self.errors[error_id].resolution_time = time.time()
                logger.info(f"Error {error_id} marked as resolved: {resolution_note}")

    async def get_error_details(self, error_id: str) -> Optional[ErrorInfo]:
        """Get detailed error information"""
        async with self._lock:
            return self.errors.get(error_id)

    # Default error handlers
    async def _handle_validation_error(self, error_info: ErrorInfo):
        """Handle validation errors"""
        logger.info(f"Validation error handled: {error_info.error_message}")

    async def _handle_network_error(self, error_info: ErrorInfo):
        """Handle network errors"""
        logger.warning(f"Network error detected: {error_info.error_message}")
        # Could implement retry logic here

    async def _handle_database_error(self, error_info: ErrorInfo):
        """Handle database errors"""
        logger.error(f"Database error: {error_info.error_message}")
        # Could implement connection retry or fallback

    async def _handle_auth_error(self, error_info: ErrorInfo):
        """Handle authentication errors"""
        logger.warning(f"Authentication error: {error_info.error_message}")

    async def _handle_system_error(self, error_info: ErrorInfo):
        """Handle system errors"""
        logger.error(f"System error: {error_info.error_message}")
        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical("Critical system error detected!")


# Global error handler instance
error_handler = ErrorHandler()
