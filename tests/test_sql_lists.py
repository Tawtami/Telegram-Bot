import pytest


@pytest.mark.asyncio
async def test_get_approved_book_buyers(tmp_path):
    import time
    from database.db import session_scope
    from database.models_sql import User, Purchase
    from database.service import get_approved_book_buyers
    from utils.crypto import crypto_manager

    # Seed unique user id per test run
    unique_id = int(time.time() * 1000) % 100000 + 50  # Get unique timestamp-based ID

    with session_scope() as session:
        u = User(
            telegram_user_id=unique_id,  # avoid collisions across tests
            first_name_enc=crypto_manager.encrypt_text("A"),
            last_name_enc=crypto_manager.encrypt_text("B"),
            phone_enc=crypto_manager.encrypt_text("0912"),
        )
        session.add(u)
        session.flush()
        session.add(
            Purchase(
                user_id=u.id, product_type="book", product_id=f"Book{unique_id}", status="approved"
            )
        )
        session.flush()

    with session_scope() as session:
        buyers = get_approved_book_buyers(session, limit=10)
        assert any(b["product_id"] == f"Book{unique_id}" for b in buyers)
