#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import os

def run_command(command):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def install_telegram_bot():
    """Try different methods to install python-telegram-bot"""
    print("🔧 تلاش برای نصب python-telegram-bot...")
    print("=" * 50)
    
    methods = [
        {
            "name": "روش ۱: نصب مستقیم",
            "command": "py -m pip install python-telegram-bot==20.7"
        },
        {
            "name": "روش ۲: نصب با trusted hosts",
            "command": "py -m pip install python-telegram-bot==20.7 --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org"
        },
        {
            "name": "روش ۳: نصب از GitHub",
            "command": "py -m pip install git+https://github.com/python-telegram-bot/python-telegram-bot.git"
        },
        {
            "name": "روش ۴: نصب با mirror چینی",
            "command": "py -m pip install python-telegram-bot==20.7 -i https://pypi.tuna.tsinghua.edu.cn/simple/"
        },
        {
            "name": "روش ۵: نصب با mirror ایرانی",
            "command": "py -m pip install python-telegram-bot==20.7 -i https://pypi.python.org/simple/"
        }
    ]
    
    for i, method in enumerate(methods, 1):
        print(f"\n🔍 {method['name']}...")
        success, stdout, stderr = run_command(method['command'])
        
        if success:
            print("✅ موفق!")
            print("🎉 python-telegram-bot نصب شد!")
            return True
        else:
            print("❌ ناموفق")
            if stderr:
                print(f"خطا: {stderr[:200]}...")
    
    print("\n❌ هیچ روشی موفق نبود!")
    print("\n💡 راه‌حل‌های جایگزین:")
    print("1. از VPN استفاده کنید")
    print("2. تنظیمات proxy را بررسی کنید")
    print("3. فایل .whl را دستی دانلود کنید")
    print("4. از Anaconda استفاده کنید")
    
    return False

def check_installation():
    """Check if telegram library is installed"""
    print("\n🔍 بررسی نصب...")
    try:
        import telegram
        print("✅ python-telegram-bot نصب شده است!")
        print(f"نسخه: {telegram.__version__}")
        return True
    except ImportError:
        print("❌ python-telegram-bot نصب نشده است!")
        return False

def main():
    """Main function"""
    print("🚀 نصب‌کننده کتابخانه تلگرام")
    print("=" * 50)
    
    # Check if already installed
    if check_installation():
        print("\n🎉 کتابخانه قبلاً نصب شده است!")
        return True
    
    # Try to install
    if install_telegram_bot():
        # Check again
        if check_installation():
            print("\n🎉 نصب موفق بود!")
            print("\n🚀 حالا می‌توانید ربات را اجرا کنید:")
            print("   py run_bot.py")
            return True
    
    return False

if __name__ == "__main__":
    main() 