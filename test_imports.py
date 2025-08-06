#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

import sys
import os


def test_imports():
    """Test all required imports"""
    try:
        print("Testing imports...")

        # Test basic imports
        import json
        import logging
        import asyncio
        import time

        print("✅ Basic imports successful")

        # Test external dependencies
        from aiogram import Bot, Dispatcher, types, Router
        from aiogram.fsm.state import State, StatesGroup
        from aiogram.fsm.context import FSMContext
        from aiogram.fsm.storage.memory import MemoryStorage
        from aiogram.types import (
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            KeyboardButton,
        )
        from aiogram.filters import Command, StateFilter
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        from dotenv import load_dotenv

        print("✅ External dependencies successful")

        # Test our modules
        from config import Config

        print("✅ Config import successful")

        from database import DataManager

        print("✅ Database import successful")

        from utils import (
            Validator,
            SimpleCache,
            RateLimiter,
            PerformanceMonitor,
            BotErrorHandler,
            SecurityUtils,
        )

        print("✅ Utils import successful")

        print("🎉 All imports successful!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
