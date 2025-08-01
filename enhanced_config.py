# -*- coding: utf-8 -*-
"""
Enhanced Configuration for Advanced Math Course Registration Bot 2025
فایل تنظیمات پیشرفته ربات ثبت‌نام کلاس‌های ریاضی
"""

import os
from typing import Dict, List, Any

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
BOT_NAME = "Ostad Hatami Advanced Bot"
BOT_USERNAME = "OstadHatami_bot"

# Admin Configuration
ADMIN_IDS = [
    "@Ostad_Hatami",  # استاد حاتمی
    "@F209EVRH"       # شما
]

# AI/ML Configuration
AI_CONFIG = {
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "gpt_model": "gpt-3.5-turbo",
    "max_tokens": 1000,
    "temperature": 0.7,
    "enable_voice": True,
    "enable_sentiment": True,
    "enable_personalization": True,
    "enable_recommendations": True
}

# Database Configuration
DATABASE_CONFIG = {
    "type": "postgresql",  # or "sqlite", "mysql"
    "url": os.getenv("DATABASE_URL", "sqlite:///bot_data.db"),
    "pool_size": 20,
    "max_overflow": 30,
    "enable_migrations": True
}

# Redis Configuration
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", 6379)),
    "db": 0,
    "password": os.getenv("REDIS_PASSWORD", None),
    "enable_cache": True,
    "cache_ttl": 3600
}

# Performance Configuration
PERFORMANCE_CONFIG = {
    "max_concurrent_users": 10000,
    "message_queue_size": 1000,
    "rate_limit_per_user": 10,  # messages per minute
    "enable_compression": True,
    "enable_caching": True,
    "cache_ttl": 300
}

# Course Information (Enhanced)
COURSES = [
    {
        "id": "math_10_algebra",
        "name": "جبر و معادله پایه دهم",
        "price": "۲۵۰,۰۰۰ تومان",
        "duration": "۱۲ جلسه",
        "level": "دهم",
        "difficulty": "متوسط",
        "prerequisites": [],
        "topics": ["معادله درجه اول", "معادله درجه دوم", "نامساوی"],
        "ai_tags": ["algebra", "equations", "grade10"],
        "type": "پولی"
    },
    {
        "id": "math_11_calculus",
        "name": "حسابان پایه یازدهم",
        "price": "۳۰۰,۰۰۰ تومان",
        "duration": "۱۵ جلسه",
        "level": "یازدهم",
        "difficulty": "پیشرفته",
        "prerequisites": ["math_10_algebra"],
        "topics": ["مشتق", "حد", "پیوستگی"],
        "ai_tags": ["calculus", "derivative", "limit", "grade11"],
        "type": "پولی"
    },
    {
        "id": "math_12_integral",
        "name": "انتگرال پایه دوازدهم",
        "price": "۳۵۰,۰۰۰ تومان",
        "duration": "۱۸ جلسه",
        "level": "دوازدهم",
        "difficulty": "پیشرفته",
        "prerequisites": ["math_11_calculus"],
        "topics": ["انتگرال نامعین", "انتگرال معین", "کاربردها"],
        "ai_tags": ["integral", "calculus", "grade12"],
        "type": "پولی"
    },
    {
        "id": "free_creative_math",
        "name": "مهارت‌های حل خلاق مسائل ریاضی",
        "price": "رایگان",
        "duration": "جمعه‌ها ساعت ۳",
        "level": "همه پایه‌ها",
        "difficulty": "متوسط",
        "prerequisites": [],
        "topics": ["تفکر خلاق", "حل مسئله", "استدلال منطقی"],
        "ai_tags": ["creative", "problem_solving", "all_grades"],
        "type": "رایگان"
    }
]

# Gamification Configuration
GAMIFICATION_CONFIG = {
    "points_system": True,
    "points_per_action": {
        "registration": 100,
        "course_completion": 500,
        "daily_login": 10,
        "referral": 200,
        "quiz_perfect": 100,
        "help_others": 50
    },
    "badges": {
        "first_registration": {"name": "شروع کننده", "points": 100},
        "course_complete": {"name": "تکمیل کننده", "points": 500},
        "perfect_score": {"name": "نمره کامل", "points": 200},
        "helpful_user": {"name": "کمک کننده", "points": 300},
        "veteran": {"name": "کهنه کار", "points": 1000}
    },
    "levels": {
        1: {"name": "تازه کار", "min_points": 0},
        2: {"name": "آموزنده", "min_points": 500},
        3: {"name": "متخصص", "min_points": 1500},
        4: {"name": "استاد", "min_points": 3000},
        5: {"name": "نابغه", "min_points": 5000}
    }
}

# Subscription Plans (Enhanced)
SUBSCRIPTION_PLANS = [
    {
        "id": "bronze",
        "name": "برنزی",
        "price": "۱۰۰,۰۰۰ تومان",
        "duration": "ماهانه",
        "features": [
            "دسترسی به کلاس‌های رایگان",
            "مشاوره اولیه",
            "دانلود مواد آموزشی پایه",
            "پشتیبانی ایمیل"
        ],
        "ai_features": ["basic_recommendations"],
        "max_courses": 2
    },
    {
        "id": "silver",
        "name": "نقره‌ای",
        "price": "۲۵۰,۰۰۰ تومان",
        "duration": "ماهانه",
        "features": [
            "تمام ویژگی‌های برنزی",
            "کلاس‌های ویژه",
            "پشتیبانی ۲۴/۷",
            "آزمون‌های تعاملی",
            "گزارش پیشرفت"
        ],
        "ai_features": ["advanced_recommendations", "personalized_learning"],
        "max_courses": 5
    },
    {
        "id": "gold",
        "name": "طلایی",
        "price": "۵۰۰,۰۰۰ تومان",
        "duration": "ماهانه",
        "features": [
            "تمام ویژگی‌های نقره‌ای",
            "کلاس‌های خصوصی",
            "مشاوره تخصصی",
            "دسترسی نامحدود",
            "اولویت در پشتیبانی"
        ],
        "ai_features": ["all_ai_features", "custom_learning_path"],
        "max_courses": -1  # Unlimited
    }
]

