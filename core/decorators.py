#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Decorators for Ostad Hatami Bot
"""

import logging
import asyncio
from functools import wraps
from typing import Union, Callable, Any
from aiogram.types import Message, CallbackQuery

from config import Config
from utils import RateLimiter, BotErrorHandler

logger = logging.getLogger(__name__)

# Initialize components
config = Config()
rate_limiter = RateLimiter(
    max_requests=config.performance.max_requests_per_minute,
    window_seconds=60
)
error_handler = BotErrorHandler()


def rate_limit(func: Callable) -> Callable:
    """Rate limiting decorator"""
    @wraps(func)
    async def wrapper(message_or_callback: Union[Message, CallbackQuery], *args, **kwargs):
        try:
            user_id = message_or_callback.from_user.id
            
            if not rate_limiter.is_allowed(user_id):
                await error_handler.handle_rate_limit(message_or_callback)
                return
            
            return await func(message_or_callback, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in rate_limit decorator: {e}")
            await error_handler.handle_error(message_or_callback, e)
    
    return wrapper


def maintenance_mode(func: Callable) -> Callable:
    """Maintenance mode decorator"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            if config.bot.maintenance_mode:
                # Find the message or callback object
                message_or_callback = None
                for arg in args:
                    if isinstance(arg, (Message, CallbackQuery)):
                        message_or_callback = arg
                        break
                
                if message_or_callback:
                    await message_or_callback.answer(
                        "🔧 ربات در حال تعمیر و نگهداری است.\n"
                        "لطفاً کمی بعد تلاش کنید.",
                        show_alert=True
                    )
                return
            
            return await func(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in maintenance_mode decorator: {e}")
            await error_handler.handle_error(message_or_callback, e)
    
    return wrapper


def admin_only(func: Callable) -> Callable:
    """Admin-only decorator"""
    @wraps(func)
    async def wrapper(message_or_callback: Union[Message, CallbackQuery], *args, **kwargs):
        try:
            user_id = message_or_callback.from_user.id
            
            if user_id not in config.bot.admin_user_ids:
                await message_or_callback.answer(
                    "❌ شما دسترسی به این بخش را ندارید.",
                    show_alert=True
                )
                return
            
            return await func(message_or_callback, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in admin_only decorator: {e}")
            await error_handler.handle_error(message_or_callback, e)
    
    return wrapper


def registered_user_only(func: Callable) -> Callable:
    """Registered user only decorator"""
    @wraps(func)
    async def wrapper(message_or_callback: Union[Message, CallbackQuery], *args, **kwargs):
        try:
            from database import DataManager
            
            user_id = message_or_callback.from_user.id
            data_manager = DataManager()
            
            user_data = data_manager.load_user_data(user_id)
            if not user_data:
                await message_or_callback.answer(
                    "❌ لطفاً ابتدا ثبت‌نام کنید.\n"
                    "از دستور /start استفاده کنید.",
                    show_alert=True
                )
                return
            
            return await func(message_or_callback, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in registered_user_only decorator: {e}")
            await error_handler.handle_error(message_or_callback, e)
    
    return wrapper


def async_retry(max_retries: int = 3, delay: float = 1.0):
    """Async retry decorator"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
            
            logger.error(f"All {max_retries} attempts failed")
            raise last_exception
        
        return wrapper
    return decorator
