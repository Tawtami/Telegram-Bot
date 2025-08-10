import os
import json
from utils.storage import StudentStorage


def test_ban_unban(tmp_path):
    data_dir = tmp_path / "data"
    storage = StudentStorage(data_dir=str(data_dir))
    uid = 123
    assert not storage.is_user_banned(uid)
    assert storage.ban_user(uid)
    assert storage.is_user_banned(uid)
    assert storage.unban_user(uid)
    assert not storage.is_user_banned(uid)


def test_save_student(tmp_path):
    data_dir = tmp_path / "data"
    storage = StudentStorage(data_dir=str(data_dir))
    assert storage.save_student({
        "user_id": 1,
        "first_name": "A",
        "last_name": "B",
        "province": "تهران",
        "city": "تهران",
        "grade": "دهم",
        "field": "ریاضی",
    })
    s = storage.get_student(1)
    assert s is not None

