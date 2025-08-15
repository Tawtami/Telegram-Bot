#!/usr/bin/env python3
"""
Mock Telegram module for running tests without python-telegram-bot

This provides the basic Telegram functionality that our test files need
to run without the actual python-telegram-bot package.
"""

import sys
from unittest.mock import MagicMock


# Mock Telegram classes
class InlineKeyboardMarkup:
    """Mock InlineKeyboardMarkup class"""

    def __init__(self, *args, **kwargs):
        self.inline_keyboard = []
        if args and isinstance(args[0], list):
            self.inline_keyboard = args[0]


class InlineKeyboardButton:
    """Mock InlineKeyboardButton class"""

    def __init__(self, *args, **kwargs):
        # Handle both positional and keyword arguments
        if args:
            self.text = args[0]
            self.callback_data = kwargs.get('callback_data', 'mock_callback')
        else:
            self.text = kwargs.get('text', 'Mock Button')
            self.callback_data = kwargs.get('callback_data', 'mock_callback')


class Update:
    """Mock Update class"""

    def __init__(self, *args, **kwargs):
        pass


class Message:
    """Mock Message class"""

    def __init__(self, *args, **kwargs):
        pass


class CallbackQuery:
    """Mock CallbackQuery class"""

    def __init__(self, *args, **kwargs):
        pass


class User:
    """Mock User class"""

    def __init__(self, *args, **kwargs):
        pass


class Chat:
    """Mock Chat class"""

    def __init__(self, *args, **kwargs):
        pass


# Mock telegram.constants module
class ParseMode:
    """Mock ParseMode constants"""

    HTML = "HTML"
    MARKDOWN = "MARKDOWN"
    MARKDOWN_V2 = "MARKDOWN_V2"


# Add to sys.modules so imports work
sys.modules['telegram'] = sys.modules[__name__]
sys.modules['telegram.ext'] = MagicMock()
sys.modules['telegram.constants'] = sys.modules[__name__]
