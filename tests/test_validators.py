import pytest

from utils.validators import Validator


def test_validate_name_ok():
    ok, val = Validator.validate_name("علی")
    assert ok
    assert val.startswith("ع")


def test_validate_phone_ok():
    ok, val = Validator.validate_phone("09121234567")
    assert ok
    assert val.startswith("+98")


def test_validate_phone_bad():
    ok, _ = Validator.validate_phone("123")
    assert not ok

