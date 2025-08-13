import os
import json
from database.db import session_scope
from database.models_sql import User
from database.service import get_or_create_user


def test_create_user_sql(tmp_path):
    with session_scope() as session:
        u = get_or_create_user(session, telegram_user_id=123, first_name="A", last_name="B")
        assert isinstance(u, User)


def test_get_or_create_idempotent(tmp_path):
    with session_scope() as session:
        u1 = get_or_create_user(session, telegram_user_id=1, first_name="A")
    with session_scope() as session:
        u2 = get_or_create_user(session, telegram_user_id=1, first_name="B")
        assert u2.id == u1.id
