#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test script for the Telegram bot
اسکریپت تست ساده برای ربات تلگرام
"""

import os
import sys

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 تست import کردن کتابخانه‌ها...")
    
    try:
        from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
        print("✅ python-telegram-bot قابل import است")
    except ImportError as e:
        print(f"❌ خطا در import python-telegram-bot: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv قابل import است")
    except ImportError as e:
        print(f"❌ خطا در import python-dotenv: {e}")
        return False
    
    try:
        import config
        print("✅ فایل config قابل import است")
    except ImportError as e:
        print(f"❌ خطا در import config: {e}")
        return False
    
    return True

def test_config():
    """Test configuration values"""
    print("\n🔍 تست تنظیمات...")
    
    import config
    
    # Check required config values
    required_configs = [
        ('BOT_TOKEN', config.BOT_TOKEN),
        ('COURSES', config.COURSES),
        ('CONTACT_INFO', config.CONTACT_INFO),
        ('SOCIAL_LINKS', config.SOCIAL_LINKS),
        ('BOOK_INFO', config.BOOK_INFO)
    ]
    
    for name, value in required_configs:
        if value:
            print(f"✅ {name}: تنظیم شده")
        else:
            print(f"❌ {name}: تنظیم نشده")
            return False
    
    return True

def test_bot_creation():
    """Test bot creation"""
    print("\n🔍 تست ایجاد ربات...")
    
    try:
        from hosted_bot import HostedMathBot
        
        # This will fail because BOT_TOKEN is not set, but we can test the import
        print("✅ کلاس HostedMathBot قابل import است")
        return True
    except Exception as e:
        print(f"❌ خطا در ایجاد ربات: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 شروع تست ربات تلگرام...")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\n❌ تست import ناموفق بود")
        return False
    
    # Test config
    if not test_config():
        print("\n❌ تست تنظیمات ناموفق بود")
        return False
    
    # Test bot creation
    if not test_bot_creation():
        print("\n❌ تست ایجاد ربات ناموفق بود")
        return False
    
    print("\n🎉 همه تست‌ها موفق بودند!")
    print("✅ ربات آماده برای استفاده است")
    print("\n💡 برای اجرای ربات:")
    print("   1. فایل .env ایجاد کنید")
    print("   2. BOT_TOKEN را تنظیم کنید")
    print("   3. py hosted_bot.py را اجرا کنید")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 