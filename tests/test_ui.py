#!/usr/bin/env python3
"""
Tests for UI module functionality including keyboards and inline buttons.
"""

import pytest
from unittest.mock import Mock
from ui.keyboards import (
    build_main_menu_keyboard,
    build_grades_keyboard,
    build_majors_keyboard,
    build_provinces_keyboard,
    build_cities_keyboard,
    build_confirmation_keyboard,
    build_register_keyboard,
    build_back_keyboard,
)


def test_main_menu_keyboard():
    """Test main menu keyboard generation."""
    keyboard = build_main_menu_keyboard()

    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0

    # Check that main menu buttons exist
    button_texts = [btn.text for row in keyboard.inline_keyboard for btn in row]
    assert "🎓 دوره‌های رایگان" in button_texts
    assert "💼 دوره‌های تخصصی" in button_texts
    assert "🛒 سبد خرید من" in button_texts
    assert "👤 پروفایل من" in button_texts


def test_grades_keyboard():
    """Test grade selection keyboard."""
    grades = ["دهم", "یازدهم", "دوازدهم"]
    keyboard = build_grades_keyboard(grades)

    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0

    # Check that all grades are present
    button_texts = [btn.text for row in keyboard.inline_keyboard for btn in row]
    assert "🎓 دهم" in button_texts
    assert "🎓 یازدهم" in button_texts
    assert "🎓 دوازدهم" in button_texts


def test_majors_keyboard():
    """Test major selection keyboard."""
    majors = ["ریاضی", "تجربی", "انسانی", "هنر"]
    keyboard = build_majors_keyboard(majors)

    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0

    # Check that all majors are present
    button_texts = [btn.text for row in keyboard.inline_keyboard for btn in row]
    assert "📚 ریاضی" in button_texts
    assert "📚 تجربی" in button_texts
    assert "📚 انسانی" in button_texts
    assert "📚 هنر" in button_texts


def test_provinces_keyboard():
    """Test province selection keyboard."""
    provinces = ["تهران", "اصفهان", "خراسان رضوی"]
    keyboard = build_provinces_keyboard(provinces)

    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0

    # Check that some common provinces are present
    button_texts = [btn.text for row in keyboard.inline_keyboard for btn in row]
    assert "🏛️ تهران" in button_texts
    assert "🏛️ اصفهان" in button_texts
    assert "🏛️ خراسان رضوی" in button_texts


def test_cities_keyboard():
    """Test city selection keyboard for a specific province."""
    # Test with Tehran cities
    cities = ["تهران", "شهریار", "ورامین"]
    keyboard = build_cities_keyboard(cities)

    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0

    # Check that cities are present
    button_texts = [btn.text for row in keyboard.inline_keyboard for btn in row]
    assert "🏙️ تهران" in button_texts
    assert "🏙️ شهریار" in button_texts
    assert "🏙️ ورامین" in button_texts


def test_confirmation_keyboard():
    """Test confirmation keyboard."""
    keyboard = build_confirmation_keyboard()

    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0

    # Check that confirmation buttons are present
    button_texts = [btn.text for row in keyboard.inline_keyboard for btn in row]
    assert "✅ تایید" in button_texts
    assert "🔙 بازگشت" in button_texts


def test_register_keyboard():
    """Test registration keyboard."""
    keyboard = build_register_keyboard()

    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0

    # Check that registration button is present
    button_texts = [btn.text for row in keyboard.inline_keyboard for btn in row]
    assert "📝 ثبت‌نام" in button_texts


def test_back_keyboard():
    """Test back button keyboard."""
    keyboard = build_back_keyboard()

    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0

    # Check that back button is present
    button_texts = [btn.text for row in keyboard.inline_keyboard for btn in row]
    assert "🔙 بازگشت" in button_texts


def test_back_keyboard_custom_callback():
    """Test back button keyboard with custom callback data."""
    custom_callback = "custom_back_action"
    keyboard = build_back_keyboard(custom_callback)

    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0

    # Check that back button has custom callback
    button = keyboard.inline_keyboard[0][0]
    assert button.callback_data == custom_callback


def test_keyboard_structure():
    """Test that all keyboards have proper structure."""
    grades = ["دهم", "یازدهم"]
    majors = ["ریاضی", "تجربی"]
    provinces = ["تهران", "اصفهان"]
    cities = ["تهران", "شهریار"]

    keyboards = [
        build_main_menu_keyboard(),
        build_grades_keyboard(grades),
        build_majors_keyboard(majors),
        build_provinces_keyboard(provinces),
        build_cities_keyboard(cities),
        build_confirmation_keyboard(),
        build_register_keyboard(),
        build_back_keyboard(),
    ]

    for keyboard in keyboards:
        assert keyboard is not None
        assert hasattr(keyboard, 'inline_keyboard')
        assert isinstance(keyboard.inline_keyboard, list)

        # Check that each row is a list of buttons
        for row in keyboard.inline_keyboard:
            assert isinstance(row, list)
            assert len(row) > 0

            # Check that each button has required attributes
            for button in row:
                assert hasattr(button, 'text')
                assert hasattr(button, 'callback_data')
                assert button.text is not None
                assert button.callback_data is not None


def test_callback_data_format():
    """Test that callback data follows expected format."""
    keyboard = build_main_menu_keyboard()

    for row in keyboard.inline_keyboard:
        for button in row:
            # Callback data should be a string and not empty
            assert isinstance(button.callback_data, str)
            assert len(button.callback_data) > 0

            # Callback data should not contain spaces or special characters that could cause issues
            assert ' ' not in button.callback_data
            assert button.callback_data.isprintable()


def test_keyboard_accessibility():
    """Test that keyboards are accessible and don't crash."""
    # Test all keyboard functions with various inputs
    try:
        build_main_menu_keyboard()
        build_grades_keyboard(["دهم", "یازدهم"])
        build_majors_keyboard(["ریاضی", "تجربی"])
        build_provinces_keyboard(["تهران", "اصفهان"])
        build_cities_keyboard(["تهران", "شهریار"])
        build_confirmation_keyboard()
        build_register_keyboard()
        build_back_keyboard()
        build_back_keyboard("custom_callback")
    except Exception as e:
        pytest.fail(f"Keyboard generation failed with error: {e}")


def test_keyboard_localization():
    """Test that keyboards use Persian text appropriately."""
    keyboard = build_main_menu_keyboard()

    # Check that Persian text is used
    button_texts = [btn.text for row in keyboard.inline_keyboard for btn in row]

    # Should contain Persian characters
    persian_chars = any(any('\u0600' <= char <= '\u06ff' for char in text) for text in button_texts)
    assert persian_chars, "Keyboards should contain Persian text"


def test_empty_lists_handling():
    """Test that keyboards handle empty lists gracefully."""
    # Test with empty lists
    empty_grades = build_grades_keyboard([])
    empty_majors = build_majors_keyboard([])
    empty_provinces = build_provinces_keyboard([])
    empty_cities = build_cities_keyboard([])

    # Should still create valid keyboards (just with back buttons)
    assert empty_grades is not None
    assert empty_majors is not None
    assert empty_provinces is not None
    assert empty_cities is not None

    # Should have at least the back button
    assert len(empty_grades.inline_keyboard) > 0
    assert len(empty_majors.inline_keyboard) > 0
    assert len(empty_provinces.inline_keyboard) > 0
    assert len(empty_cities.inline_keyboard) > 0
