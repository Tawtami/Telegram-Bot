import types
import pytest


@pytest.mark.asyncio
async def test_orders_ui_filters():
    from bot import orders_ui_command

    class DummyMsg:
        async def reply_text(self, text, reply_markup=None):
            assert isinstance(text, str)

    class DummyUpdate:
        effective_message = DummyMsg()
        effective_user = types.SimpleNamespace(id=111)

    class DummyContext:
        args = ["0", "book"]
        bot_data = {
            "config": types.SimpleNamespace(
                bot=types.SimpleNamespace(admin_user_ids=[111])
            ),
            "payment_notifications": {
                "t1": {
                    "processed": False,
                    "item_type": "book",
                    "item_title": "B",
                    "student_id": 5,
                    "created_at": 1,
                },
                "t2": {
                    "processed": False,
                    "item_type": "course",
                    "item_title": "C",
                    "student_id": 6,
                    "created_at": 2,
                },
            },
        }

    await orders_ui_command(DummyUpdate(), DummyContext())
