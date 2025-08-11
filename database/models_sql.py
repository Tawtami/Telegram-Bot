#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
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
    telegram_user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    first_name_enc: Mapped[str] = mapped_column(String(512))
    last_name_enc: Mapped[str] = mapped_column(String(512))
    phone_enc: Mapped[str] = mapped_column(String(512), nullable=True)
    province: Mapped[str] = mapped_column(String(128), nullable=True)
    city: Mapped[str] = mapped_column(String(128), nullable=True)
    grade: Mapped[str] = mapped_column(String(32), nullable=True)
    field_of_study: Mapped[str] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


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
    admin_action_by: Mapped[int] = mapped_column(Integer, nullable=True)
    admin_action_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    notes_enc: Mapped[str] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    __table_args__ = (Index("ix_purchases_status", "status"),)


class Receipt(Base):
    __tablename__ = "receipts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchase_id: Mapped[int] = mapped_column(
        ForeignKey("purchases.id", ondelete="CASCADE"), index=True
    )
    telegram_file_id: Mapped[str] = mapped_column(String(256))
    file_unique_id: Mapped[str] = mapped_column(String(128), index=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    duplicate_checked: Mapped[bool] = mapped_column(Integer, default=0)
    __table_args__ = (
        UniqueConstraint("file_unique_id", name="uq_file_unique_id"),
        Index("ix_receipts_file_unique_id", "file_unique_id"),
    )


class PurchaseAudit(Base):
    __tablename__ = "purchase_audits"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchase_id: Mapped[int] = mapped_column(Integer, index=True)
    admin_id: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(16))  # approve|reject
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
