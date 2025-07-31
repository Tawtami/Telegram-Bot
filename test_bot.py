#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Ostad Hatami Bot
اسکریپت تست ربات استاد حاتمی
"""

import json
import os
from config import *

def test_configuration():
    """Test bot configuration"""
    print("🔧 تست تنظیمات ربات...")
    print("=" * 40)
    
    # Test bot token
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ توکن ربات تنظیم نشده است!")
        return False
    else:
        print("✅ توکن ربات تنظیم شده است")
    
    # Test bot info
    print(f"📱 نام ربات: {BOT_NAME}")
    print(f"🔗 نام کاربری: @{BOT_USERNAME}")
    
    # Test contact info
    print(f"📞 واتساپ: {CONTACT_INFO['whatsapp']}")
    print(f"📱 تلگرام: {CONTACT_INFO['telegram']}")
    
    # Test social links
    print(f"📱 اینستاگرام: {SOCIAL_LINKS['instagram']}")
    print(f"📺 یوتیوب: {SOCIAL_LINKS['youtube']}")
    
    return True

def test_courses():
    """Test course configuration"""
    print("\n📚 تست دوره‌های آموزشی...")
    print("=" * 40)
    
    total_courses = 0
    for grade, courses in COURSES.items():
        print(f"📖 پایه {grade}:")
        for course_name, course_info in courses.items():
            print(f"   • {course_name}: {course_info['price']:,} تومان")
            total_courses += 1
    
    print(f"\n📊 تعداد کل دوره‌ها: {total_courses}")
    return total_courses > 0

def test_data_directory():
    """Test data directory creation"""
    print("\n💾 تست دایرکتوری داده‌ها...")
    print("=" * 40)
    
    try:
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        print("✅ دایرکتوری‌های data و logs ایجاد شدند")
        
        # Test JSON file creation
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            print("✅ فایل students.json ایجاد شد")
        else:
            print("✅ فایل students.json موجود است")
        
        return True
    except Exception as e:
        print(f"❌ خطا در ایجاد دایرکتوری‌ها: {e}")
        return False

def test_dependencies():
    """Test required dependencies"""
    print("\n📦 تست وابستگی‌ها...")
    print("=" * 40)
    
    try:
        import telegram
        print("✅ python-telegram-bot نصب شده است")
        return True
    except ImportError:
        print("❌ python-telegram-bot نصب نشده است!")
        print("💡 برای نصب: pip install python-telegram-bot")
        return False

def main():
    """Main test function"""
    print("🧪 تست ربات استاد حاتمی")
    print("=" * 50)
    
    tests = [
        ("تنظیمات", test_configuration),
        ("دوره‌های آموزشی", test_courses),
        ("دایرکتوری داده‌ها", test_data_directory),
        ("وابستگی‌ها", test_dependencies)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: موفق")
            else:
                print(f"❌ {test_name}: ناموفق")
        except Exception as e:
            print(f"❌ {test_name}: خطا - {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 نتایج تست: {passed}/{total} موفق")
    
    if passed == total:
        print("🎉 همه تست‌ها موفق بودند! ربات آماده اجرا است.")
        print("\n🚀 برای اجرای ربات:")
        print("   python run_bot.py")
    else:
        print("⚠️ برخی تست‌ها ناموفق بودند. لطفاً مشکلات را برطرف کنید.")
    
    return passed == total

if __name__ == "__main__":
    main() 