#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def test_telegram_installation():
    """Test if telegram library is properly installed"""
    print("🔍 تست نصب کتابخانه تلگرام...")
    print("=" * 40)
    
    try:
        import telegram
        print("✅ python-telegram-bot نصب شده است!")
        print(f"📦 نسخه: {telegram.__version__}")
        
        # Test basic functionality
        from telegram import Bot
        print("✅ کلاس Bot قابل import است!")
        
        from telegram.ext import Application
        print("✅ کلاس Application قابل import است!")
        
        print("\n🎉 همه چیز درست کار می‌کند!")
        print("🚀 آماده برای اجرای ربات!")
        
        return True
        
    except ImportError as e:
        print(f"❌ خطا در import: {e}")
        print("\n💡 راه‌حل:")
        print("1. اسکریپت install_library.py را اجرا کنید")
        print("2. یا دستی نصب کنید: py -m pip install python-telegram-bot==20.7")
        return False
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
        return False

if __name__ == "__main__":
    test_telegram_installation() 