import types
import pytest

from database.db import session_scope
from database.service import (
    ban_user,
    unban_user,
    is_user_banned,
    get_or_create_user,
    create_purchase,
)
from database.models_sql import User, Purchase


def test_storage_has_admin_methods(tmp_path):
    with session_scope() as s:
        assert ban_user(s, 1) is True
        assert is_user_banned(s, 1) is True
        assert unban_user(s, 1) is True


def test_sql_create_purchase(tmp_path):
    with session_scope() as s:
        # Use timestamp to ensure unique values
        import time

        timestamp = int(time.time() * 1000)
        u = get_or_create_user(s, telegram_user_id=timestamp, first_name="A", last_name="B")
        p = create_purchase(s, user_id=u.id, product_type="book", product_id=f"X{timestamp}")
        assert isinstance(p, Purchase)
