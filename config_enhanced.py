# -*- coding: utf-8 -*-
"""
Enhanced Configuration for Math Course Registration Bot - 2025 Edition
تنظیمات پیشرفته ربات ثبت‌نام کلاس‌های ریاضی - نسخه ۲۰۲۵
"""

import os
from typing import Dict, List, Any

# ============================================================================
# BOT CONFIGURATION
# ============================================================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
BOT_NAME = "Ostad Hatami Bot"
BOT_USERNAME = "OstadHatami_bot"

# ============================================================================
# ADMIN CONFIGURATION
# ============================================================================
ADMIN_IDS = [
    "@Ostad_Hatami",  # استاد حاتمی
    "@F209EVRH"       # شما
]

# ============================================================================
# PERFORMANCE & CACHING CONFIGURATION
# ============================================================================
# Cache settings
CACHE_ENABLED = True
CACHE_TTL = 300  # 5 minutes
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Rate limiting
RATE_LIMIT_ENABLED = True
RATE_LIMIT_PER_USER = 10  # requests per minute
RATE_LIMIT_PER_IP = 50    # requests per minute

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot_data.db")
CONNECTION_POOL_SIZE = 10
CONNECTION_POOL_MAX_OVERFLOW = 20

# Background tasks
BACKGROUND_TASKS_ENABLED = True
TASK_QUEUE_SIZE = 100

# ============================================================================
# UI/UX CONFIGURATION
# ============================================================================
# Theme colors and styling
UI_THEME = {
    "primary_color": "🔵",
    "success_color": "✅",
    "warning_color": "⚠️",
    "error_color": "❌",
    "info_color": "ℹ️",
    "premium_color": "💎",
    "free_color": "🆓"
}

# Button layouts
BUTTON_LAYOUTS = {
    "main_menu": {
        "columns": 2,
        "max_buttons_per_row": 2,
        "show_back_button": True
    },
    "course_selection": {
        "columns": 1,
        "max_buttons_per_row": 1,
        "show_back_button": True
    },
    "admin_panel": {
        "columns": 2,
        "max_buttons_per_row": 2,
        "show_back_button": True
    }
}

# Progress indicators
PROGRESS_INDICATORS = {
    "registration": ["📝", "📱", "🎓", "🎯", "📞", "✅"],
    "payment": ["💳", "💰", "✅"],
    "admin": ["⚙️", "📊", "✅"]
}

# Loading messages
LOADING_MESSAGES = [
    "🔄 در حال پردازش...",
    "⏳ لطفاً صبر کنید...",
    "🔄 در حال بارگذاری...",
    "⏳ یک لحظه...",
    "🔄 در حال آماده‌سازی..."
]