# Voice Configuration
VOICE_CONFIG = {
    "enable_voice_input": True,
    "enable_voice_output": True,
    "supported_languages": ["fa", "en"],
    "voice_models": {
        "fa": "persian_voice_model",
        "en": "english_voice_model"
    },
    "max_voice_duration": 60,  # seconds
    "voice_quality": "high"
}

# Analytics Configuration
ANALYTICS_CONFIG = {
    "enable_tracking": True,
    "track_user_behavior": True,
    "track_conversions": True,
    "track_performance": True,
    "enable_a_b_testing": True,
    "retention_analysis": True,
    "engagement_metrics": True
}

# Security Configuration
SECURITY_CONFIG = {
    "enable_encryption": True,
    "encryption_key": os.getenv("ENCRYPTION_KEY", "your-secret-key"),
    "hash_salt": os.getenv("HASH_SALT", "your-salt"),
    "rate_limiting": True,
    "fraud_detection": True,
    "two_factor_auth": True,
    "session_timeout": 3600,
    "max_login_attempts": 5
}

# Notification Configuration
NOTIFICATION_CONFIG = {
    "enable_push_notifications": True,
    "enable_email_notifications": True,
    "notification_types": {
        "course_reminder": True,
        "achievement_unlocked": True,
        "new_content": True,
        "payment_reminder": True,
        "system_maintenance": True
    },
    "notification_timing": {
        "morning": "09:00",
        "afternoon": "15:00",
        "evening": "20:00"
    }
}

# Social Features Configuration
SOCIAL_CONFIG = {
    "enable_friends": True,
    "enable_groups": True,
    "enable_leaderboards": True,
    "enable_sharing": True,
    "enable_challenges": True,
    "max_friends": 100,
    "max_group_size": 50
}

# Learning Path Configuration
LEARNING_PATHS = {
    "grade_10": {
        "name": "مسیر یادگیری پایه دهم",
        "courses": ["math_10_algebra", "free_creative_math"],
        "duration": "6 months",
        "difficulty_progression": ["beginner", "intermediate"]
    },
    "grade_11": {
        "name": "مسیر یادگیری پایه یازدهم",
        "courses": ["math_11_calculus", "free_creative_math"],
        "duration": "8 months",
        "difficulty_progression": ["intermediate", "advanced"]
    },
    "grade_12": {
        "name": "مسیر یادگیری پایه دوازدهم",
        "courses": ["math_12_integral", "free_creative_math"],
        "duration": "10 months",
        "difficulty_progression": ["advanced", "expert"]
    }
}

# Quick Reply Configuration
QUICK_REPLIES = {
    "new_user": [
        "🚀 ثبت‌نام سریع",
        "📚 مشاهده کلاس‌ها",
        "❓ راهنما",
        "🎯 آزمون تعیین سطح"
    ],
    "registered": [
        "📊 پروفایل من",
        "🎯 کلاس بعدی",
        "💬 سوال از استاد",
        "📖 مواد آموزشی"
    ],
    "admin": [
        "📢 ارسال اطلاعیه",
        "📊 مشاهده آمار",
        "👥 مدیریت کاربران",
        "⚙️ تنظیمات سیستم"
    ]
}

# Error Messages
ERROR_MESSAGES = {
    "general": "متأسفانه خطایی رخ داده است. لطفاً دوباره تلاش کنید.",
    "network": "مشکل در اتصال شبکه. لطفاً اینترنت خود را بررسی کنید.",
    "permission": "شما مجوز انجام این کار را ندارید.",
    "not_found": "مورد درخواستی یافت نشد.",
    "invalid_input": "ورودی نامعتبر است. لطفاً دوباره تلاش کنید.",
    "rate_limit": "تعداد درخواست‌های شما زیاد است. لطفاً کمی صبر کنید."
}

# Success Messages
SUCCESS_MESSAGES = {
    "registration": "ثبت‌نام شما با موفقیت انجام شد! 🎉",
    "course_enrollment": "ثبت‌نام در کلاس با موفقیت انجام شد! 📚",
    "payment": "پرداخت شما با موفقیت انجام شد! 💰",
    "achievement": "دستاورد جدید کسب کردید! 🏆",
    "profile_update": "پروفایل شما با موفقیت به‌روزرسانی شد! ✅"
}

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
    "website": "https://hamrahbaostad.com"
}

# Data Storage
DATA_FILE = "data/students.json"
BACKUP_FILE = "data/students_backup.json"
USERS_FILE = "data/users.json"
ANALYTICS_FILE = "data/analytics.json"

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = "logs/bot.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Feature Flags
FEATURES = {
    "ai_enabled": True,
    "voice_enabled": True,
    "gamification_enabled": True,
    "social_enabled": True,
    "analytics_enabled": True,
    "subscription_enabled": True,
    "multi_language_enabled": True,
    "advanced_admin_enabled": True
} 