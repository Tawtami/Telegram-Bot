#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON storage utility for Ostad Hatami Bot
Thread-safe file operations with proper locking
"""

import os
import base64
import json
import time
import threading
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from utils.crypto import crypto_manager
except Exception:
    crypto_manager = None  # type: ignore[assignment]


class StudentStorage:
    """Thread-safe JSON storage for student data with caching"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.students_file = self.data_dir / "students.json"
        self.courses_file = self.data_dir / "courses.json"
        self.purchases_file = self.data_dir / "purchases.json"
        self.banned_file = self.data_dir / "banned.json"
        # Use a re-entrant lock to guard file writes and read-modify-write sequences
        self.lock = threading.RLock()
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minutes
        self._last_cache_update: Dict[str, float] = {}
        self._initialize_files()

    def _initialize_files(self):
        """Initialize JSON files with proper structure"""
        self.data_dir.mkdir(exist_ok=True)

        # Initialize students.json
        if not self.students_file.exists():
            self._save_json(self.students_file, {"students": []}, update_cache=False)

        # Do not initialize courses.json here; it is a data source list managed separately

        # Initialize purchases.json
        if not self.purchases_file.exists():
            self._save_json(self.purchases_file, {"purchases": []}, update_cache=False)

        # Initialize banned.json
        if not self.banned_file.exists():
            self._save_json(self.banned_file, {"banned_user_ids": []}, update_cache=False)

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

    def _save_json(self, file_path: Path, data: Dict[str, Any], update_cache: bool = True):
        """Save JSON file safely and optionally update cache"""
        try:
            with self.lock:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                # Update cache (optional, skip during initialization)
                if update_cache:
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
            # Validate required fields
            required_fields = [
                "user_id",
                "first_name",
                "last_name",
                "province",
                "city",
                "grade",
                "field",
            ]
            for field in required_fields:
                if field not in student_data or not student_data[field]:
                    logger.error(f"Missing required field: {field}")
                    return False

            # Validate user_id is integer
            try:
                user_id = int(student_data["user_id"])
            except (ValueError, TypeError):
                logger.error(f"Invalid user_id: {student_data['user_id']}")
                return False

            # Perform read-modify-write under the same lock for thread safety
            with self.lock:
                data = self._load_json(self.students_file)
                students = data.get("students", [])

            # Check if student already exists
            existing_index = None
            for i, student in enumerate(students):
                if student.get("user_id") == user_id:
                    existing_index = i
                    break

            # Encrypt sensitive fields before saving
            sensitive_fields = ["first_name", "last_name", "phone_number"]
            if crypto_manager is not None:
                for field in sensitive_fields:
                    if field in student_data and student_data[field]:
                        try:
                            encrypted_value = crypto_manager.encrypt_text(str(student_data[field]))
                            # Normalize to JSON-serializable string
                            if isinstance(encrypted_value, bytes):
                                encrypted_value = base64.urlsafe_b64encode(encrypted_value).decode(
                                    "utf-8"
                                )
                            elif not isinstance(encrypted_value, str):
                                encrypted_value = str(encrypted_value)
                            student_data[field] = encrypted_value
                        except Exception:
                            # If encryption fails for any reason, keep original value to avoid data loss
                            pass

                # Add timestamp
                student_data["last_updated"] = datetime.now().isoformat()
                if existing_index is None:
                    student_data["registration_date"] = datetime.now().isoformat()
                    students.append(student_data)
                else:
                    students[existing_index] = student_data

                # Save updated data
                self._save_json(self.students_file, {"students": students})
                logger.info(f"Student data saved/updated for user {user_id}")
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
                    # Decrypt sensitive fields on read
                    if crypto_manager is not None:
                        for field in ("first_name", "last_name", "phone_number"):
                            if field in student and student[field]:
                                try:
                                    student[field] = crypto_manager.decrypt_text(student[field])
                                except Exception:
                                    # If not encrypted (legacy), leave as is
                                    pass
                    return student
            return None
        except Exception as e:
            logger.error(f"Error getting student data: {e}")
            return None

    def get_all_students(self) -> List[Dict[str, Any]]:
        """Get all students data"""
        try:
            data = self._load_json(self.students_file)
            students = data.get("students", [])
            # Decrypt sensitive fields for admin views/search
            if crypto_manager is not None:
                for s in students:
                    for field in ("first_name", "last_name", "phone_number"):
                        val = s.get(field)
                        if val:
                            try:
                                s[field] = crypto_manager.decrypt_text(val)
                            except Exception:
                                pass
            return students
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

            # Update last activity
            student["last_activity"] = datetime.now().isoformat()

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

            # Update last activity
            student["last_activity"] = datetime.now().isoformat()

            return self.save_student(student)
        except Exception as e:
            logger.error(f"Error adding pending payment: {e}")
            return False

    # -----------------------------
    # Ban management
    # -----------------------------
    def _load_banned(self) -> Dict[str, Any]:
        try:
            return self._load_json(self.banned_file) or {"banned_user_ids": []}
        except Exception:
            return {"banned_user_ids": []}

    def is_user_banned(self, user_id: int) -> bool:
        try:
            data = self._load_banned()
            return int(user_id) in set(data.get("banned_user_ids", []))
        except Exception:
            return False

    def ban_user(self, user_id: int) -> bool:
        try:
            data = self._load_banned()
            banned: list = list({int(x) for x in data.get("banned_user_ids", [])})
            if int(user_id) not in banned:
                banned.append(int(user_id))
            data["banned_user_ids"] = banned
            self._save_json(self.banned_file, data)
            return True
        except Exception as e:
            logger.error(f"Error banning user {user_id}: {e}")
            return False

    def unban_user(self, user_id: int) -> bool:
        try:
            data = self._load_banned()
            banned_set = {int(x) for x in data.get("banned_user_ids", [])}
            if int(user_id) in banned_set:
                banned_set.remove(int(user_id))
            data["banned_user_ids"] = list(banned_set)
            self._save_json(self.banned_file, data)
            return True
        except Exception as e:
            logger.error(f"Error unbanning user {user_id}: {e}")
            return False

    def get_user_courses(self, user_id: int) -> Dict[str, list]:
        """Get user's enrolled courses (both free and paid)"""
        try:
            student = self.get_student(user_id)
            if not student:
                return {"free_courses": [], "purchased_courses": []}

            return {
                "free_courses": student.get("free_courses", []),
                "purchased_courses": student.get("purchased_courses", []),
            }
        except Exception as e:
            logger.error(f"Error getting user courses: {e}")
            return {"free_courses": [], "purchased_courses": []}
