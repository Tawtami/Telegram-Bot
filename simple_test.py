#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test script for Ostad Hatami Bot (without telegram library)
اسکریپت تست ساده ربات استاد حاتمی (بدون نیاز به کتابخانه تلگرام)
"""

import json
import os

def test_configuration():
    """Test bot configuration"""
    print("🔧 تست تنظیمات ربات...")
    print("=" * 40)
    
    try:
        import config
        
        # Test bot token
        if config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            print("❌ توکن ربات تنظیم نشده است!")
            return False
        else:
            print("✅ توکن ربات تنظیم شده است")
            print(f"   توکن: {config.BOT_TOKEN[:20]}...")
        
        # Test bot info
        print(f"📱 نام ربات: {config.BOT_NAME}")
        print(f"🔗 نام کاربری: @{config.BOT_USERNAME}")
        
        # Test contact info
        print(f"📞 واتساپ: {config.CONTACT_INFO['whatsapp']}")
        print(f"📱 تلگرام: {config.CONTACT_INFO['telegram']}")
        print(f"📧 ایمیل: {config.CONTACT_INFO['email']}")
        
        # Test social links
        print(f"📱 اینستاگرام: {config.SOCIAL_LINKS['instagram']}")
        print(f"📺 یوتیوب: {config.SOCIAL_LINKS['youtube']}")
        print(f"📢 کانال تلگرام: {config.SOCIAL_LINKS['telegram_channel']}")
        
        return True
        
    except ImportError as e:
        print(f"❌ خطا در import کردن config: {e}")
        return False
    except Exception as e:
        print(f"❌ خطا در تست تنظیمات: {e}")
        return False

def test_courses():
    """Test course configuration"""
    print("\n📚 تست دوره‌های آموزشی...")
    print("=" * 40)
    
    try:
        import config
        
        total_courses = 0
        for grade, courses in config.COURSES.items():
            print(f"📖 پایه {grade}:")
            for course_name, course_info in courses.items():
                price_formatted = f"{course_info['price']:,}".replace(',', '،')
                print(f"   • {course_name}: {price_formatted} تومان")
                total_courses += 1
        
        print(f"\n📊 تعداد کل دوره‌ها: {total_courses}")
        return total_courses > 0
        
    except Exception as e:
        print(f"❌ خطا در تست دوره‌ها: {e}")
        return False

def test_data_directory():
    """Test data directory creation"""
    print("\n💾 تست دایرکتوری داده‌ها...")
    print("=" * 40)
    
    try:
        import config
        
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        print("✅ دایرکتوری‌های data و logs ایجاد شدند")
        
        # Test JSON file creation
        if not os.path.exists(config.DATA_FILE):
            with open(config.DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            print("✅ فایل students.json ایجاد شد")
        else:
            print("✅ فایل students.json موجود است")
        
        return True
    except Exception as e:
        print(f"❌ خطا در ایجاد دایرکتوری‌ها: {e}")
        return False

def test_telegram_library():
    """Test if telegram library is available"""
    print("\n📦 تست کتابخانه تلگرام...")
    print("=" * 40)
    
    try:
        import telegram
        print("✅ python-telegram-bot نصب شده است")
        return True
    except ImportError:
        print("❌ python-telegram-bot نصب نشده است!")
        print("💡 برای نصب:")
        print("   pip install python-telegram-bot")
        print("   یا")
        print("   pip install --trusted-host pypi.org python-telegram-bot")
        return False

def main():
    """Main test function"""
    print("🧪 تست ساده ربات استاد حاتمی")
    print("=" * 50)
    
    tests = [
        ("تنظیمات", test_configuration),
        ("دوره‌های آموزشی", test_courses),
        ("دایرکتوری داده‌ها", test_data_directory),
        ("کتابخانه تلگرام", test_telegram_library)
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
    
    if passed >= 3:  # At least config, courses, and data directory should work
        print("🎉 تنظیمات اصلی درست است!")
        if passed == 4:
            print("🚀 همه چیز آماده است! ربات آماده اجرا است.")
            print("\nبرای اجرای ربات:")
            print("   python run_bot.py")
        else:
            print("⚠️ فقط کتابخانه تلگرام نیاز به نصب دارد.")
            print("💡 پس از نصب کتابخانه، ربات آماده اجرا خواهد بود.")
    else:
        print("⚠️ برخی تنظیمات اصلی مشکل دارند. لطفاً مشکلات را برطرف کنید.")
    
    return passed >= 3

if __name__ == "__main__":
    main() 