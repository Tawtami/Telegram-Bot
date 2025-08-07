#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data models for Ostad Hatami Bot
مدل‌های داده برای ربات استاد حاتمی
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class UserStatus(Enum):
    """User registration status"""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class CourseType(Enum):
    """Course types"""
    FREE = "free"
    PAID = "paid"


class PurchaseStatus(Enum):
    """Purchase status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class NotificationType(Enum):
    """Notification types"""
    COURSE_PURCHASE = "course_purchase"
    BOOK_PURCHASE = "book_purchase"
    PAYMENT_RECEIVED = "payment_received"


@dataclass
class UserData:
    """User registration data"""
    user_id: int
    first_name: str
    last_name: str
    grade: str
    major: str
    province: str
    city: str
    phone: str
    registration_date: str
    status: UserStatus = UserStatus.ACTIVE
    enrolled_courses: List[str] = None
    purchased_courses: List[str] = None
    purchased_books: List[str] = None

    def __post_init__(self):
        if self.enrolled_courses is None:
            self.enrolled_courses = []
        if self.purchased_courses is None:
            self.purchased_courses = []
        if self.purchased_books is None:
            self.purchased_books = []
        if not self.registration_date:
            self.registration_date = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserData":
        """Create from dictionary"""
        if "status" in data:
            data["status"] = UserStatus(data["status"])
        return cls(**data)

    def get_full_name(self) -> str:
        """Get full name"""
        return f"{self.first_name} {self.last_name}"

    def is_admin(self, admin_ids: List[int]) -> bool:
        """Check if user is admin"""
        return self.user_id in admin_ids


@dataclass
class CourseData:
    """Course information"""
    course_id: str
    title: str
    description: str
    course_type: CourseType
    price: int = 0  # 0 for free courses
    duration: str = ""
    schedule: str = ""
    max_students: int = 0
    current_students: int = 0
    is_active: bool = True
    created_date: str = ""

    def __post_init__(self):
        if not self.created_date:
            self.created_date = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["course_type"] = self.course_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CourseData":
        """Create from dictionary"""
        if "course_type" in data:
            data["course_type"] = CourseType(data["course_type"])
        return cls(**data)

    def is_full(self) -> bool:
        """Check if course is full"""
        return self.max_students > 0 and self.current_students >= self.max_students

    def can_enroll(self) -> bool:
        """Check if course can be enrolled"""
        return self.is_active and not self.is_full()


@dataclass
class PurchaseData:
    """Purchase information"""
    purchase_id: str
    user_id: int
    item_type: str  # "course" or "book"
    item_id: str
    amount: int
    status: PurchaseStatus = PurchaseStatus.PENDING
    payment_receipt: str = ""
    admin_notes: str = ""
    created_date: str = ""
    approved_date: str = ""
    admin_id: Optional[int] = None

    def __post_init__(self):
        if not self.created_date:
            self.created_date = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PurchaseData":
        """Create from dictionary"""
        if "status" in data:
            data["status"] = PurchaseStatus(data["status"])
        return cls(**data)


@dataclass
class NotificationData:
    """Admin notification data"""
    notification_id: str
    notification_type: NotificationType
    user_id: int
    message: str
    data: Dict[str, Any] = None
    is_read: bool = False
    created_date: str = ""

    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if not self.created_date:
            self.created_date = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["notification_type"] = self.notification_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NotificationData":
        """Create from dictionary"""
        if "notification_type" in data:
            data["notification_type"] = NotificationType(data["notification_type"])
        return cls(**data)


@dataclass
class BookData:
    """Book information"""
    book_id: str
    title: str
    description: str
    price: int
    author: str
    pages: int
    features: List[str] = None
    is_available: bool = True
    created_date: str = ""

    def __post_init__(self):
        if self.features is None:
            self.features = []
        if not self.created_date:
            self.created_date = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BookData":
        """Create from dictionary"""
        return cls(**data)
