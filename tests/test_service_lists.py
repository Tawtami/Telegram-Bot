from database.db import session_scope
from database.service import (
    get_or_create_user,
    create_purchase,
    get_pending_purchases,
    get_course_participants_by_slug,
    get_free_course_participants_by_grade,
    ban_user,
    is_user_banned,
    unban_user,
)


def test_get_pending_purchases_filters_and_limits():
    import time

    unique_id = int(time.time() * 1000) % 100000 + 10  # Get unique timestamp-based ID

    with session_scope() as s:
        u = get_or_create_user(s, telegram_user_id=unique_id, first_name="P")
        p1 = create_purchase(s, u.id, product_type="book", product_id=f"B{unique_id}")
        p2 = create_purchase(
            s, u.id, product_type="book", product_id=f"B{unique_id+1}", status="approved"
        )

    with session_scope() as s:
        rows = get_pending_purchases(s, limit=10)
        ids = {r["purchase_id"] for r in rows}
        assert p1.id in ids
        assert p2.id not in ids


def test_course_participants_and_free_grade_lists():
    import time

    unique_id = int(time.time() * 1000) % 100000 + 20  # Get unique timestamp-based ID

    with session_scope() as s:
        u1 = get_or_create_user(s, telegram_user_id=unique_id, first_name="A", grade="9")
        u2 = get_or_create_user(s, telegram_user_id=unique_id + 1, first_name="B", grade="9")
        create_purchase(
            s, u1.id, product_type="course", product_id=f"math-{unique_id}", status="approved"
        )
        create_purchase(
            s, u2.id, product_type="course", product_id=f"math-{unique_id}", status="approved"
        )

    with session_scope() as s:
        participants = get_course_participants_by_slug(s, f"math-{unique_id}")
        assert u1.id in participants and u2.id in participants
        free_by_grade = get_free_course_participants_by_grade(s, "9")
        # Should at least include the two approved users of grade 9
        assert u1.id in free_by_grade and u2.id in free_by_grade


def test_ban_and_unban_flow():
    import time

    unique_id = int(time.time() * 1000) % 100000 + 30  # Get unique timestamp-based ID

    with session_scope() as s:
        u = get_or_create_user(s, telegram_user_id=unique_id, first_name="Z")
        assert not is_user_banned(s, u.telegram_user_id)
        assert ban_user(s, u.telegram_user_id)
        assert is_user_banned(s, u.telegram_user_id)
        assert unban_user(s, u.telegram_user_id)
        assert not is_user_banned(s, u.telegram_user_id)
