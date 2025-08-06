#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data models for Ostad Hatami Bot
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class UserStatus(Enum):
    """User registration status"""

    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class CourseType(Enum):
    """Course types"""

    FREE = "free"
    PAID = "paid"
    PREMIUM = "premium"


@dataclass
class UserData:
    """User registration data model"""

    user_id: int
    first_name: str
    last_name: str
    grade: str
    major: str
    province: str
    city: str
    phone: str
    status: UserStatus = UserStatus.PENDING
    registration_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    last_login: Optional[datetime] = None
    login_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.registration_date is None:
            self.registration_date = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "user_id": self.user_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "grade": self.grade,
            "major": self.major,
            "province": self.province,
            "city": self.city,
            "phone": self.phone,
            "status": self.status.value,
            "registration_date": (
                self.registration_date.isoformat() if self.registration_date else None
            ),
            "last_updated": (
                self.last_updated.isoformat() if self.last_updated else None
            ),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "login_count": self.login_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserData":
        """Create UserData from dictionary"""
        # Parse dates
        registration_date = None
        if data.get("registration_date"):
            registration_date = datetime.fromisoformat(data["registration_date"])

        last_updated = None
        if data.get("last_updated"):
            last_updated = datetime.fromisoformat(data["last_updated"])

        last_login = None
        if data.get("last_login"):
            last_login = datetime.fromisoformat(data["last_login"])

        return cls(
            user_id=data["user_id"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            grade=data["grade"],
            major=data["major"],
            province=data["province"],
            city=data["city"],
            phone=data["phone"],
            status=UserStatus(data.get("status", "pending")),
            registration_date=registration_date,
            last_updated=last_updated,
            last_login=last_login,
            login_count=data.get("login_count", 0),
            metadata=data.get("metadata", {}),
        )

    def update_login(self):
        """Update login information"""
        self.last_login = datetime.now()
        self.login_count += 1
        self.last_updated = datetime.now()

    def get_full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"

    def is_active(self) -> bool:
        """Check if user is active"""
        return self.status == UserStatus.ACTIVE


@dataclass
class CourseData:
    """Course information data model"""

    course_id: str
    name: str
    description: str
    course_type: CourseType
    grade_level: str
    major: str
    max_students: int
    current_students: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    schedule: Dict[str, Any] = field(default_factory=dict)
    price: Optional[float] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "course_id": self.course_id,
            "name": self.name,
            "description": self.description,
            "course_type": self.course_type.value,
            "grade_level": self.grade_level,
            "major": self.major,
            "max_students": self.max_students,
            "current_students": self.current_students,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "schedule": self.schedule,
            "price": self.price,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CourseData":
        """Create CourseData from dictionary"""
        # Parse dates
        start_date = None
        if data.get("start_date"):
            start_date = datetime.fromisoformat(data["start_date"])

        end_date = None
        if data.get("end_date"):
            end_date = datetime.fromisoformat(data["end_date"])

        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        updated_at = None
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])

        return cls(
            course_id=data["course_id"],
            name=data["name"],
            description=data["description"],
            course_type=CourseType(data.get("course_type", "free")),
            grade_level=data["grade_level"],
            major=data["major"],
            max_students=data["max_students"],
            current_students=data.get("current_students", 0),
            start_date=start_date,
            end_date=end_date,
            schedule=data.get("schedule", {}),
            price=data.get("price"),
            is_active=data.get("is_active", True),
            created_at=created_at,
            updated_at=updated_at,
            metadata=data.get("metadata", {}),
        )

    def is_full(self) -> bool:
        """Check if course is full"""
        return self.current_students >= self.max_students

    def has_available_seats(self) -> bool:
        """Check if course has available seats"""
        return self.current_students < self.max_students

    def get_availability_percentage(self) -> float:
        """Get course availability percentage"""
        if self.max_students == 0:
            return 0.0
        return (self.current_students / self.max_students) * 100

    def is_free(self) -> bool:
        """Check if course is free"""
        return self.course_type == CourseType.FREE or self.price == 0

    def update_student_count(self, count: int):
        """Update student count"""
        self.current_students = max(0, self.current_students + count)
        self.updated_at = datetime.now()


@dataclass
class RegistrationData:
    """Course registration data model"""

    registration_id: str
    user_id: int
    course_id: str
    registration_date: datetime
    status: str = "pending"  # pending, confirmed, cancelled, completed
    payment_status: Optional[str] = None
    payment_amount: Optional[float] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "registration_id": self.registration_id,
            "user_id": self.user_id,
            "course_id": self.course_id,
            "registration_date": self.registration_date.isoformat(),
            "status": self.status,
            "payment_status": self.payment_status,
            "payment_amount": self.payment_amount,
            "notes": self.notes,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RegistrationData":
        """Create RegistrationData from dictionary"""
        registration_date = datetime.fromisoformat(data["registration_date"])

        return cls(
            registration_id=data["registration_id"],
            user_id=data["user_id"],
            course_id=data["course_id"],
            registration_date=registration_date,
            status=data.get("status", "pending"),
            payment_status=data.get("payment_status"),
            payment_amount=data.get("payment_amount"),
            notes=data.get("notes"),
            metadata=data.get("metadata", {}),
        )
