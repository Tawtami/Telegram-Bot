#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for user data saving and viewing system
اسکریپت تست برای سیستم ذخیره و مشاهده اطلاعات کاربران
"""

import json
import os
from datetime import datetime
from hosted_bot import ProfessionalDataManager

def test_data_system():
    """Test the data saving and viewing system"""
    print("🧪 تست سیستم ذخیره و مشاهده اطلاعات کاربران")
    print("=" * 50)
    
    # Initialize data manager
    data_manager = ProfessionalDataManager()
    
    # Test data
    test_students = [
        {
            "user_id": 123456789,
            "name": "احمد محمدی",
            "phone": "09123456789",
            "course": "نظریه اعداد و ریاضی گسسته",
            "grade": "پایه دوازدهم",
            "field": "ریاضی",
            "parent_phone": "09187654321",
            "type": "پولی",
            "status": "pending_payment"
        },
        {
            "user_id": 987654321,
            "name": "فاطمه احمدی",
            "phone": "09987654321",
            "course": "مهارت‌های حل خلاق مسائل ریاضی",
            "grade": "پایه یازدهم",
            "field": "تجربی",
            "parent_phone": "09123456789",
            "type": "رایگان",
            "status": "active"
        },
        {
            "user_id": 555666777,
            "name": "علی رضایی",
            "phone": "09351234567",
            "course": "کلاس‌های پایه دهم",
            "grade": "پایه دهم",
            "field": "ریاضی",
            "parent_phone": "09351234568",
            "type": "رایگان",
            "status": "active"
        }
    ]
    
    print("📝 اضافه کردن کاربران تست...")
    
    # Add test students
    for student in test_students:
        result = data_manager.add_student(student)
        print(f"✅ کاربر {result['name']} اضافه شد")
    
    print("\n📊 تست بارگذاری اطلاعات...")
    
    # Load and display students
    students = data_manager.load_students()
    print(f"👥 تعداد کل کاربران: {len(students)}")
    
    for i, student in enumerate(students, 1):
        print(f"\n{i}. 👤 {student.get('name', 'نامشخص')}")
        print(f"   📱 تلفن: {student.get('phone', 'نامشخص')}")
        print(f"   📚 کلاس: {student.get('course', 'نامشخص')}")
        print(f"   🎓 پایه: {student.get('grade', 'نامشخص')}")
        print(f"   📖 رشته: {student.get('field', 'نامشخص')}")
        print(f"   📞 تلفن والدین: {student.get('parent_phone', 'نامشخص')}")
        print(f"   💰 نوع: {student.get('type', 'نامشخص')}")
        print(f"   ✅ وضعیت: {student.get('status', 'نامشخص')}")
        print(f"   🆔 شناسه کاربر: {student.get('user_id', 'نامشخص')}")
    
    print("\n📋 تست خروجی خلاصه...")
    
    # Test export summary
    summary = data_manager.export_user_data_summary()
    print("📊 خلاصه اطلاعات:")
    print(summary)
    
    print("\n🔄 تست به‌روزرسانی کاربر...")
    
    # Test updating a student
    updates = {
        "status": "active",
        "last_updated": datetime.now().isoformat()
    }
    
    success = data_manager.update_student(123456789, updates)
    if success:
        print("✅ به‌روزرسانی کاربر موفق بود")
    else:
        print("❌ به‌روزرسانی کاربر ناموفق بود")
    
    print("\n🔍 تست جستجوی کاربر...")
    
    # Test getting student by user_id
    student = data_manager.get_student_by_user_id(123456789)
    if student:
        print(f"✅ کاربر پیدا شد: {student['name']}")
        print(f"   وضعیت جدید: {student['status']}")
    else:
        print("❌ کاربر پیدا نشد")
    
    print("\n📁 بررسی فایل‌های ذخیره شده...")
    
    # Check if files exist
    if os.path.exists("data/students.json"):
        print("✅ فایل students.json موجود است")
        with open("data/students.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"   تعداد رکوردها: {len(data)}")
    else:
        print("❌ فایل students.json موجود نیست")
    
    if os.path.exists("data/students_backup.json"):
        print("✅ فایل پشتیبان موجود است")
    else:
        print("⚠️ فایل پشتیبان موجود نیست")
    
    print("\n🎉 تست سیستم کامل شد!")
    print("\n📋 راهنمای استفاده:")
    print("1. برای مشاهده اطلاعات کاربران در ربات: /admin")
    print("2. برای خروجی اطلاعات: /export")
    print("3. فایل‌های ذخیره شده در پوشه data/")

if __name__ == "__main__":
    test_data_system() 