# ============================================================================
# COURSE INFORMATION (Enhanced)
# ============================================================================
COURSES = [
    {
        "id": "number_theory",
        "name": "نظریه اعداد و ریاضی گسسته",
        "price": "۵۰۰,۰۰۰ تومان",
        "duration": "دوره کامل",
        "description": "قوی‌ترین مبحث کتاب درسی ریاضی گسسته دوازدهم رشته ریاضی و المپیاد ریاضی",
        "target": "پایه دوازدهم ریاضی + المپیاد دهم و یازدهم",
        "type": "پولی",
        "difficulty": "پیشرفته",
        "seats_available": 50,
        "start_date": "جمعه ۱۷ مرداد",
        "features": ["ویدیوهای آموزشی", "تمرینات تعاملی", "پشتیبانی ۲۴/۷"],
        "category": "premium"
    },
    {
        "id": "creative_math",
        "name": "مهارت‌های حل خلاق مسائل ریاضی",
        "price": "رایگان",
        "duration": "جمعه‌ها ساعت ۳",
        "description": "آموزش تفکر خلاق در حل مسائل ریاضی و ارتقاء سطح سواد ریاضی",
        "target": "پایه‌های دهم، یازدهم و دوازدهم",
        "type": "رایگان",
        "difficulty": "متوسط",
        "seats_available": 100,
        "start_date": "جمعه ۱۰ مرداد",
        "features": ["کلاس آنلاین", "محتوی رایگان", "گواهی پایان دوره"],
        "category": "free"
    },
    {
        "id": "grade_10",
        "name": "کلاس‌های پایه دهم",
        "price": "رایگان",
        "duration": "جمعه‌ها",
        "description": "کلاس‌های مشترک ریاضی و تجربی پایه دهم",
        "target": "پایه دهم",
        "type": "رایگان",
        "difficulty": "مبتدی",
        "seats_available": 80,
        "start_date": "جمعه ۱۰ مرداد",
        "features": ["مفاهیم پایه", "تمرینات عملی", "پشتیبانی"],
        "category": "free"
    },
    {
        "id": "grade_11",
        "name": "کلاس‌های پایه یازدهم",
        "price": "رایگان",
        "duration": "جمعه‌ها",
        "description": "کلاس‌های مشترک ریاضی و تجربی پایه یازدهم",
        "target": "پایه یازدهم",
        "type": "رایگان",
        "difficulty": "متوسط",
        "seats_available": 80,
        "start_date": "جمعه ۱۰ مرداد",
        "features": ["مفاهیم پیشرفته", "تمرینات تعاملی", "پشتیبانی"],
        "category": "free"
    },
    {
        "id": "grade_12",
        "name": "کلاس‌های پایه دوازدهم",
        "price": "رایگان",
        "duration": "جمعه‌ها",
        "description": "کلاس‌های مشترک ریاضی و تجربی پایه دوازدهم",
        "target": "پایه دوازدهم",
        "type": "رایگان",
        "difficulty": "پیشرفته",
        "seats_available": 80,
        "start_date": "جمعه ۱۰ مرداد",
        "features": ["آمادگی کنکور", "نمونه سوالات", "پشتیبانی ویژه"],
        "category": "free"
    }
]

# ============================================================================
# SPECIAL COURSES (Enhanced)
# ============================================================================
SPECIAL_COURSES = [
    {
        "id": "number_theory_free",
        "name": "نظریه اعداد گسسته",
        "target": "پایه دوازدهم ریاضی + المپیاد دهم و یازدهم",
        "start_date": "جمعه ۱۷ مرداد",
        "type": "آنلاین رایگان",
        "duration": "دوره کامل",
        "deadline": "۸ مرداد ماه",
        "description": "قوی‌ترین مبحث کتاب درسی ریاضی گسسته دوازدهم رشته ریاضی و المپیاد ریاضی",
        "seats_available": 30,
        "features": ["کلاس آنلاین", "محتوی رایگان", "گواهی پایان دوره"],
        "difficulty": "پیشرفته",
        "category": "special_free"
    },
    {
        "id": "creative_skills",
        "name": "مهارت‌های حل خلاق مسائل",
        "target": "پایه‌های دهم، یازدهم و دوازدهم",
        "schedule": "جمعه‌ها ساعت ۳ بعدازظهر",
        "type": "آنلاین رایگان",
        "platform": "اسکای روم",
        "description": "آموزش تفکر خلاق در حل مسائل ریاضی و ارتقاء سطح سواد ریاضی",
        "seats_available": 50,
        "features": ["کلاس آنلاین", "تمرینات تعاملی", "پشتیبانی"],
        "difficulty": "متوسط",
        "category": "special_free"
    }
]

# ============================================================================
# SCHEDULE CONFIGURATION (Enhanced)
# ============================================================================
CURRENT_SCHEDULE = [
    {
        "id": "schedule_1",
        "day": "جمعه ۱۰ مرداد",
        "time": "ساعت ۳ بعدازظهر",
        "grade": "پایه‌های دهم، یازدهم و دوازدهم",
        "topic": "مشترک هر دو رشته ریاضی و تجربی",
        "platform": "اسکای روم",
        "note": "حضور به موقع خیلی مهم است",
        "duration": "۹۰ دقیقه",
        "instructor": "استاد حاتمی",
        "status": "upcoming"
    },
    {
        "id": "schedule_2",
        "day": "جمعه ۱۷ مرداد",
        "time": "ساعت ۳ بعدازظهر",
        "grade": "پایه دوازدهم ریاضی",
        "topic": "شروع کلاس نظریه اعداد",
        "platform": "اسکای روم",
        "note": "کلاس ویژه المپیاد",
        "duration": "۱۲۰ دقیقه",
        "instructor": "استاد حاتمی",
        "status": "upcoming"
    }
]

