#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Manager for Ostad Hatami Bot
مدیریت داده برای ربات استاد حاتمی
"""

import json
import os
import uuid
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from .models import (
    UserData,
    CourseData,
    PurchaseData,
    NotificationData,
    BookData,
    UserStatus,
    CourseType,
    PurchaseStatus,
    NotificationType,
)


class DataManager:
    """Singleton data manager for JSON file storage"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

        # File paths
        self.users_file = self.data_dir / "users.json"
        self.courses_file = self.data_dir / "courses.json"
        self.purchases_file = self.data_dir / "purchases.json"
        self.notifications_file = self.data_dir / "notifications.json"
        self.books_file = self.data_dir / "books.json"

        # Initialize files if they don't exist
        self._initialize_files()

    def _initialize_files(self):
        """Initialize JSON files with proper structure"""
        # Initialize users file with 'students' wrapper as per specification
        if not self.users_file.exists():
            with open(self.users_file, "w", encoding="utf-8") as f:
                json.dump({"students": []}, f, ensure_ascii=False, indent=2)

        # Initialize other files with empty arrays
        other_files = [
            self.courses_file,
            self.purchases_file,
            self.notifications_file,
            self.books_file,
        ]

        for file_path in other_files:
            if not file_path.exists():
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump([], f, ensure_ascii=False, indent=2)

    def _load_json(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load JSON file safely"""
        try:
            if not file_path.exists():
                return []
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Handle users file with 'students' wrapper
                if (
                    file_path == self.users_file
                    and isinstance(data, dict)
                    and "students" in data
                ):
                    return data["students"]
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_json(self, file_path: Path, data: List[Dict[str, Any]]):
        """Save JSON file safely"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                # Handle users file with 'students' wrapper
                if file_path == self.users_file:
                    json.dump({"students": data}, f, ensure_ascii=False, indent=2)
                else:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving {file_path}: {e}")

    # ============================================================================
    # USER MANAGEMENT
    # ============================================================================
    def save_user_data(self, user_data: Dict[str, Any]) -> bool:
        """Save user registration data"""
        try:
            users_data = self._load_json(self.users_file)

            # Check if user already exists
            existing_user = next(
                (
                    user
                    for user in users_data
                    if user.get("user_id") == user_data["user_id"]
                ),
                None,
            )

            if existing_user:
                # Update existing user
                existing_user.update(user_data)
            else:
                # Add new user
                users_data.append(user_data)

            self._save_json(self.users_file, users_data)
            return True

        except Exception as e:
            print(f"Error saving user data: {e}")
            return False

    def load_user_data(self, user_id: int) -> Optional[UserData]:
        """Load user data by user ID"""
        try:
            users_data = self._load_json(self.users_file)
            user_dict = next(
                (user for user in users_data if user.get("user_id") == user_id), None
            )

            if user_dict:
                return UserData.from_dict(user_dict)
            return None

        except Exception as e:
            print(f"Error loading user data: {e}")
            return None

    def user_exists(self, user_id: int) -> bool:
        """Check if user exists"""
        try:
            users_data = self._load_json(self.users_file)
            return any(user.get("user_id") == user_id for user in users_data)
        except Exception:
            return False

    async def get_all_users(self) -> List[UserData]:
        """Get all users"""
        try:
            users_data = self._load_json(self.users_file)
            return [UserData.from_dict(user) for user in users_data]
        except Exception as e:
            print(f"Error loading all users: {e}")
            return []

    async def update_user_courses(
        self, user_id: int, course_id: str, action: str = "add"
    ):
        """Update user's enrolled courses"""
        try:
            user = await self.load_user_data(user_id)
            if not user:
                return False

            if action == "add" and course_id not in user.enrolled_courses:
                user.enrolled_courses.append(course_id)
            elif action == "remove" and course_id in user.enrolled_courses:
                user.enrolled_courses.remove(course_id)

            await self.save_user_data(user.to_dict())
            return True

        except Exception as e:
            print(f"Error updating user courses: {e}")
            return False

    # ============================================================================
    # COURSE MANAGEMENT
    # ============================================================================
    async def save_course(self, course: CourseData) -> bool:
        """Save course data"""
        try:
            courses_data = self._load_json(self.courses_file)

            # Check if course already exists
            existing_course = next(
                (c for c in courses_data if c.get("course_id") == course.course_id),
                None,
            )

            if existing_course:
                # Update existing course
                existing_course.update(course.to_dict())
            else:
                # Add new course
                courses_data.append(course.to_dict())

            self._save_json(self.courses_file, courses_data)
            return True

        except Exception as e:
            print(f"Error saving course: {e}")
            return False

    async def get_course(self, course_id: str) -> Optional[CourseData]:
        """Get course by ID"""
        try:
            courses_data = self._load_json(self.courses_file)
            course_dict = next(
                (c for c in courses_data if c.get("course_id") == course_id), None
            )

            if course_dict:
                return CourseData.from_dict(course_dict)
            return None

        except Exception as e:
            print(f"Error loading course: {e}")
            return None

    async def get_all_courses(
        self, course_type: Optional[CourseType] = None
    ) -> List[CourseData]:
        """Get all courses, optionally filtered by type"""
        try:
            courses_data = self._load_json(self.courses_file)
            courses = [CourseData.from_dict(c) for c in courses_data]

            if course_type:
                courses = [c for c in courses if c.course_type == course_type]

            return courses

        except Exception as e:
            print(f"Error loading courses: {e}")
            return []

    async def update_course_students(self, course_id: str, change: int = 1):
        """Update course student count"""
        try:
            course = await self.get_course(course_id)
            if not course:
                return False

            course.current_students = max(0, course.current_students + change)
            await self.save_course(course)
            return True

        except Exception as e:
            print(f"Error updating course students: {e}")
            return False

    # ============================================================================
    # PURCHASE MANAGEMENT
    # ============================================================================
    async def save_purchase(self, purchase: PurchaseData) -> bool:
        """Save purchase data"""
        try:
            purchases_data = self._load_json(self.purchases_file)
            purchases_data.append(purchase.to_dict())
            self._save_json(self.purchases_file, purchases_data)
            return True

        except Exception as e:
            print(f"Error saving purchase: {e}")
            return False

    async def get_purchase(self, purchase_id: str) -> Optional[PurchaseData]:
        """Get purchase by ID"""
        try:
            purchases_data = self._load_json(self.purchases_file)
            purchase_dict = next(
                (p for p in purchases_data if p.get("purchase_id") == purchase_id), None
            )

            if purchase_dict:
                return PurchaseData.from_dict(purchase_dict)
            return None

        except Exception as e:
            print(f"Error loading purchase: {e}")
            return None

    async def get_user_purchases(
        self, user_id: int, status: Optional[PurchaseStatus] = None
    ) -> List[PurchaseData]:
        """Get user's purchases"""
        try:
            purchases_data = self._load_json(self.purchases_file)
            purchases = [
                PurchaseData.from_dict(p)
                for p in purchases_data
                if p.get("user_id") == user_id
            ]

            if status:
                purchases = [p for p in purchases if p.status == status]

            return purchases

        except Exception as e:
            print(f"Error loading user purchases: {e}")
            return []

    async def update_purchase_status(
        self,
        purchase_id: str,
        status: PurchaseStatus,
        admin_id: Optional[int] = None,
        notes: str = "",
    ):
        """Update purchase status"""
        try:
            purchase = await self.get_purchase(purchase_id)
            if not purchase:
                return False

            purchase.status = status
            purchase.admin_id = admin_id
            purchase.admin_notes = notes

            if status == PurchaseStatus.APPROVED:
                purchase.approved_date = datetime.now().isoformat()

            # Update in file
            purchases_data = self._load_json(self.purchases_file)
            for i, p in enumerate(purchases_data):
                if p.get("purchase_id") == purchase_id:
                    purchases_data[i] = purchase.to_dict()
                    break

            self._save_json(self.purchases_file, purchases_data)
            return True

        except Exception as e:
            print(f"Error updating purchase status: {e}")
            return False

    # ============================================================================
    # NOTIFICATION MANAGEMENT
    # ============================================================================
    async def save_notification(self, notification: NotificationData) -> bool:
        """Save notification"""
        try:
            notifications_data = self._load_json(self.notifications_file)
            notifications_data.append(notification.to_dict())
            self._save_json(self.notifications_file, notifications_data)
            return True

        except Exception as e:
            print(f"Error saving notification: {e}")
            return False

    async def get_unread_notifications(self) -> List[NotificationData]:
        """Get unread notifications"""
        try:
            notifications_data = self._load_json(self.notifications_file)
            unread = [n for n in notifications_data if not n.get("is_read", False)]
            return [NotificationData.from_dict(n) for n in unread]

        except Exception as e:
            print(f"Error loading notifications: {e}")
            return []

    async def mark_notification_read(self, notification_id: str):
        """Mark notification as read"""
        try:
            notifications_data = self._load_json(self.notifications_file)
            for notification in notifications_data:
                if notification.get("notification_id") == notification_id:
                    notification["is_read"] = True
                    break

            self._save_json(self.notifications_file, notifications_data)

        except Exception as e:
            print(f"Error marking notification read: {e}")

    # ============================================================================
    # BOOK MANAGEMENT
    # ============================================================================
    async def save_book(self, book: BookData) -> bool:
        """Save book data"""
        try:
            books_data = self._load_json(self.books_file)

            existing_book = next(
                (b for b in books_data if b.get("book_id") == book.book_id), None
            )

            if existing_book:
                existing_book.update(book.to_dict())
            else:
                books_data.append(book.to_dict())

            self._save_json(self.books_file, books_data)
            return True

        except Exception as e:
            print(f"Error saving book: {e}")
            return False

    async def get_book(self, book_id: str) -> Optional[BookData]:
        """Get book by ID"""
        try:
            books_data = self._load_json(self.books_file)
            book_dict = next(
                (b for b in books_data if b.get("book_id") == book_id), None
            )

            if book_dict:
                return BookData.from_dict(book_dict)
            return None

        except Exception as e:
            print(f"Error loading book: {e}")
            return None

    async def get_all_books(self) -> List[BookData]:
        """Get all books"""
        try:
            books_data = self._load_json(self.books_file)
            return [BookData.from_dict(b) for b in books_data]

        except Exception as e:
            print(f"Error loading books: {e}")
            return []

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            users = await self.get_all_users()
            courses = await self.get_all_courses()
            purchases = self._load_json(self.purchases_file)
            notifications = await self.get_unread_notifications()

            total_size = 0
            for file_path in [
                self.users_file,
                self.courses_file,
                self.purchases_file,
                self.notifications_file,
                self.books_file,
            ]:
                if file_path.exists():
                    total_size += file_path.stat().st_size

            return {
                "total_users": len(users),
                "total_courses": len(courses),
                "total_purchases": len(purchases),
                "unread_notifications": len(notifications),
                "total_size_mb": total_size / (1024 * 1024),
            }

        except Exception as e:
            print(f"Error getting database stats: {e}")
            return {}

    def generate_id(self) -> str:
        """Generate unique ID"""
        return str(uuid.uuid4())

    async def backup_data(self, backup_dir: str = "backups"):
        """Create backup of all data"""
        try:
            backup_path = Path(backup_dir)
            backup_path.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            files_to_backup = [
                self.users_file,
                self.courses_file,
                self.purchases_file,
                self.notifications_file,
                self.books_file,
            ]

            for file_path in files_to_backup:
                if file_path.exists():
                    backup_file = backup_path / f"{file_path.stem}_{timestamp}.json"
                    with open(file_path, "r", encoding="utf-8") as src:
                        with open(backup_file, "w", encoding="utf-8") as dst:
                            dst.write(src.read())

            return True

        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
