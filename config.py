# -*- coding: utf-8 -*-
"""
Configuration file for Math Course Registration Bot
فایل تنظیمات ربات ثبت‌نام کلاس‌های ریاضی
"""

import os

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")  # Get from environment variable
BOT_NAME = "Ostad Hatami Bot"
BOT_USERNAME = "OstadHatami_bot"

# Admin Configuration
ADMIN_IDS = [
    "@Ostad_Hatami",  # استاد حاتمی
    "@F209EVRH"       # شما
]

# Course Information
COURSES = [
    {
        "name": "نظریه اعداد و ریاضی گسسته",
        "price": "۵۰۰,۰۰۰ تومان",
        "duration": "دوره کامل",
        "description": "قوی‌ترین مبحث کتاب درسی ریاضی گسسته دوازدهم رشته ریاضی و المپیاد ریاضی",
        "target": "پایه دوازدهم ریاضی + المپیاد دهم و یازدهم",
        "type": "پولی"
    },
    {
        "name": "مهارت‌های حل خلاق مسائل ریاضی",
        "price": "رایگان",
        "duration": "جمعه‌ها ساعت ۳",
        "description": "آموزش تفکر خلاق در حل مسائل ریاضی و ارتقاء سطح سواد ریاضی",
        "target": "پایه‌های دهم، یازدهم و دوازدهم",
        "type": "رایگان"
    },
    {
        "name": "کلاس‌های پایه دهم",
        "price": "رایگان",
        "duration": "جمعه‌ها",
        "description": "کلاس‌های مشترک ریاضی و تجربی پایه دهم",
        "target": "پایه دهم",
        "type": "رایگان"
    },
    {
        "name": "کلاس‌های پایه یازدهم",
        "price": "رایگان",
        "duration": "جمعه‌ها",
        "description": "کلاس‌های مشترک ریاضی و تجربی پایه یازدهم",
        "target": "پایه یازدهم",
        "type": "رایگان"
    },
    {
        "name": "کلاس‌های پایه دوازدهم",
        "price": "رایگان",
        "duration": "جمعه‌ها",
        "description": "کلاس‌های مشترک ریاضی و تجربی پایه دوازدهم",
        "target": "پایه دوازدهم",
        "type": "رایگان"
    }
]

# Special Courses (Free Online)
SPECIAL_COURSES = [
    {
        "name": "نظریه اعداد گسسته",
        "target": "پایه دوازدهم ریاضی + المپیاد دهم و یازدهم",
        "start_date": "جمعه ۱۷ مرداد",
        "type": "آنلاین رایگان",
        "duration": "دوره کامل",
        "deadline": "۸ مرداد ماه",
        "description": "قوی‌ترین مبحث کتاب درسی ریاضی گسسته دوازدهم رشته ریاضی و المپیاد ریاضی"
    },
    {
        "name": "مهارت‌های حل خلاق مسائل",
        "target": "پایه‌های دهم، یازدهم و دوازدهم",
        "schedule": "جمعه‌ها ساعت ۳ بعدازظهر",
        "type": "آنلاین رایگان",
        "platform": "اسکای روم",
        "description": "آموزش تفکر خلاق در حل مسائل ریاضی و ارتقاء سطح سواد ریاضی"
    }
]

# Current Class Schedule
CURRENT_SCHEDULE = [
    {
        "day": "جمعه ۱۰ مرداد",
        "time": "ساعت ۳ بعدازظهر",
        "grade": "پایه‌های دهم، یازدهم و دوازدهم",
        "topic": "مشترک هر دو رشته ریاضی و تجربی",
        "platform": "اسکای روم",
        "note": "حضور به موقع خیلی مهم است"
    },
    {
        "day": "جمعه ۱۷ مرداد",
        "time": "ساعت ۳ بعدازظهر",
        "grade": "پایه دوازدهم ریاضی",
        "topic": "شروع کلاس نظریه اعداد",
        "platform": "اسکای روم",
        "note": "کلاس جدید - ثبت‌نام تا ۸ مرداد"
    }
]

