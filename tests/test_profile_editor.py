import types
import pytest


class DummyMsg:
    async def edit_text(self, *args, **kwargs):
        return True


class DummyQuery:
    def __init__(self, data):
        self.data = data

    async def answer(self):
        return True

    async def edit_message_text(self, *args, **kwargs):
        return True


class DummyUpdate:
    def __init__(self, user_id, data):
        self.callback_query = DummyQuery(data)
        self.effective_user = types.SimpleNamespace(id=user_id)


class DummyContext:
    bot_data = {}


@pytest.mark.asyncio
async def test_profile_set_province_city(tmp_path):
    from handlers.profile import set_province, set_city
    from database.db import session_scope
    from database.service import get_or_create_user

    # Seed user
    with session_scope() as session:
        get_or_create_user(session, telegram_user_id=123)

    # Set province
    await set_province(DummyUpdate(123, "set_province:تهران"), DummyContext())
    # Then set city
    await set_city(DummyUpdate(123, "set_city:تهران"), DummyContext())

    # Verify state saved
    from database.models_sql import User

    with session_scope() as session:
        u = session.query(User).filter(User.telegram_user_id == 123).one()
        assert u.province == "تهران"
        assert u.city == "تهران"


@pytest.mark.asyncio
async def test_profile_set_grade_major(tmp_path):
    from handlers.profile import set_grade, set_major
    from database.db import session_scope
    from database.service import get_or_create_user

    with session_scope() as session:
        get_or_create_user(session, telegram_user_id=124)
    await set_grade(DummyUpdate(124, "set_grade:دهم"), DummyContext())
    await set_major(DummyUpdate(124, "set_major:ریاضی"), DummyContext())
    from database.models_sql import User

    with session_scope() as session:
        u = session.query(User).filter(User.telegram_user_id == 124).one()
        assert u.grade == "دهم"
        assert u.field_of_study == "ریاضی"
