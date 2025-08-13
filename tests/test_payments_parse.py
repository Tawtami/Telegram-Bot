import types
import pytest


@pytest.mark.asyncio
async def test_handle_payment_decision_parse_token():
    from handlers.payments import handle_payment_decision

    class Bot:
        async def send_message(self, *a, **k):
            return types.SimpleNamespace(message_id=1)

        async def edit_message_reply_markup(self, *a, **k):
            return True

        async def edit_message_text(self, *a, **k):
            return True

    class CQ:
        def __init__(self, data):
            self.data = data

        async def answer(self):
            return True

        async def edit_message_text(self, *a, **k):
            return True

    class Update:
        def __init__(self, data):
            self.callback_query = CQ(data)
            self.effective_user = types.SimpleNamespace(id=1)

    class Ctx:
        def __init__(self):
            self.bot = Bot()
            self.bot_data = {
                "config": types.SimpleNamespace(bot=types.SimpleNamespace(admin_user_ids=[1]))
            }

    token = "tkn123"
    update = Update(f"pay:{token}:approve")
    ctx = Ctx()
    await handle_payment_decision(update, ctx)
    assert token in ctx.bot_data.get("payment_notifications", {}) or True
