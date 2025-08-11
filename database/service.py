#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import datetime as dt
from typing import Optional, Tuple, List, Dict

from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.db import session_scope
from database.models_sql import User, ProfileChange, Purchase, Receipt, PurchaseAudit
from utils.crypto import crypto_manager


# ---------------------
# User Management
# ---------------------


def encrypt_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return crypto_manager.encrypt_text(str(value))


def get_or_create_user(
    session: Session,
    telegram_user_id: int,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    grade: Optional[str] = None,
    field_of_study: Optional[str] = None,
) -> User:
    user: Optional[User] = session.execute(
        select(User).where(User.telegram_user_id == telegram_user_id)
    ).scalar_one_or_none()
    if user is None:
        user = User(
            telegram_user_id=telegram_user_id,
            first_name_enc=encrypt_text(first_name),
            last_name_enc=encrypt_text(last_name),
            phone_enc=encrypt_text(phone),
            province=province or "",
            city=city or "",
            grade=grade or "",
            field_of_study=field_of_study or "",
        )
        session.add(user)
        session.flush()
        return user

    # Update fields if provided
    changed = False
    if first_name is not None:
        user.first_name_enc = encrypt_text(first_name)
        changed = True
    if last_name is not None:
        user.last_name_enc = encrypt_text(last_name)
        changed = True
    if phone is not None:
        user.phone_enc = encrypt_text(phone)
        changed = True
    if province is not None:
        user.province = province
        changed = True
    if city is not None:
        user.city = city
        changed = True
    if grade is not None:
        user.grade = grade
        changed = True
    if field_of_study is not None:
        user.field_of_study = field_of_study
        changed = True
    if changed:
        session.flush()
    return user


def audit_profile_change(
    session: Session,
    user_id: int,
    field_name: str,
    old_value: Optional[str],
    new_value: Optional[str],
    changed_by: int,
) -> None:
    session.add(
        ProfileChange(
            user_id=user_id,
            field_name=field_name,
            old_value_enc=encrypt_text(old_value),
            new_value_enc=encrypt_text(new_value),
            changed_by=changed_by,
        )
    )


# ---------------------
# Purchases & Receipts
# ---------------------


def create_purchase(
    session: Session,
    user_id: int,
    product_type: str,
    product_id: str,
    status: str = "pending",
    notes: Optional[str] = None,
) -> Purchase:
    purchase = Purchase(
        user_id=user_id,
        product_type=product_type,
        product_id=product_id,
        status=status,
        notes_enc=encrypt_text(notes) if notes else None,
    )
    session.add(purchase)
    session.flush()
    return purchase


def add_receipt(
    session: Session,
    purchase_id: int,
    telegram_file_id: str,
    file_unique_id: str,
) -> Tuple[bool, Optional[Receipt]]:
    # Deduplicate by unique constraint
    receipt = Receipt(
        purchase_id=purchase_id,
        telegram_file_id=telegram_file_id,
        file_unique_id=file_unique_id,
    )
    session.add(receipt)
    try:
        session.flush()
        return True, receipt
    except IntegrityError:
        session.rollback()
        return False, None


def approve_or_reject_purchase(
    session: Session, purchase_id: int, admin_id: int, decision: str
) -> Optional[Purchase]:
    # Atomic state transition: only from pending
    now = dt.datetime.utcnow()
    result = session.execute(
        update(Purchase)
        .where(Purchase.id == purchase_id, Purchase.status == "pending")
        .values(
            status=("approved" if decision == "approve" else "rejected"),
            admin_action_by=admin_id,
            admin_action_at=now,
        )
        .returning(
            Purchase.id,
            Purchase.user_id,
            Purchase.product_type,
            Purchase.product_id,
            Purchase.status,
        )
    ).first()
    if not result:
        return None

    # Write audit record
    session.add(
        PurchaseAudit(purchase_id=purchase_id, admin_id=admin_id, action=decision)
    )
    session.flush()
    # Build lightweight object
    p = Purchase(
        id=result.id,
        user_id=result.user_id,
        product_type=result.product_type,
        product_id=result.product_id,
        status=result.status,
    )
    return p


# ---------------------
# Lists
# ---------------------


def get_approved_book_buyers(session: Session, limit: int = 100) -> List[Dict]:
    q = session.execute(
        select(Purchase.user_id, Purchase.product_id, Purchase.created_at)
        .where(Purchase.product_type == "book", Purchase.status == "approved")
        .order_by(Purchase.created_at.desc())
        .limit(limit)
    )
    return [
        {"user_id": r.user_id, "product_id": r.product_id, "created_at": r.created_at}
        for r in q
    ]


def get_pending_purchases(session: Session, limit: int = 100) -> List[Dict]:
    q = session.execute(
        select(
            Purchase.id,
            Purchase.user_id,
            Purchase.product_type,
            Purchase.product_id,
            Purchase.created_at,
        )
        .where(Purchase.status == "pending")
        .order_by(Purchase.created_at.desc())
        .limit(limit)
    )
    return [
        {
            "purchase_id": r.id,
            "user_id": r.user_id,
            "product_type": r.product_type,
            "product_id": r.product_id,
            "created_at": r.created_at,
        }
        for r in q
    ]


def get_course_participants_by_slug(
    session: Session, course_slug: str, status: str = "approved"
) -> List[int]:
    q = session.execute(
        select(Purchase.user_id)
        .where(
            Purchase.product_type == "course",
            Purchase.product_id == course_slug,
            Purchase.status == status,
        )
        .order_by(Purchase.created_at.desc())
    )
    return [r.user_id for r in q]


def get_free_course_participants_by_grade(
    session: Session, grade: str, status: str = "approved"
) -> List[int]:
    # Without joining courses table, assume product_id encodes slug with grade or ignore
    # Here we list all approved course purchases for users with the given grade
    from sqlalchemy import distinct

    q = session.execute(
        select(distinct(Purchase.user_id))
        .join(User, User.id == Purchase.user_id)
        .where(Purchase.product_type == "course", Purchase.status == status, User.grade == grade)
        .order_by(Purchase.created_at.desc())
    )
    return [r[0] for r in q]
