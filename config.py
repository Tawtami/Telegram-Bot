# -*- coding: utf-8 -*-
"""
Configuration file for Math Course Registration Bot
فایل تنظیمات ربات ثبت‌نام کلاس‌های ریاضی
"""

# Bot Configuration
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Replace with your actual bot token from @BotFather
BOT_NAME = "Ostad Hatami Bot"
BOT_USERNAME = "OstadHatami_bot"

# Admin Configuration
ADMIN_USER_ID = None  # Your Telegram user ID for admin features

# Course Information
COURSES = {
    "دهم": {
        "جبر و معادله": {"price": 250000, "duration": "12 جلسه", "type": "آنلاین"},
        "هندسه تحلیلی": {"price": 250000, "duration": "10 جلسه", "type": "آنلاین"}
    },
    "یازدهم": {
        "حسابان": {"price": 300000, "duration": "15 جلسه", "type": "آنلاین"},
        "آمار و احتمال": {"price": 300000, "duration": "12 جلسه", "type": "آنلاین"}
    },
    "دوازدهم": {
        "مشتق و حد": {"price": 350000, "duration": "18 جلسه", "type": "آنلاین"},
        "انتگرال": {"price": 350000, "duration": "16 جلسه", "type": "آنلاین"},
        "هندسه": {"price": 350000, "duration": "14 جلسه", "type": "آنلاین"}
    }
}

# Contact Information
CONTACT_INFO = {
    "whatsapp": "+98 938 153 0556",  # Update with actual WhatsApp number
    "phone": "+98 938 153 0556",     # Update with actual phone number
    "telegram": "@Ostad_Hatami",      # Update with actual Telegram username
    "email": "HamrahBaOstad@gmail.com",  # Update with actual email
    "address": "تهران",    # Update with actual address
    "working_hours": "شنبه تا چهارشنبه: ۹ صبح تا ۶ عصر\nپنجشنبه: ۹ صبح تا ۱ ظهر"
}

# Social Media Links
SOCIAL_LINKS = {
    "instagram": "https://www.instagram.com/hamrahbaostad",      # Update with actual Instagram
    "youtube": "youtube.com/@hamrahbaostad", # Update with actual YouTube
    "telegram_channel": "https://t.me/hamrahbaostad", # Update with actual Telegram channel
    "website": "Soon"        # Update with actual website
}

# Book Information
BOOK_INFO = {
    "title": "انفجار خلاقیت ریاضی",
    "price": 150000,
    "description": "این کتاب شامل تکنیک‌های خلاقانه حل مسائل ریاضی است که به دانش‌آموزان کمک می‌کند تا مفاهیم پیچیده را به راحتی درک کنند.",
    "target_audience": [
        "دانش‌آموزان پایه دهم تا دوازدهم",
        "داوطلبان کنکور سراسری",
        "علاقه‌مندان به ریاضیات"
    ]
}

# Data Storage
DATA_FILE = "data/students.json"
BACKUP_FILE = "data/students_backup.json"

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = "logs/bot.log"

# Message Templates
MESSAGES = {
    "welcome": "👋 سلام {name}! خوش آمدید به ربات ثبت‌نام کلاس‌های ریاضی استاد.",
    "registration_success": "✅ ثبت‌نام شما با موفقیت انجام شد!",
    "registration_cancelled": "❌ ثبت‌نام لغو شد. برای شروع مجدد /start را ارسال کنید.",
    "already_registered": "شما قبلاً ثبت‌نام کرده‌اید. منوی اصلی نمایش داده می‌شود."
} 