from database.db import session_scope
from database.service import (
    get_or_create_user,
    create_purchase,
    approve_or_reject_purchase,
    get_stats_summary,
)


def test_approve_then_reject_is_noop():
    import time

    unique_id = int(time.time() * 1000) % 100000  # Get unique timestamp-based ID

    with session_scope() as s:
        u = get_or_create_user(s, telegram_user_id=unique_id, first_name="A")
        p = create_purchase(s, u.id, product_type="book", product_id=f"B{unique_id}")
        purchase_id = p.id  # Store the ID for later use

    with session_scope() as s:
        ok = approve_or_reject_purchase(s, purchase_id, admin_id=100, decision="approve")
        assert ok is not None

    with session_scope() as s:
        # second decision should be ignored (already approved)
        ok2 = approve_or_reject_purchase(s, purchase_id, admin_id=101, decision="reject")
        assert ok2 is None


def test_stats_summary_counts():
    import time

    unique_id = int(time.time() * 1000) % 100000 + 1  # Get unique timestamp-based ID + 1

    with session_scope() as s:
        u = get_or_create_user(s, telegram_user_id=unique_id, first_name="B")
        p = create_purchase(s, u.id, product_type="book", product_id=f"B{unique_id}")

    with session_scope() as s:
        approve_or_reject_purchase(s, p.id, admin_id=200, decision="approve")
        stats = get_stats_summary(s)
        assert stats["users"] >= 1
        assert stats["purchases"]["total"] >= 1
