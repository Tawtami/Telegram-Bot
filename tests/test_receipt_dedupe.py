from database.db import session_scope
from database.service import create_purchase, add_receipt, get_or_create_user
from utils.crypto import crypto_manager


def test_receipt_dedupe(tmp_path):
    with session_scope() as session:
        u = get_or_create_user(session, 222, first_name="A", last_name="B", phone="0912")
        p = create_purchase(session, u.id, product_type="book", product_id="BookY")
        ok1, _ = add_receipt(session, p.id, telegram_file_id="f1", file_unique_id="uniq-1")
        ok2, _ = add_receipt(session, p.id, telegram_file_id="f2", file_unique_id="uniq-1")
        assert ok1 is True
        assert ok2 is False


