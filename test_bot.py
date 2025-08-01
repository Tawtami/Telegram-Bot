#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Ostad Hatami Bot
اسکریپت تست برای ربات استاد حاتمی
"""

import os
import sys
import json
from pathlib import Path

def test_python_version():
    """Test Python version"""
    print("🐍 Testing Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Need 3.8+")
        return False

def test_dependencies():
    """Test required dependencies"""
    print("\n📦 Testing dependencies...")
    
    try:
        import telegram
        print("✅ python-telegram-bot - OK")
    except ImportError:
        print("❌ python-telegram-bot - NOT INSTALLED")
        return False
    
    try:
        import dotenv
        print("✅ python-dotenv - OK")
    except ImportError:
        print("❌ python-dotenv - NOT INSTALLED")
        return False
    
    return True

def test_environment():
    """Test environment variables"""
    print("\n🔧 Testing environment...")
    
    # Load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .env file loaded")
    except Exception as e:
        print(f"❌ Error loading .env: {e}")
        return False
    
    # Check BOT_TOKEN
    bot_token = os.getenv("BOT_TOKEN")
    if bot_token and bot_token != "your_bot_token_here":
        print("✅ BOT_TOKEN is set")
        return True
    else:
        print("❌ BOT_TOKEN not set or invalid")
        return False

def test_file_structure():
    """Test file structure"""
    print("\n📁 Testing file structure...")
    
    required_files = [
        "final_bot.py",
        "requirements_final.txt",
        "env_template.txt"
    ]
    
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file} - OK")
        else:
            print(f"❌ {file} - MISSING")
            return False
    
    return True

def test_data_directory():
    """Test data directory creation"""
    print("\n💾 Testing data directory...")
    
    try:
        # Import and test UserDataManager
        sys.path.append('.')
        from final_bot import UserDataManager
        
        data_manager = UserDataManager()
        data_dir = Path(data_manager.data_dir)
        
        if data_dir.exists():
            print(f"✅ Data directory {data_dir} - OK")
        else:
            print(f"❌ Data directory {data_dir} - NOT CREATED")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error testing data directory: {e}")
        return False

def test_bot_import():
    """Test bot import"""
    print("\n🤖 Testing bot import...")
    
    try:
        from final_bot import OstadHatamiBot
        print("✅ Bot class imported successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing bot: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Ostad Hatami Bot Setup")
    print("=" * 50)
    
    tests = [
        ("Python Version", test_python_version),
        ("Dependencies", test_dependencies),
        ("Environment", test_environment),
        ("File Structure", test_file_structure),
        ("Data Directory", test_data_directory),
        ("Bot Import", test_bot_import)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bot is ready to use.")
        print("\n🚀 Next steps:")
        print("1. Set your BOT_TOKEN in .env file")
        print("2. Run: python final_bot.py")
        print("3. Test with /start command in Telegram")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print("\n🔧 Common fixes:")
        print("1. Install dependencies: pip install -r requirements_final.txt")
        print("2. Set BOT_TOKEN in .env file")
        print("3. Ensure all files are present")

if __name__ == "__main__":
    main() 