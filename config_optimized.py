#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Configuration for 200X Optimized Bot
پیکربندی پیشرفته برای ربات بهینه‌سازی شده ۲۰۰ برابری
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

# ============================================================================
# CORE BOT CONFIGURATION
# ============================================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
WEBHOOK_ENABLED = os.getenv("WEBHOOK_ENABLED", "false").lower() == "true"

# ============================================================================
# PERFORMANCE & CACHING
# ============================================================================
CACHE_ENABLED = True
CACHE_TTL = 300  # 5 minutes
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
MEMORY_CACHE_SIZE = 1000
RATE_LIMIT_PER_USER = 30  # requests per minute
RATE_LIMIT_PER_IP = 100   # requests per minute

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot_data.db")
DATABASE_ENABLED = True
BACKUP_ENABLED = True
BACKUP_INTERVAL_HOURS = 24

# ============================================================================
# AI & MACHINE LEARNING
# ============================================================================
AI_ENABLED = True
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AI_MODEL = "gpt-3.5-turbo"
AI_MAX_TOKENS = 150
SENTIMENT_ANALYSIS_ENABLED = True
RECOMMENDATION_ENGINE_ENABLED = True

# ============================================================================
# ANALYTICS & MONITORING
# ============================================================================
ANALYTICS_ENABLED = True
METRICS_ENABLED = True
PROMETHEUS_ENABLED = True
HEALTH_CHECK_ENABLED = True
PERFORMANCE_MONITORING = True

# ============================================================================
# SECURITY & PRIVACY
# ============================================================================
ENCRYPTION_ENABLED = True
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
TWO_FACTOR_ENABLED = True
SESSION_TIMEOUT_MINUTES = 60
MAX_LOGIN_ATTEMPTS = 5
BLOCK_DURATION_MINUTES = 30

# ============================================================================
# UI/UX ENHANCEMENTS
# ============================================================================
UI_THEME = {
    "primary_color": "🔵",
    "success_color": "✅",
    "warning_color": "⚠️",
    "error_color": "❌",
    "info_color": "ℹ️",
    "premium_color": "💎",
    "free_color": "🆓",
    "vip_color": "👑",
    "new_color": "🆕",
    "hot_color": "🔥"
}

BUTTON_LAYOUTS = {
    "compact": 2,  # buttons per row
    "normal": 1,
    "wide": 3
}

PROGRESS_INDICATORS = {
    "enabled": True,
    "style": "dots",  # dots, bars, percentage
    "color": "🔵"
}

# ============================================================================
# COURSE & CONTENT MANAGEMENT
# ============================================================================
COURSES = {
    "number_theory": {
        "id": "number_theory",
        "name": "نظریه اعداد و ریاضی گسسته",
        "price": 500000,
        "currency": "تومان",
        "duration": "دوره کامل",
        "level": "پیشرفته",
        "target": ["پایه دوازدهم ریاضی", "المپیاد"],
        "features": ["ویدیوهای آموزشی", "تمرینات تعاملی", "پشتیبانی ۲۴/۷"],
        "instructor": "استاد حاتمی",
        "rating": 4.9,
        "students": 1250,
        "last_updated": "2024-01-15",
        "status": "active"
    },
    "creative_math": {
        "id": "creative_math",
        "name": "مهارت‌های حل خلاق مسائل ریاضی",
        "price": 0,
        "currency": "رایگان",
        "duration": "جمعه‌ها ساعت ۳",
        "level": "متوسط",
        "target": ["پایه دهم", "پایه یازدهم", "پایه دوازدهم"],
        "features": ["کلاس زنده", "گروه پشتیبانی", "مطالب تکمیلی"],
        "instructor": "استاد حاتمی",
        "rating": 4.8,
        "students": 2100,
        "last_updated": "2024-01-10",
        "status": "active"
    },
    "foundation": {
        "id": "foundation",
        "name": "کلاس‌های پایه (دهم، یازدهم، دوازدهم)",
        "price": 0,
        "currency": "رایگان",
        "duration": "جمعه‌ها",
        "level": "مبتدی",
        "target": ["همه پایه‌ها"],
        "features": ["مفاهیم پایه", "تمرینات ساده", "پشتیبانی"],
        "instructor": "استاد حاتمی",
        "rating": 4.7,
        "students": 3500,
        "last_updated": "2024-01-05",
        "status": "active"
    }
}

BOOKS = {
    "creative_explosion": {
        "id": "creative_explosion",
        "name": "انفجار خلاقیت",
        "author": "استاد حاتمی",
        "pages": 400,
        "price": 250000,
        "currency": "تومان",
        "features": ["مثال‌های حل شده", "تمرینات متنوع", "نمونه سوالات کنکور", "پاسخ تشریحی"],
        "isbn": "978-600-123-456-7",
        "publisher": "انتشارات حاتمی",
        "language": "فارسی",
        "format": "چاپی",
        "availability": "موجود",
        "shipping": "رایگان",
        "rating": 4.9,
        "reviews": 156
    }
}