# Class Capacity Status
CLASS_CAPACITY = [
    {
        "grade": "پایه دهم",
        "current": 21,
        "max": 29,
        "status": "در حال ثبت‌نام",
        "available": 8
    },
    {
        "grade": "پایه یازدهم",
        "current": 23,
        "max": 29,
        "status": "در حال ثبت‌نام",
        "available": 6
    },
    {
        "grade": "پایه دوازدهم",
        "current": 29,
        "max": 29,
        "status": "تکمیل شده",
        "available": 0
    }
]

# Contact Information
CONTACT_INFO = {
    "whatsapp": "+98 938 153 0556",
    "phone": "+98 938 153 0556",
    "telegram": "@Ostad_Hatami",
    "email": "HamrahBaOstad@gmail.com",
    "address": "تهران",
    "working_hours": "شنبه تا چهارشنبه: ۹ صبح تا ۶ عصر\nپنجشنبه: ۹ صبح تا ۱ ظهر"
}

# Social Media Links
SOCIAL_LINKS = {
    "instagram": "https://www.instagram.com/hamrahbaostad",
    "youtube": "https://youtube.com/@hamrahbaostad",
    "telegram_channel": "https://t.me/hamrahbaostad",
    "website": "Soon"
}

# Book Information
BOOK_INFO = {
    "name": "انفجار خلاقیت ریاضی",
    "author": "استاد حاتمی",
    "price": "۱۵۰,۰۰۰ تومان",
    "year": "۱۴۰۴",
    "description": "این کتاب شامل تکنیک‌های خلاقانه حل مسائل ریاضی است که به دانش‌آموزان کمک می‌کند تا مفاهیم پیچیده را به راحتی درک کنند. حاصل ۴۰ سال تدریس در مدارس معتبر تهران نظیر رشد، انرژی اتمی، سلام، تیزهوشان حلی، فرزانگان، علامه و...",
    "target_audience": [
        "دانش‌آموزان پایه دهم تا دوازدهم",
        "داوطلبان کنکور سراسری",
        "علاقه‌مندان به ریاضیات"
    ]
}

# Latest Announcements
ANNOUNCEMENTS = [
    {
        "title": "برنامه کلاس‌های روز جمعه ۱۰ مرداد",
        "content": "کلاس روز جمعه دهم از ساعت 3 برای دانش‌آموزان پایه‌های دهم و یازدهم و دوازدهم، مشترک هر دو رشته ریاضی و تجربی در اسکای روم برگزار می‌شود.",
        "date": "۳۰ تیر ۱۴۰۴"
    },
    {
        "title": "ثبت‌نام دوره نظریه اعداد",
        "content": "ثبت‌نام دوره کامل نظریه اعداد (قوی‌ترین مبحث کتاب درسی) ریاضی گسسته دوازدهم رشته ریاضی و علاقه‌مندان المپیاد ریاضی دهم و یازدهم - فقط تا ۸ مرداد ماه - آنلاین و رایگان",
        "date": "۲۸ تیر ۱۴۰۴"
    },
    {
        "title": "کلاس‌های آموزش مهارت‌های حل خلاق",
        "content": "کلاس آنلاین و رایگان در آموزش مهارت‌های لازم برای حل خلاق مسائل ریاضی از روز جمعه شروع می‌شود. حاصل ۴۰ سال تدریس در مدارس معتبر تهران.",
        "date": "۲۸ تیر ۱۴۰۴"
    }
]

# Data Storage
DATA_FILE = "data/students.json"
BACKUP_FILE = "data/students_backup.json"

# Security Configuration
ENCRYPTION_KEY = "your-secret-encryption-key-here"  # Change this in production
HASH_SALT = "your-hash-salt-here"  # Change this in production

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = "logs/bot.log"

# Notification Settings
NOTIFICATION_ENABLED = True
AUTO_BACKUP_ENABLED = True
BACKUP_INTERVAL_HOURS = 24

