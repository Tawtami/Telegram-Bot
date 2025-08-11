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
    assert storage.save_student(
        {
            "user_id": 1,
            "first_name": "A",
            "last_name": "B",
            "province": "تهران",
            "city": "تهران",
            "grade": "دهم",
            "field": "ریاضی",
        }
    )
    s = storage.get_student(1)
    assert s is not None
    # Encrypted at rest; but on read we should get plaintext
    assert s["first_name"] == "A"
    assert s["last_name"] == "B"
    # Inspect raw file to ensure fields are not plaintext
    with open(data_dir / "students.json", "r", encoding="utf-8") as f:
        raw = json.load(f)
    raw_student = next(x for x in raw["students"] if x["user_id"] == 1)
    assert raw_student["first_name"] != "A"
    assert raw_student["last_name"] != "B"