# ============================================================================
# SOCIAL MEDIA & CONTENT
# ============================================================================
SOCIAL_MEDIA = {
    "youtube": {
        "url": "https://youtube.com/@OstadHatami",
        "name": "کانال یوتیوب استاد حاتمی",
        "subscribers": "15K+",
        "videos": "200+",
        "content": ["آموزش‌های رایگان ریاضی", "حل مسئله‌های خلاقانه", "تکنیک‌های حل مسئله"]
    },
    "instagram": {
        "url": "https://instagram.com/OstadHatami",
        "name": "پیج اینستاگرام استاد حاتمی",
        "followers": "25K+",
        "posts": "500+",
        "content": ["نکات آموزشی روزانه", "نمونه سوالات", "اخبار و اطلاعیه‌ها"]
    },
    "telegram_channel": {
        "url": "https://t.me/OstadHatamiChannel",
        "name": "کانال تلگرام استاد حاتمی",
        "members": "8K+",
        "content": ["اخبار و اطلاعیه‌های کلاس‌ها", "نمونه سوالات و پاسخ‌ها", "نکات آموزشی مفید"]
    },
    "telegram_group": {
        "url": "https://t.me/OstadHatamiGroup",
        "name": "گروه مشاوره استاد حاتمی",
        "members": "3K+",
        "content": ["پرسش و پاسخ", "رفع اشکال", "مشاوره تحصیلی"]
    }
}

# ============================================================================
# CONTACT & SUPPORT
# ============================================================================
CONTACT_INFO = {
    "phone": "۰۹۱۲۳۴۵۶۷۸۹",
    "email": "info@ostadhatami.ir",
    "address": "تهران، ایران",
    "website": "https://ostadhatami.ir",
    "telegram_support": "@Ostad_Hatami",
    "working_hours": {
        "weekdays": "شنبه تا چهارشنبه: ۹ صبح تا ۶ عصر",
        "weekend": "جمعه: ۹ صبح تا ۲ عصر",
        "holidays": "پنجشنبه: تعطیل"
    },
    "response_time": "حداکثر ۲ ساعت"
}

# ============================================================================
# GAMIFICATION & ENGAGEMENT
# ============================================================================
GAMIFICATION = {
    "enabled": True,
    "points_system": {
        "daily_login": 10,
        "course_completion": 100,
        "quiz_correct": 5,
        "referral": 50,
        "feedback": 20
    },
    "badges": {
        "newcomer": {"name": "تازه‌وارد", "points": 0, "icon": "🆕"},
        "regular": {"name": "کاربر منظم", "points": 100, "icon": "⭐"},
        "learner": {"name": "یادگیرنده", "points": 500, "icon": "📚"},
        "expert": {"name": "متخصص", "points": 1000, "icon": "🎓"},
        "master": {"name": "استاد", "points": 5000, "icon": "👑"}
    },
    "leaderboard": {
        "enabled": True,
        "update_interval": 3600,  # 1 hour
        "top_users": 10
    }
}

# ============================================================================
# NOTIFICATIONS & ALERTS
# ============================================================================
NOTIFICATIONS = {
    "enabled": True,
    "types": {
        "course_reminder": True,
        "new_content": True,
        "achievement": True,
        "promotional": False,
        "system": True
    },
    "channels": {
        "telegram": True,
        "email": False,
        "sms": False
    },
    "scheduling": {
        "morning": "09:00",
        "afternoon": "15:00",
        "evening": "20:00"
    }
}

# ============================================================================
# PERSONALIZATION & RECOMMENDATIONS
# ============================================================================
PERSONALIZATION = {
    "enabled": True,
    "learning_path": True,
    "content_recommendations": True,
    "difficulty_adaptation": True,
    "progress_tracking": True,
    "study_reminders": True
}

# ============================================================================
# ADVANCED FEATURES
# ============================================================================
ADVANCED_FEATURES = {
    "voice_messages": True,
    "file_sharing": True,
    "screen_sharing": False,
    "live_streaming": False,
    "virtual_classroom": False,
    "ai_tutor": True,
    "progress_analytics": True,
    "certificate_generation": True,
    "multi_language": False,
    "dark_mode": True
}