# ============================================================================
# SOCIAL LINKS & CONTACT (Enhanced)
# ============================================================================
SOCIAL_LINKS = {
    "telegram_channel": "https://t.me/OstadHatamiChannel",
    "telegram_group": "https://t.me/OstadHatamiGroup",
    "youtube": "https://youtube.com/@OstadHatami",
    "instagram": "https://instagram.com/OstadHatami",
    "website": "https://ostadhatami.ir"
}

CONTACT_INFO = {
    "phone": "۰۹۱۲۳۴۵۶۷۸۹",
    "email": "info@ostadhatami.ir",
    "address": "تهران، ایران",
    "office_hours": "شنبه تا چهارشنبه ۹ صبح تا ۶ عصر"
}

# ============================================================================
# ANNOUNCEMENTS (Enhanced)
# ============================================================================
ANNOUNCEMENTS = [
    {
        "id": "announcement_1",
        "title": "شروع کلاس‌های رایگان",
        "content": "کلاس‌های رایگان از جمعه ۱۰ مرداد شروع می‌شود. لطفاً ثبت‌نام کنید.",
        "date": "۱۴۰۴/۰۵/۰۵",
        "priority": "high",
        "category": "general"
    },
    {
        "id": "announcement_2",
        "title": "کلاس ویژه المپیاد",
        "content": "کلاس نظریه اعداد برای المپیاد از جمعه ۱۷ مرداد شروع می‌شود.",
        "date": "۱۴۰۴/۰۵/۰۶",
        "priority": "medium",
        "category": "olympiad"
    }
]

# ============================================================================
# BOOK INFORMATION (Enhanced)
# ============================================================================
BOOK_INFO = {
    "title": "کتاب نظریه اعداد و ریاضی گسسته",
    "author": "استاد حاتمی",
    "price": "۲۵۰,۰۰۰ تومان",
    "pages": "۴۰۰ صفحه",
    "description": "کتاب جامع نظریه اعداد و ریاضی گسسته برای پایه دوازدهم و المپیاد",
    "features": [
        "مثال‌های حل شده",
        "تمرینات متنوع",
        "نمونه سوالات کنکور",
        "پاسخ تشریحی"
    ],
    "available": True,
    "stock": 50
}

# ============================================================================
# SECURITY & DATA CONFIGURATION
# ============================================================================
# File paths
DATA_FILE = "data/students.json"
BACKUP_FILE = "data/students_backup.json"
LOG_FILE = "logs/bot.log"

# Security settings
HASH_SALT = os.getenv("HASH_SALT", "your_salt_here")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "your_key_here")
AUTO_BACKUP_ENABLED = True
BACKUP_INTERVAL = 3600  # 1 hour

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ============================================================================
# PAYMENT CONFIGURATION (Enhanced)
# ============================================================================
PAYMENT_SETTINGS = {
    "enabled": True,
    "methods": ["manual", "online"],
    "currency": "تومان",
    "auto_approval": False,
    "notification_enabled": True
}

# ============================================================================
# GAMIFICATION CONFIGURATION
# ============================================================================
GAMIFICATION = {
    "enabled": True,
    "points_per_registration": 10,
    "points_per_referral": 5,
    "badges": {
        "first_registration": "🎓 دانشجوی جدید",
        "multiple_courses": "📚 دانشجوی فعال",
        "referral": "🤝 معرف",
        "premium": "💎 دانشجوی ویژه"
    }
}

# ============================================================================
# NOTIFICATION CONFIGURATION
# ============================================================================
NOTIFICATIONS = {
    "welcome_message": True,
    "course_reminders": True,
    "payment_notifications": True,
    "announcement_notifications": True,
    "reminder_interval": 24  # hours
}

# ============================================================================
# ANALYTICS CONFIGURATION
# ============================================================================
ANALYTICS = {
    "enabled": True,
    "track_user_behavior": True,
    "track_conversion": True,
    "export_interval": 24  # hours
} 