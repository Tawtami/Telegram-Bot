import pytest


def _seed_purchase(session, crypto_manager):
    from database.models_sql import User, Purchase

    u = User(
        telegram_user_id=999,
        first_name_enc=crypto_manager.encrypt_text("X"),
        last_name_enc=crypto_manager.encrypt_text("Y"),
        phone_enc=crypto_manager.encrypt_text("0912"),
    )
    session.add(u)
    session.flush()
    p = Purchase(user_id=u.id, product_type="course", product_id="slug-1", status="pending")
    session.add(p)
    session.flush()
    return u, p


def test_atomic_approve(tmp_path):
    from database.db import session_scope
    from database.service import approve_or_reject_purchase
    from utils.crypto import crypto_manager

    with session_scope() as session:
        u, p = _seed_purchase(session, crypto_manager)

    # Two competing approvals
    with session_scope() as s1:
        r1 = approve_or_reject_purchase(s1, p.id, admin_id=1, decision="approve")
    with session_scope() as s2:
        r2 = approve_or_reject_purchase(s2, p.id, admin_id=2, decision="approve")

    # Exactly one should succeed
    ok_count = int(r1 is not None) + int(r2 is not None)
    assert ok_count == 1
