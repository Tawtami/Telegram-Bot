import types
import pytest

from utils.storage import StudentStorage


def test_storage_has_admin_methods(tmp_path):
    storage = StudentStorage(data_dir=str(tmp_path / "data"))
    assert hasattr(storage, "ban_user")
    assert hasattr(storage, "unban_user")
    assert hasattr(storage, "is_user_banned")


def test_confirm_payment_moves_pending_to_purchased(tmp_path):
    storage = StudentStorage(data_dir=str(tmp_path / "data"))
    user_id = 456
    # Seed student with pending payment
    storage.save_student(
        {
            "user_id": user_id,
            "first_name": "A",
            "last_name": "B",
            "province": "تهران",
            "city": "تهران",
            "grade": "دهم",
            "field": "ریاضی",
            "pending_payments": ["course-1"],
        }
    )
    assert storage.confirm_payment(user_id)
    student = storage.get_student(user_id)
    assert "pending_payments" not in student
    assert "course-1" in student.get("purchased_courses", [])