# ============================================================================
# SYSTEM CONFIGURATION
# ============================================================================
SYSTEM = {
    "debug_mode": os.getenv("DEBUG", "false").lower() == "true",
    "log_level": os.getenv("LOG_LEVEL", "INFO"),
    "max_file_size": 50 * 1024 * 1024,  # 50MB
    "allowed_file_types": ["jpg", "jpeg", "png", "pdf", "doc", "docx"],
    "backup_retention_days": 30,
    "maintenance_mode": False,
    "version": "2.0.0"
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def get_course_by_id(course_id: str) -> Dict[str, Any]:
    """Get course information by ID"""
    return COURSES.get(course_id, {})

def get_all_courses() -> List[Dict[str, Any]]:
    """Get all available courses"""
    return list(COURSES.values())

def get_active_courses() -> List[Dict[str, Any]]:
    """Get only active courses"""
    return [course for course in COURSES.values() if course.get("status") == "active"]

def get_free_courses() -> List[Dict[str, Any]]:
    """Get free courses"""
    return [course for course in COURSES.values() if course.get("price", 0) == 0]

def get_premium_courses() -> List[Dict[str, Any]]:
    """Get premium (paid) courses"""
    return [course for course in COURSES.values() if course.get("price", 0) > 0]

def format_price(price: int, currency: str = "تومان") -> str:
    """Format price with proper Persian formatting"""
    if price == 0:
        return "رایگان"
    return f"{price:,} {currency}"

def get_user_level(points: int) -> str:
    """Get user level based on points"""
    if points >= 5000:
        return "master"
    elif points >= 1000:
        return "expert"
    elif points >= 500:
        return "learner"
    elif points >= 100:
        return "regular"
    else:
        return "newcomer"

def get_badge_info(level: str) -> Dict[str, Any]:
    """Get badge information for user level"""
    return GAMIFICATION["badges"].get(level, {})

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================
def validate_phone(phone: str) -> bool:
    """Validate Iranian phone number"""
    import re
    patterns = [
        r'^\+98[0-9]{10}$',  # +98xxxxxxxxxx
        r'^09[0-9]{9}$',     # 09xxxxxxxxx
        r'^9[0-9]{9}$'       # 9xxxxxxxxx
    ]
    return any(re.match(pattern, phone) for pattern in patterns)

def validate_email(email: str) -> bool:
    """Validate email address"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_grade(grade: str) -> bool:
    """Validate grade selection"""
    return grade in ["9", "10", "11"]

def validate_field(field: str) -> bool:
    """Validate field selection"""
    return field in ["ریاضی", "تجربی", "انسانی"]

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def get_current_time() -> str:
    """Get current time in Persian format"""
    from datetime import datetime
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

def calculate_age(birth_date: str) -> int:
    """Calculate age from birth date"""
    from datetime import datetime
    birth = datetime.strptime(birth_date, "%Y-%m-%d")
    today = datetime.now()
    return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

def format_duration(seconds: int) -> str:
    """Format duration in human readable format"""
    if seconds < 60:
        return f"{seconds} ثانیه"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} دقیقه"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours} ساعت و {minutes} دقیقه"

# ============================================================================
# CONSTANTS
# ============================================================================
GRADES = {
    "9": "پایه ۹",
    "10": "پایه ۱۰", 
    "11": "پایه ۱۱"
}

FIELDS = {
    "ریاضی": "mathematics",
    "تجربی": "biology", 
    "انسانی": "humanities"
}

CITIES = [
    "تهران", "مشهد", "اصفهان", "شیراز", "تبریز", "قم", "اهواز", "کرج",
    "کرمانشاه", "ارومیه", "یزد", "اصفهان", "قم", "کاشان", "ساری"
]

LANGUAGES = {
    "fa": "فارسی",
    "en": "English",
    "ar": "العربية"
}

TIMEZONES = {
    "IRST": "Asia/Tehran",
    "UTC": "UTC"
}

# ============================================================================
# ERROR MESSAGES
# ============================================================================
ERROR_MESSAGES = {
    "invalid_phone": "شماره تلفن نامعتبر است. لطفاً شماره معتبر وارد کنید.",
    "invalid_email": "ایمیل نامعتبر است. لطفاً ایمیل معتبر وارد کنید.",
    "invalid_grade": "پایه تحصیلی نامعتبر است.",
    "invalid_field": "رشته تحصیلی نامعتبر است.",
    "user_not_found": "کاربر یافت نشد.",
    "course_not_found": "دوره یافت نشد.",
    "insufficient_points": "امتیاز کافی ندارید.",
    "maintenance_mode": "ربات در حال تعمیر است. لطفاً بعداً تلاش کنید.",
    "rate_limit_exceeded": "تعداد درخواست‌های شما بیش از حد مجاز است.",
    "permission_denied": "شما مجوز انجام این عملیات را ندارید."
}

SUCCESS_MESSAGES = {
    "registration_complete": "ثبت‌نام شما با موفقیت انجام شد!",
    "course_enrolled": "شما با موفقیت در دوره ثبت‌نام شدید!",
    "points_earned": "امتیاز شما با موفقیت اضافه شد!",
    "badge_earned": "شما یک نشان جدید کسب کردید!",
    "profile_updated": "پروفایل شما با موفقیت به‌روزرسانی شد!",
    "feedback_sent": "نظر شما با موفقیت ارسال شد!"
} 