from database.db import session_scope
from database.service import (
    get_or_create_user,
    create_purchase,
    approve_or_reject_purchase,
    get_stats_summary,
)


def test_approve_then_reject_is_noop():
    with session_scope() as s:
        u = get_or_create_user(s, telegram_user_id=991, first_name="A")
        p = create_purchase(s, u.id, product_type="book", product_id="B1")

    with session_scope() as s:
        ok = approve_or_reject_purchase(s, p.id, admin_id=100, decision="approve")
        assert ok is not None

    with session_scope() as s:
        # second decision should be ignored (already approved)
        ok2 = approve_or_reject_purchase(s, p.id, admin_id=101, decision="reject")
        assert ok2 is None


def test_stats_summary_counts():
    with session_scope() as s:
        u = get_or_create_user(s, telegram_user_id=992, first_name="B")
        p = create_purchase(s, u.id, product_type="book", product_id="B2")

    with session_scope() as s:
        approve_or_reject_purchase(s, p.id, admin_id=200, decision="approve")
        stats = get_stats_summary(s)
        assert stats["users"] >= 1
        assert stats["purchases"]["total"] >= 1

