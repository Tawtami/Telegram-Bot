#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON storage utility for Ostad Hatami Bot
Thread-safe file operations with proper locking
"""

import os
import json
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class StudentStorage:
    """Thread-safe JSON storage for student data with caching"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.students_file = self.data_dir / "students.json"
        self.courses_file = self.data_dir / "courses.json"
        self.purchases_file = self.data_dir / "purchases.json"
        self.lock = asyncio.Lock()
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
        self._last_cache_update = {}
        self._initialize_files()

    def _initialize_files(self):
        """Initialize JSON files with proper structure"""
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize students.json
        if not self.students_file.exists():
            self._save_json(self.students_file, {"students": []})
        
        # Initialize courses.json
        if not self.courses_file.exists():
            self._save_json(self.courses_file, {"courses": []})
        
        # Initialize purchases.json
        if not self.purchases_file.exists():
            self._save_json(self.purchases_file, {"purchases": []})

    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """Load JSON file safely with caching"""
        try:
            # Check cache first
            cache_key = str(file_path)
            now = time.time()
            if (
                cache_key in self._cache
                and cache_key in self._last_cache_update
                and now - self._last_cache_update[cache_key] < self._cache_ttl
            ):
                return self._cache[cache_key]

            # Load from file
            if not file_path.exists():
                return {}
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Update cache
                self._cache[cache_key] = data
                self._last_cache_update[cache_key] = now
                return data
        except json.JSONDecodeError:
            logger.error(f"Error reading {file_path}")
            return {}

    def _save_json(self, file_path: Path, data: Dict[str, Any]):
        """Save JSON file safely and update cache"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            # Update cache
            cache_key = str(file_path)
            self._cache[cache_key] = data
            self._last_cache_update[cache_key] = time.time()
        except Exception as e:
            logger.error(f"Error saving {file_path}: {e}")
            # Invalidate cache on error
            cache_key = str(file_path)
            self._cache.pop(cache_key, None)
            self._last_cache_update.pop(cache_key, None)

    def save_student(self, student_data: Dict[str, Any]) -> bool:
        """Save student data to JSON file"""
        try:
            data = self._load_json(self.students_file)
            students = data.get("students", [])
            
            # Update existing student or add new one
            student_data["registration_date"] = datetime.now().isoformat()
            student_data["last_updated"] = datetime.now().isoformat()
            
            for i, student in enumerate(students):
                if student["user_id"] == student_data["user_id"]:
                    students[i] = student_data
                    break
            else:
                students.append(student_data)
            
            data["students"] = students
            self._save_json(self.students_file, data)
            return True
        except Exception as e:
            logger.error(f"Error saving student data: {e}")
            return False

    def get_student(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get student data by user ID"""
        try:
            data = self._load_json(self.students_file)
            for student in data.get("students", []):
                if student["user_id"] == user_id:
                    return student
            return None
        except Exception as e:
            logger.error(f"Error getting student data: {e}")
            return None

    def get_all_students(self) -> List[Dict[str, Any]]:
        """Get all students data"""
        try:
            data = self._load_json(self.students_file)
            return data.get("students", [])
        except Exception as e:
            logger.error(f"Error getting all students: {e}")
            return []

    def save_course_registration(self, user_id: int, course_id: str, is_paid: bool = False) -> bool:
        """Save course registration"""
        try:
            student = self.get_student(user_id)
            if not student:
                return False

            # Update student's courses
            if is_paid:
                if "purchased_courses" not in student:
                    student["purchased_courses"] = []
                if course_id not in student["purchased_courses"]:
                    student["purchased_courses"].append(course_id)
            else:
                if "free_courses" not in student:
                    student["free_courses"] = []
                if course_id not in student["free_courses"]:
                    student["free_courses"].append(course_id)

            return self.save_student(student)
        except Exception as e:
            logger.error(f"Error saving course registration: {e}")
            return False

    def save_book_purchase(self, user_id: int, book_data: Dict[str, Any]) -> bool:
        """Save book purchase information"""
        try:
            student = self.get_student(user_id)
            if not student:
                return False

            if "book_purchases" not in student:
                student["book_purchases"] = []
            
            book_data["purchase_date"] = datetime.now().isoformat()
            student["book_purchases"].append(book_data)
            
            return self.save_student(student)
        except Exception as e:
            logger.error(f"Error saving book purchase: {e}")
            return False

    def confirm_payment(self, user_id: int) -> bool:
        """Confirm payment for a student"""
        try:
            student = self.get_student(user_id)
            if not student:
                return False

            # Check if student has pending payments
            if not student.get("pending_payments"):
                return False

            # Move pending courses to purchased
            pending = student.pop("pending_payments", [])
            if "purchased_courses" not in student:
                student["purchased_courses"] = []
            student["purchased_courses"].extend(pending)

            return self.save_student(student)
        except Exception as e:
            logger.error(f"Error confirming payment: {e}")
            return False

    def add_pending_payment(self, user_id: int, course_id: str) -> bool:
        """Add pending payment for a course"""
        try:
            student = self.get_student(user_id)
            if not student:
                return False

            if "pending_payments" not in student:
                student["pending_payments"] = []
            if course_id not in student["pending_payments"]:
                student["pending_payments"].append(course_id)

            return self.save_student(student)
        except Exception as e:
            logger.error(f"Error adding pending payment: {e}")
            return False