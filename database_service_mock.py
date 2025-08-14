#!/usr/bin/env python3
"""
Mock database.service module for running tests without real database

This provides all the service functions that tests need
to run without the actual database service.
"""

import sys
from unittest.mock import MagicMock
from datetime import datetime, timezone


# Mock user management functions
def get_or_create_user(session, telegram_user_id, **kwargs):
    """Mock get_or_create_user function"""
    from database_mock import User
    return User(telegram_user_id=telegram_user_id, **kwargs)


def is_user_banned(session, telegram_user_id):
    """Mock is_user_banned function"""
    return False


def ban_user(session, telegram_user_id):
    """Mock ban_user function"""
    return True


def unban_user(session, telegram_user_id, admin_id):
    """Mock unban_user function"""
    return True


def audit_profile_change(session, user_id, field_name, old_value, new_value, changed_by):
    """Mock audit_profile_change function"""
    return True


# Mock purchase functions
def create_purchase(session, user_id, product_type, product_id, **kwargs):
    """Mock create_purchase function"""
    from database_mock import Purchase
    return Purchase(
        user_id=user_id,
        product_type=product_type,
        product_id=product_id,
        amount=kwargs.get('amount', 1000),
        **kwargs
    )


def approve_or_reject_purchase(session, purchase_id, action, admin_id, **kwargs):
    """Mock approve_or_reject_purchase function"""
    if action == "approve":
        return True
    elif action == "reject":
        return None
    return False


def approve_or_reject_purchase_legacy(session, purchase_id, admin_id, decision, **kwargs):
    """Mock approve_or_reject_purchase with legacy signature"""
    if decision == "approve":
        return True
    elif decision == "reject":
        return None
    return False


def add_receipt(session, user_id, purchase_id, amount, **kwargs):
    """Mock add_receipt function"""
    from database_mock import Receipt
    return Receipt(user_id=user_id, purchase_id=purchase_id, amount=amount)


# Mock course functions
def get_course_participants_by_slug(session, course_slug):
    """Mock get_course_participants_by_slug function"""
    from database_mock import User
    return [User(id=1), User(id=2)]


def get_free_course_participants_by_grade(session, grade):
    """Mock get_free_course_participants_by_grade function"""
    from database_mock import User
    return [User(id=1, grade=grade), User(id=2, grade=grade)]


# Mock quiz functions
def get_daily_question(session):
    """Mock get_daily_question function"""
    from database_mock import QuizQuestion
    return QuizQuestion(question="Test question", answer="Test answer")


def submit_answer(session, user_id, question_id, answer):
    """Mock submit_answer function"""
    from database_mock import QuizAttempt
    return QuizAttempt(
        user_id=user_id,
        question_id=question_id,
        answer=answer,
        is_correct=answer == "Test answer"
    )


# Mock stats functions
def get_user_stats(session, user_id):
    """Mock get_user_stats function"""
    return {"courses": 2, "books": 1, "quiz_score": 85}


def get_leaderboard_top(session, limit=10):
    """Mock get_leaderboard_top function"""
    return [
        {"user_id": 1, "score": 100, "name": "User 1"},
        {"user_id": 2, "score": 90, "name": "User 2"},
    ]


def get_stats_summary(session):
    """Mock get_stats_summary function"""
    return {
        "users": 10,
        "purchases": 25,
        "courses": 5,
        "books": 3
    }


# Mock list functions
def get_approved_book_buyers(session, **kwargs):
    """Mock get_approved_book_buyers function"""
    return [
        {"user_id": 1, "product_id": "Book123", "amount": 1000},
        {"user_id": 2, "product_id": "Book456", "amount": 1500},
    ]


def get_pending_purchases(session, **kwargs):
    """Mock get_pending_purchases function"""
    from database_mock import Purchase
    return [
        {"user_id": 1, "purchase_id": 1, "product_type": "book", "product_id": "Book123"},
        {"user_id": 2, "purchase_id": 2, "product_type": "course", "product_id": "Course456"},
    ]


def get_course_participants(session, course_slug):
    """Mock get_course_participants function"""
    from database_mock import User
    return [User(id=1), User(id=2)]


# Mock admin functions
def get_admin_stats(session):
    """Mock get_admin_stats function"""
    return {
        "users": 10,
        "purchases": 25,
        "courses": 5,
        "books": 3
    }


# Add to sys.modules so imports work
sys.modules['database.service'] = sys.modules[__name__]