# 2025 Advanced Features Configuration
# Multi-language Support
SUPPORTED_LANGUAGES = ["fa", "en"]
DEFAULT_LANGUAGE = "fa"

# AI/ML Features
AI_ENABLED = True
SENTIMENT_ANALYSIS_ENABLED = True
PERSONALIZATION_ENABLED = True
PREDICTIVE_RESPONSES_ENABLED = True

# Advanced UI/UX Features
RICH_MENUS_ENABLED = True
CONVERSATIONAL_UI_ENABLED = True
VISUAL_FEEDBACK_ENABLED = True
WEB_APP_INTEGRATION_ENABLED = True

# Business & Monetization Features
PAYMENT_PROCESSING_ENABLED = True
SUBSCRIPTION_SYSTEM_ENABLED = True
ECOMMERCE_INTEGRATION_ENABLED = True
ANALYTICS_DASHBOARD_ENABLED = True

# Advanced Integration Features
IOT_CONNECTIVITY_ENABLED = False
AR_VR_FEATURES_ENABLED = False
BLOCKCHAIN_INTEGRATION_ENABLED = False
CRM_INTEGRATION_ENABLED = True

# Compliance & Security Features
GDPR_COMPLIANCE_ENABLED = True
CONTENT_MODERATION_ENABLED = True
AGE_VERIFICATION_ENABLED = True
AUDIT_TRAILS_ENABLED = True

# User Growth & Engagement Features
VIRAL_MECHANISMS_ENABLED = True
GAMIFICATION_ENABLED = True
SOCIAL_FEATURES_ENABLED = True
PERSONALIZED_NOTIFICATIONS_ENABLED = True

# Advanced Analytics Configuration
ANALYTICS_CONFIG = {
    "user_behavior_tracking": True,
    "conversion_tracking": True,
    "performance_metrics": True,
    "a_b_testing": True
}

# Payment Methods
PAYMENT_METHODS = {
    "online": True,
    "bank_transfer": True,
    "crypto": False,
    "subscription": True
}

# Subscription Plans
SUBSCRIPTION_PLANS = [
    {
        "name": "برنزی",
        "price": "۱۰۰,۰۰۰ تومان",
        "duration": "ماهانه",
        "features": ["دسترسی به کلاس‌های رایگان", "مشاوره اولیه"]
    },
    {
        "name": "نقره‌ای",
        "price": "۲۵۰,۰۰۰ تومان", 
        "duration": "ماهانه",
        "features": ["تمام ویژگی‌های برنزی", "کلاس‌های ویژه", "پشتیبانی ۲۴/۷"]
    },
    {
        "name": "طلایی",
        "price": "۵۰۰,۰۰۰ تومان",
        "duration": "ماهانه", 
        "features": ["تمام ویژگی‌های نقره‌ای", "کلاس‌های خصوصی", "مشاوره تخصصی"]
    }
]

# Gamification System
GAMIFICATION_CONFIG = {
    "points_system": True,
    "badges": True,
    "leaderboards": True,
    "rewards": True,
    "achievements": [
        "اولین ثبت‌نام",
        "شرکت در ۵ کلاس",
        "توصیه به دوستان",
        "پرداخت موفق"
    ]
}

# Social Features
SOCIAL_FEATURES_CONFIG = {
    "user_profiles": True,
    "friend_system": True,
    "group_chats": True,
    "content_sharing": True,
    "community_forums": True
}

# AI/ML Models Configuration
AI_MODELS_CONFIG = {
    "language_model": "gpt-3.5-turbo",
    "sentiment_analyzer": "vader",
    "recommendation_engine": "collaborative_filtering",
    "personalization_model": "user_based"
}

# Advanced Security Features
SECURITY_CONFIG = {
    "two_factor_auth": True,
    "end_to_end_encryption": True,
    "rate_limiting": True,
    "fraud_detection": True,
    "data_anonymization": True
}

# Performance Optimization
PERFORMANCE_CONFIG = {
    "caching_enabled": True,
    "database_optimization": True,
    "load_balancing": True,
    "cdn_integration": True,
    "auto_scaling": True
} 