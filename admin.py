#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Admin Utility for Math Course Registration Bot
ابزار مدیریت ربات ثبت‌نام کلاس‌های ریاضی
"""

import json
import os
from datetime import datetime
from config import DATA_FILE

def load_students():
    """Load students data from JSON file"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ فایل داده‌ها یافت نشد!")
        return []

def save_students(students):
    """Save students data to JSON file"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(students, f, ensure_ascii=False, indent=2)

def display_students():
    """Display all registered students"""
    students = load_students()
    
    if not students:
        print("📭 هیچ دانش‌آموزی ثبت‌نام نکرده است.")
        return
    
    print(f"📊 تعداد کل دانش‌آموزان: {len(students)}")
    print("=" * 50)
    
    for i, student in enumerate(students, 1):
        print(f"\n👤 دانش‌آموز {i}:")
        print(f"   نام: {student['name']} {student['lastname']}")
        print(f"   پایه: {student['grade']}")
        print(f"   رشته: {student['field']}")
        print(f"   شهر: {student['city']}")
        print(f"   شماره: {student['phone']}")
        print(f"   تاریخ ثبت‌نام: {student['registration_date']}")
        print("-" * 30)

def search_student():
    """Search for a specific student"""
    students = load_students()
    
    if not students:
        print("📭 هیچ دانش‌آموزی ثبت‌نام نکرده است.")
        return
    
    search_term = input("🔍 نام یا شماره دانش‌آموز را وارد کنید: ").strip()
    
    found_students = []
    for student in students:
        if (search_term.lower() in student['name'].lower() or 
            search_term.lower() in student['lastname'].lower() or
            search_term in student['phone']):
            found_students.append(student)
    
    if not found_students:
        print("❌ دانش‌آموزی یافت نشد!")
        return
    
    print(f"✅ {len(found_students)} دانش‌آموز یافت شد:")
    for student in found_students:
        print(f"\n👤 {student['name']} {student['lastname']}")
        print(f"   پایه: {student['grade']} - رشته: {student['field']}")
        print(f"   شهر: {student['city']}")
        print(f"   شماره: {student['phone']}")

def export_to_csv():
    """Export students data to CSV file"""
    students = load_students()
    
    if not students:
        print("📭 هیچ دانش‌آموزی برای export وجود ندارد.")
        return
    
    import csv
    
    filename = f"students_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['نام', 'نام خانوادگی', 'پایه', 'رشته', 'شهر', 'شماره', 'تاریخ ثبت‌نام']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for student in students:
            writer.writerow({
                'نام': student['name'],
                'نام خانوادگی': student['lastname'],
                'پایه': student['grade'],
                'رشته': student['field'],
                'شهر': student['city'],
                'شماره': student['phone'],
                'تاریخ ثبت‌نام': student['registration_date']
            })
    
    print(f"✅ داده‌ها در فایل {filename} ذخیره شد.")

def statistics():
    """Show registration statistics"""
    students = load_students()
    
    if not students:
        print("📭 هیچ دانش‌آموزی ثبت‌نام نکرده است.")
        return
    
    # Grade statistics
    grades = {}
    fields = {}
    
    for student in students:
        grade = student['grade']
        field = student['field']
        
        grades[grade] = grades.get(grade, 0) + 1
        fields[field] = fields.get(field, 0) + 1
    
    print("📊 آمار ثبت‌نام:")
    print("=" * 30)
    print(f"📈 تعداد کل: {len(students)}")
    
    print("\n📚 بر اساس پایه:")
    for grade, count in grades.items():
        print(f"   {grade}: {count} نفر")
    
    print("\n🎯 بر اساس رشته:")
    for field, count in fields.items():
        print(f"   {field}: {count} نفر")

def delete_student():
    """Delete a student from the database"""
    students = load_students()
    
    if not students:
        print("📭 هیچ دانش‌آموزی ثبت‌نام نکرده است.")
        return
    
    display_students()
    
    try:
        index = int(input("\n🔢 شماره دانش‌آموز برای حذف (0 برای لغو): ")) - 1
        
        if index < 0 or index >= len(students):
            print("❌ شماره نامعتبر!")
            return
        
        student = students[index]
        confirm = input(f"⚠️ آیا از حذف {student['name']} {student['lastname']} اطمینان دارید؟ (y/n): ")
        
        if confirm.lower() == 'y':
            deleted_student = students.pop(index)
            save_students(students)
            print(f"✅ {deleted_student['name']} {deleted_student['lastname']} حذف شد.")
        else:
            print("❌ عملیات لغو شد.")
    
    except ValueError:
        print("❌ لطفاً یک عدد وارد کنید!")

def main_menu():
    """Display main admin menu"""
    while True:
        print("\n" + "=" * 50)
        print("🔧 پنل مدیریت ربات کلاس‌های ریاضی")
        print("=" * 50)
        print("1. 📊 نمایش همه دانش‌آموزان")
        print("2. 🔍 جستجوی دانش‌آموز")
        print("3. 📈 آمار ثبت‌نام")
        print("4. 📤 Export به CSV")
        print("5. 🗑️ حذف دانش‌آموز")
        print("0. ❌ خروج")
        
        choice = input("\n🔢 انتخاب کنید: ").strip()
        
        if choice == "1":
            display_students()
        elif choice == "2":
            search_student()
        elif choice == "3":
            statistics()
        elif choice == "4":
            export_to_csv()
        elif choice == "5":
            delete_student()
        elif choice == "0":
            print("👋 خداحافظ!")
            break
        else:
            print("❌ انتخاب نامعتبر!")

if __name__ == "__main__":
    main_menu() 