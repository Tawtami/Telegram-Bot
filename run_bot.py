#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Startup script for Math Course Registration Bot
اسکریپت راه‌اندازی ربات ثبت‌نام کلاس‌های ریاضی
"""

import sys
import os
import time
import asyncio

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import telegram
        print("✅ python-telegram-bot نصب شده است")
        return True
    except ImportError:
        print("❌ python-telegram-bot نصب نشده است!")
        print("💡 برای نصب:")
        print("   py install_library.py")
        print("   یا")
        print("   py -m pip install python-telegram-bot")
        return False

def check_config():
    """Check if bot token is configured"""
    try:
        from config import BOT_TOKEN
        if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            print("❌ توکن ربات تنظیم نشده است!")
            print("💡 لطفاً توکن خود را در فایل config.py وارد کنید")
            return False
        
        print("✅ توکن ربات تنظیم شده است")
        return True
    except ImportError:
        print("❌ فایل config.py یافت نشد!")
        return False

async def main():
    """Main startup function"""
    print("🚀 راه‌اندازی ربات کلاس‌های ریاضی...")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n💡 برای نصب کتابخانه، دستور زیر را اجرا کنید:")
        print("   py install_library.py")
        sys.exit(1)
    
    # Check configuration
    if not check_config():
        sys.exit(1)
    
    print("\n✅ همه چیز آماده است!")
    print("🤖 ربات در حال راه‌اندازی...")
    
    try:
        # Import and run bot
        from mathbot import MathBot
        from config import BOT_TOKEN
        
        bot = MathBot(BOT_TOKEN)
        await bot.run()
    except KeyboardInterrupt:
        print("\n⏹️ ربات متوقف شد.")
    except Exception as e:
        print(f"\n❌ خطا در اجرای ربات: {e}")
        print("💡 لطفاً تنظیمات را بررسی کنید")

if __name__ == "__main__":
    asyncio.run(main()) 