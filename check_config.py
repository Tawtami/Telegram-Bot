#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os

def main():
    print("Testing Ostad Hatami Bot Configuration")
    print("=" * 50)
    
    try:
        # Test config import
        from config import *
        print("✅ Config file loaded successfully")
        
        # Test bot token
        if BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
            print(f"✅ Bot token is configured: {BOT_TOKEN[:20]}...")
        else:
            print("❌ Bot token not configured")
            return
        
        # Test bot info
        print(f"✅ Bot name: {BOT_NAME}")
        print(f"✅ Bot username: @{BOT_USERNAME}")
        
        # Test contact info
        print(f"✅ WhatsApp: {CONTACT_INFO['whatsapp']}")
        print(f"✅ Telegram: {CONTACT_INFO['telegram']}")
        print(f"✅ Email: {CONTACT_INFO['email']}")
        
        # Test social links
        print(f"✅ Instagram: {SOCIAL_LINKS['instagram']}")
        print(f"✅ YouTube: {SOCIAL_LINKS['youtube']}")
        print(f"✅ Telegram Channel: {SOCIAL_LINKS['telegram_channel']}")
        
        # Test courses
        total_courses = 0
        for grade, courses in COURSES.items():
            for course_name, course_info in courses.items():
                total_courses += 1
        print(f"✅ Total courses configured: {total_courses}")
        
        # Test data directory
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        print("✅ Data directories created")
        
        # Test JSON file
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            print("✅ Students JSON file created")
        else:
            print("✅ Students JSON file exists")
        
        # Test telegram library
        try:
            import telegram
            print("✅ python-telegram-bot is installed")
            print("\n🎉 Everything is ready! You can run the bot with:")
            print("   python run_bot.py")
        except ImportError:
            print("❌ python-telegram-bot is not installed")
            print("💡 Install it with: pip install python-telegram-bot")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 