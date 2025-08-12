#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    DateTime,
    Enum,
    ForeignKey,
    UniqueConstraint,
    Index,
    JSON,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from database.db import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    first_name_enc: Mapped[str] = mapped_column(String(512))
    last_name_enc: Mapped[str] = mapped_column(String(512))
    phone_enc: Mapped[str] = mapped_column(String(512), nullable=True)
    province: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    city: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    grade: Mapped[str] = mapped_column(String(32), nullable=True, index=True)
    field_of_study: Mapped[str] = mapped_column(String(32), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class BannedUser(Base):
    __tablename__ = "banned_users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ProfileChange(Base):
    __tablename__ = "profile_changes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    field_name: Mapped[str] = mapped_column(String(64))
    old_value_enc: Mapped[str] = mapped_column(String(1024))
    new_value_enc: Mapped[str] = mapped_column(String(1024))
    changed_by: Mapped[int] = mapped_column(Integer)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )


class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(256))
    type: Mapped[str] = mapped_column(String(16))  # free|paid
    grade: Mapped[str] = mapped_column(String(32), nullable=True)
    price: Mapped[int] = mapped_column(Integer, default=0)
    extra: Mapped[dict] = mapped_column(JSON, default={})


class Purchase(Base):
    __tablename__ = "purchases"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    product_type: Mapped[str] = mapped_column(String(16))  # book|course
    product_id: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(
        String(16), index=True
    )  # pending|approved|rejected
    admin_action_by: Mapped[int] = mapped_column(BigInteger, nullable=True)
    admin_action_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    notes_enc: Mapped[str] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    __table_args__ = (
        # Prevent duplicate product entries per user (single row updates status)
        UniqueConstraint(
            "user_id", "product_type", "product_id", name="uq_user_product"
        ),
        # Speed up common filters
        Index("ix_purchases_user_status", "user_id", "status"),
        Index("ix_purchases_created_at", "created_at"),
        # Enforce that decisions include admin attribution
        # (status='pending') OR (admin_action_by IS NOT NULL AND admin_action_at IS NOT NULL)
    )


class Receipt(Base):
    __tablename__ = "receipts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchase_id: Mapped[int] = mapped_column(
        ForeignKey("purchases.id", ondelete="CASCADE"), index=True
    )
    telegram_file_id: Mapped[str] = mapped_column(String(256))
    file_unique_id: Mapped[str] = mapped_column(String(128))
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    duplicate_checked: Mapped[bool] = mapped_column(Integer, default=0)
    __table_args__ = (UniqueConstraint("file_unique_id", name="uq_file_unique_id"),)


class PurchaseAudit(Base):
    __tablename__ = "purchase_audits"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchase_id: Mapped[int] = mapped_column(Integer, index=True)
    admin_id: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(16))  # approve|reject
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ---------------------
# Learning: Quiz content and progress
# ---------------------


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grade: Mapped[str] = mapped_column(String(32), index=True)
    difficulty: Mapped[int] = mapped_column(Integer, default=1, index=True)
    question_text: Mapped[str] = mapped_column(String(2048))
    options: Mapped[dict] = mapped_column(JSON)  # {"choices": ["A","B",...]} (max 8)
    correct_index: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index("ix_quiz_grade_diff", "grade", "difficulty"),
    )


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("quiz_questions.id", ondelete="CASCADE"), index=True)
    selected_index: Mapped[int] = mapped_column(Integer)
    correct: Mapped[int] = mapped_column(Integer, default=0)  # 0/1
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class UserStats(Base):
    __tablename__ = "user_stats"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    total_attempts: Mapped[int] = mapped_column(Integer, default=0)
    total_correct: Mapped[int] = mapped_column(Integer, default=0)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    last_attempt_date: Mapped[str] = mapped_column(String(10), nullable=True)  # YYYY-MM-DD
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
