# -*- coding: utf-8 -*-
"""
Configuration file for Math Course Registration Bot
فایل تنظیمات ربات ثبت‌نام کلاس‌های ریاضی
"""

# Bot Configuration
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Replace with your actual bot token from @BotFather
BOT_NAME = "Ostad Hatami Bot"
BOT_USERNAME = "OstadHatami_bot"

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

# Special Courses (Free Online)
SPECIAL_COURSES = {
    "نظریه اعداد گسسته": {
        "target": "پایه دوازدهم ریاضی + المپیاد دهم و یازدهم",
        "start_date": "جمعه ۱۷ مرداد",
        "type": "آنلاین رایگان",
        "duration": "دوره کامل",
        "deadline": "۸ مرداد ماه"
    },
    "مهارت‌های حل خلاق مسائل": {
        "target": "پایه‌های دهم، یازدهم و دوازدهم",
        "schedule": "جمعه‌ها ساعت ۳ بعدازظهر",
        "type": "آنلاین رایگان",
        "platform": "اسکای روم"
    }
}

# Current Class Schedule
CURRENT_SCHEDULE = {
    "جمعه ۱۰ مرداد": {
        "time": "ساعت ۳ بعدازظهر",
        "participants": "پایه‌های دهم، یازدهم و دوازدهم",
        "subjects": "ریاضی و تجربی",
        "platform": "اسکای روم",
        "note": "حضور به موقع مهم است"
    }
}

# Class Capacity Status
CLASS_CAPACITY = {
    "پایه دهم": {"current": 21, "max": 29, "status": "در حال ثبت‌نام"},
    "پایه یازدهم": {"current": 23, "max": 29, "status": "در حال ثبت‌نام"},
    "پایه دوازدهم": {"current": 29, "max": 29, "status": "تکمیل شده"}
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
    "youtube": "youtube.com/@hamrahbaostad",
    "telegram_channel": "https://t.me/hamrahbaostad",
    "website": "Soon"
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

# Logging Configuration
LOG_LEVEL = "INFO" 