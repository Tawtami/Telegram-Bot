import types
import pytest

from utils.storage import StudentStorage


def test_storage_has_admin_methods(tmp_path):
    storage = StudentStorage(data_dir=str(tmp_path / "data"))
    assert hasattr(storage, "ban_user")
    assert hasattr(storage, "unban_user")
    assert hasattr(storage, "is_user_banned")

