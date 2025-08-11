import types
import json
import pytest


class DummyBot:
    def __init__(self):
        self.sent_messages = []
        self.edits = []

    async def send_message(self, chat_id, text, **kwargs):
        self.sent_messages.append({"chat_id": chat_id, "text": text})
        return types.SimpleNamespace(message_id=1)

    async def edit_message_reply_markup(self, chat_id, message_id, reply_markup=None):
        self.edits.append(
            {
                "type": "reply_markup",
                "chat_id": chat_id,
                "message_id": message_id,
            }
        )

    async def edit_message_text(self, chat_id, message_id, text):
        self.edits.append(
            {
                "type": "text",
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
            }
        )


class DummyQuery:
    def __init__(self, data):
        self.data = data

    async def answer(self):
        return True

    async def edit_message_text(self, text):
        # no-op for these tests
        return True


class DummyUpdate:
    def __init__(self, user_id: int, data: str):
        self.callback_query = DummyQuery(data)
        self.effective_user = types.SimpleNamespace(id=user_id)


class DummyContext:
    def __init__(self, bot_data, bot):
        self.bot_data = bot_data
        self.bot = bot
        self.application = types.SimpleNamespace()


@pytest.mark.asyncio
async def test_handle_payment_decision_approve_course(tmp_path):
    from handlers.payments import handle_payment_decision
    from utils.storage import StudentStorage

    # Arrange storage with pending course
    storage = StudentStorage(data_dir=str(tmp_path / "data"))
    user_id = 555
    storage.save_student(
        {
            "user_id": user_id,
            "first_name": "Ali",
            "last_name": "R",
            "province": "تهران",
            "city": "تهران",
            "grade": "دهم",
            "field": "ریاضی",
            "pending_payments": ["course-1"],
        }
    )

    token = "abcdabcdabcdabcd"
    bot = DummyBot()
    bot_data = {
        "config": types.SimpleNamespace(
            bot=types.SimpleNamespace(admin_user_ids=[111])
        ),
        "storage": storage,
        "payment_notifications": {
            token: {
                "student_id": user_id,
                "item_type": "course",
                "item_id": "course-1",
                "item_title": "Course 1",
                "messages": [(111, 10)],
                "processed": False,
                "created_at": 1,
            }
        },
    }

    update = DummyUpdate(user_id=111, data=f"pay:{token}:approve")
    context = DummyContext(bot_data=bot_data, bot=bot)

    # Act
    await handle_payment_decision(update, context)

    # Assert
    meta = bot_data["payment_notifications"][token]
    assert meta["processed"] is True
    assert meta["decision"] == "approve"
    student = storage.get_student(user_id)
    assert "course-1" in student.get("purchased_courses", [])
    assert "pending_payments" not in student or "course-1" not in student.get(
        "pending_payments", []
    )
    # Confirmation message sent to student
    assert any(m["chat_id"] == user_id for m in bot.sent_messages)


@pytest.mark.asyncio
async def test_handle_payment_decision_approve_book(tmp_path):
    from handlers.payments import handle_payment_decision
    from utils.storage import StudentStorage

    storage = StudentStorage(data_dir=str(tmp_path / "data"))
    user_id = 777
    storage.save_student(
        {
            "user_id": user_id,
            "first_name": "Sara",
            "last_name": "M",
            "province": "تهران",
            "city": "تهران",
            "grade": "دهم",
            "field": "ریاضی",
            "book_purchases": [{"title": "BookA"}],
        }
    )

    token = "eeeeffffaaaabbbb"
    bot = DummyBot()
    bot_data = {
        "config": types.SimpleNamespace(
            bot=types.SimpleNamespace(admin_user_ids=[111])
        ),
        "storage": storage,
        "payment_notifications": {
            token: {
                "student_id": user_id,
                "item_type": "book",
                "item_id": "BookA",
                "item_title": "BookA",
                "messages": [(111, 11)],
                "processed": False,
                "created_at": 1,
            }
        },
    }

    update = DummyUpdate(user_id=111, data=f"pay:{token}:approve")
    context = DummyContext(bot_data=bot_data, bot=bot)

    await handle_payment_decision(update, context)

    meta = bot_data["payment_notifications"][token]
    assert meta["processed"] is True
    assert meta["decision"] == "approve"
    student = storage.get_student(user_id)
    assert any(
        p.get("title") == "BookA" and p.get("approved")
        for p in student.get("book_purchases", [])
    )


@pytest.mark.asyncio
async def test_handle_payment_decision_reject_book(tmp_path):
    from handlers.payments import handle_payment_decision
    from utils.storage import StudentStorage

    storage = StudentStorage(data_dir=str(tmp_path / "data"))
    user_id = 888
    storage.save_student(
        {
            "user_id": user_id,
            "first_name": "Nima",
            "last_name": "T",
            "province": "تهران",
            "city": "تهران",
            "grade": "دهم",
            "field": "ریاضی",
            "book_purchases": [{"title": "BookB"}],
        }
    )

    token = "1122334455667788"
    bot = DummyBot()
    bot_data = {
        "config": types.SimpleNamespace(
            bot=types.SimpleNamespace(admin_user_ids=[111])
        ),
        "storage": storage,
        "payment_notifications": {
            token: {
                "student_id": user_id,
                "item_type": "book",
                "item_id": "BookB",
                "item_title": "BookB",
                "messages": [(111, 12)],
                "processed": False,
                "created_at": 1,
            }
        },
    }

    update = DummyUpdate(user_id=111, data=f"pay:{token}:reject")
    context = DummyContext(bot_data=bot_data, bot=bot)

    await handle_payment_decision(update, context)

    meta = bot_data["payment_notifications"][token]
    assert meta["processed"] is True
    assert meta["decision"] == "reject"
    student = storage.get_student(user_id)
    # Ensure not marked approved
    assert not any(
        p.get("title") == "BookB" and p.get("approved")
        for p in student.get("book_purchases", [])
    )
    # Rejection message sent
    assert any(
        (m["chat_id"] == user_id and "ناموفق" in m["text"]) for m in bot.sent_messages
    )
