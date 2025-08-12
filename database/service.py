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
from database.models_sql import (
    User,
    ProfileChange,
    Purchase,
    Receipt,
    PurchaseAudit,
    BannedUser,
    QuizQuestion,
    QuizAttempt,
    UserStats,
)
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
        .where(
            Purchase.product_type == "course",
            Purchase.status == status,
            User.grade == grade,
        )
        .order_by(Purchase.created_at.desc())
    )
    return [r[0] for r in q]


# ---------------------
# Ban management (SQL)
# ---------------------


def is_user_banned(session: Session, telegram_user_id: int) -> bool:
    return (
        session.execute(
            select(BannedUser).where(BannedUser.telegram_user_id == telegram_user_id)
        ).scalar_one_or_none()
        is not None
    )


def ban_user(session: Session, telegram_user_id: int) -> bool:
    if is_user_banned(session, telegram_user_id):
        return True
    session.add(BannedUser(telegram_user_id=telegram_user_id))
    session.flush()
    return True


def unban_user(session: Session, telegram_user_id: int) -> bool:
    row = session.execute(
        select(BannedUser).where(BannedUser.telegram_user_id == telegram_user_id)
    ).scalar_one_or_none()
    if not row:
        return True
    session.delete(row)
    session.flush()
    return True


# ---------------------
# Reporting & Housekeeping
# ---------------------


def get_stats_summary(session: Session) -> Dict:
    total_users = session.execute(select(func.count(User.id))).scalar() or 0
    total_purchases = session.execute(select(func.count(Purchase.id))).scalar() or 0
    pending_purchases = (
        session.execute(
            select(func.count(Purchase.id)).where(Purchase.status == "pending")
        ).scalar()
        or 0
    )
    approved_purchases = (
        session.execute(
            select(func.count(Purchase.id)).where(Purchase.status == "approved")
        ).scalar()
        or 0
    )
    rejected_purchases = (
        session.execute(
            select(func.count(Purchase.id)).where(Purchase.status == "rejected")
        ).scalar()
        or 0
    )

    grades = [
        {
            "grade": r[0] or "",
            "count": int(r[1] or 0),
        }
        for r in session.execute(
            select(User.grade, func.count(User.id))
            .group_by(User.grade)
            .order_by(func.count(User.id).desc())
        )
    ]

    cities_top = [
        {
            "city": r[0] or "",
            "count": int(r[1] or 0),
        }
        for r in session.execute(
            select(User.city, func.count(User.id))
            .group_by(User.city)
            .order_by(func.count(User.id).desc())
        ).fetchmany(10)
    ]

    return {
        "users": total_users,
        "purchases": {
            "total": total_purchases,
            "pending": pending_purchases,
            "approved": approved_purchases,
            "rejected": rejected_purchases,
        },
        "grades": grades,
        "cities_top": cities_top,
    }


def list_stale_pending_purchases(
    session: Session, older_than_days: int = 14
) -> List[Dict]:
    cutoff = dt.datetime.utcnow() - dt.timedelta(days=max(1, older_than_days))
    q = session.execute(
        select(
            Purchase.id,
            Purchase.user_id,
            Purchase.product_type,
            Purchase.product_id,
            Purchase.created_at,
        )
        .where(Purchase.status == "pending", Purchase.created_at < cutoff)
        .order_by(Purchase.created_at.asc())
        .limit(200)
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


# ---------------------
# Learning services (Quiz)
# ---------------------


def upsert_user_stats(session: Session, user_db_id: int, correct: bool) -> None:
    today = dt.datetime.utcnow().date().isoformat()
    stats = (
        session.execute(select(UserStats).where(UserStats.user_id == user_db_id))
        .scalars()
        .first()
    )
    if stats is None:
        stats = UserStats(
            user_id=user_db_id,
            total_attempts=1,
            total_correct=1 if correct else 0,
            streak_days=1 if correct else 0,
            last_attempt_date=today,
            points=5 + (5 if correct else 0),
            last_daily_award_date=today,
        )
        session.add(stats)
        session.flush()
        return
    stats.total_attempts += 1
    if correct:
        stats.total_correct += 1
        stats.points += 5
    # daily award (once per day)
    if stats.last_daily_award_date != today:
        stats.points += 5
        stats.last_daily_award_date = today
    # streak
    if stats.last_attempt_date == today:
        pass
    else:
        try:
            prev = dt.date.fromisoformat(stats.last_attempt_date or today)
            if prev == dt.date.fromisoformat(today) - dt.timedelta(days=1):
                stats.streak_days += 1
            else:
                stats.streak_days = 1 if correct else 0
        except Exception:
            stats.streak_days = 1 if correct else 0
        stats.last_attempt_date = today
    session.flush()


def get_daily_question(session: Session, grade: str) -> QuizQuestion | None:
    # Pick the easiest unanswered question for daily practice
    q = (
        session.execute(
            select(QuizQuestion)
            .where(QuizQuestion.grade == grade)
            .order_by(QuizQuestion.difficulty.asc(), QuizQuestion.id.asc())
        )
        .scalars()
        .first()
    )
    return q


def submit_answer(
    session: Session, user_db_id: int, question_id: int, selected_index: int
) -> bool:
    question = (
        session.execute(select(QuizQuestion).where(QuizQuestion.id == question_id))
        .scalars()
        .first()
    )
    if not question:
        return False
    is_correct = int(selected_index == int(question.correct_index))
    attempt = QuizAttempt(
        user_id=user_db_id,
        question_id=question_id,
        selected_index=selected_index,
        correct=is_correct,
    )
    session.add(attempt)
    upsert_user_stats(session, user_db_id, bool(is_correct))
    session.flush()
    return bool(is_correct)


def get_user_stats(session: Session, user_db_id: int) -> Dict:
    stats = (
        session.execute(select(UserStats).where(UserStats.user_id == user_db_id))
        .scalars()
        .first()
    )
    if not stats:
        return {"total_attempts": 0, "total_correct": 0, "streak_days": 0, "points": 0}
    return {
        "total_attempts": int(stats.total_attempts or 0),
        "total_correct": int(stats.total_correct or 0),
        "streak_days": int(stats.streak_days or 0),
        "points": int(stats.points or 0),
    }


def get_leaderboard_top(session: Session, limit: int = 10) -> List[Dict]:
    q = session.execute(
        select(UserStats.user_id, UserStats.points)
        .order_by(UserStats.points.desc())
        .limit(max(1, min(50, limit)))
    )
    user_ids = [r.user_id for r in q]
    if not user_ids:
        return []
    # Map user_id -> telegram id
    m = {}
    rows = session.execute(select(User.id, User.telegram_user_id).where(User.id.in_(user_ids)))
    for r in rows:
        m[int(r.id)] = int(r.telegram_user_id)
    q2 = session.execute(
        select(UserStats.user_id, UserStats.points)
        .order_by(UserStats.points.desc())
        .limit(max(1, min(50, limit)))
    )
    out = []
    for r in q2:
        out.append({"telegram_user_id": int(m.get(int(r.user_id), 0)), "points": int(r.points or 0)})
    return out
