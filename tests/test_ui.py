#!/usr/bin/env python3
"""
Tests for UI module functionality including keyboards and inline buttons.
"""

import pytest
from unittest.mock import Mock
from ui.keyboards import (
    get_main_menu_keyboard,
    get_grade_keyboard,
    get_major_keyboard,
    get_province_keyboard,
    get_city_keyboard,
    get_edit_profile_keyboard,
    get_course_keyboard,
    get_payment_confirmation_keyboard,
    get_admin_keyboard
)


def test_main_menu_keyboard():
    """Test main menu keyboard generation."""
    keyboard = get_main_menu_keyboard()
    
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0
    
    # Check that main menu buttons exist
    button_texts = [btn.text for row in keyboard.inline_keyboard for btn in row]
    assert "📚 کلاس‌ها" in button_texts
    assert "📖 کتاب" in button_texts
    assert "📞 تماس" in button_texts
    assert "👤 پروفایل" in button_texts


def test_grade_keyboard():
    """Test grade selection keyboard."""
    keyboard = get_grade_keyboard()
    
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0
    
    # Check that all grades are present
    button_texts = [btn.text for row in keyboard.inline_keyboard for btn in row]
    assert "دهم" in button_texts
    assert "یازدهم" in button_texts
    assert "دوازدهم" in button_texts


def test_major_keyboard():
    """Test major selection keyboard."""
    keyboard = get_major_keyboard()
    
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0
    
    # Check that all majors are present
    button_texts = [btn.text for row in keyboard.inline_keyboard for btn in row]
    assert "ریاضی" in button_texts
    assert "تجربی" in button_texts
    assert "انسانی" in button_texts
    assert "هنر" in button_texts


def test_province_keyboard():
    """Test province selection keyboard."""
    keyboard = get_province_keyboard()
    
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0
    
    # Check that some common provinces are present
    button_texts = [btn.text for row in keyboard.inline_keyboard for btn in row]
    assert "تهران" in button_texts
    assert "اصفهان" in button_texts
    assert "خراسان رضوی" in button_texts


def test_city_keyboard():
    """Test city selection keyboard for a specific province."""
    # Test with Tehran province
    keyboard = get_city_keyboard("تهران")
    
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0
    
    # Check that Tehran cities are present
    button_texts = [btn.text for row in keyboard.inline_keyboard for btn in row]
    assert "تهران" in button_texts
    
    # Test with Isfahan province
    keyboard = get_city_keyboard("اصفهان")
    assert keyboard is not None
    
    # Test with non-existent province (should handle gracefully)
    keyboard = get_city_keyboard("غیرموجود")
    assert keyboard is not None


def test_edit_profile_keyboard():
    """Test edit profile keyboard."""
    keyboard = get_edit_profile_keyboard()
    
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0
    
    # Check that edit options are present
    button_texts = [btn.text for row in keyboard.inline_keyboard for btn in row]
    assert "نام" in button_texts
    assert "نام خانوادگی" in button_texts
    assert "شماره تلفن" in button_texts
    assert "پایه" in button_texts
    assert "رشته" in button_texts
    assert "استان" in button_texts
    assert "شهر" in button_texts


def test_course_keyboard():
    """Test course selection keyboard."""
    # Mock course data
    mock_course = Mock()
    mock_course.slug = "test-course"
    mock_course.title = "دوره تست"
    mock_course.type = "free"
    mock_course.price = 0
    
    keyboard = get_course_keyboard(mock_course)
    
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0
    
    # Check that course action buttons are present
    button_texts = [btn.text for row in keyboard.inline_keyboard for btn in row]
    assert "ثبت‌نام" in button_texts or "خرید" in button_texts


def test_payment_confirmation_keyboard():
    """Test payment confirmation keyboard."""
    keyboard = get_payment_confirmation_keyboard()
    
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0
    
    # Check that confirmation buttons are present
    button_texts = [btn.text for row in keyboard.inline_keyboard for btn in row]
    assert "تأیید" in button_texts or "تایید" in button_texts
    assert "انصراف" in button_texts or "لغو" in button_texts


def test_admin_keyboard():
    """Test admin keyboard."""
    keyboard = get_admin_keyboard()
    
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0
    
    # Check that admin action buttons are present
    button_texts = [btn.text for row in keyboard.inline_keyboard for btn in row]
    assert "📊 آمار" in button_texts or "آمار" in button_texts
    assert "📢 ارسال پیام" in button_texts or "ارسال پیام" in button_texts


def test_keyboard_structure():
    """Test that all keyboards have proper structure."""
    keyboards = [
        get_main_menu_keyboard(),
        get_grade_keyboard(),
        get_major_keyboard(),
        get_province_keyboard(),
        get_city_keyboard("تهران"),
        get_edit_profile_keyboard(),
        get_admin_keyboard()
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
    keyboard = get_main_menu_keyboard()
    
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
        get_main_menu_keyboard()
        get_grade_keyboard()
        get_major_keyboard()
        get_province_keyboard()
        get_city_keyboard("تهران")
        get_city_keyboard("اصفهان")
        get_city_keyboard("")  # Empty string
        get_city_keyboard(None)  # None value
        get_edit_profile_keyboard()
        get_admin_keyboard()
    except Exception as e:
        pytest.fail(f"Keyboard generation failed with error: {e}")


def test_keyboard_localization():
    """Test that keyboards use Persian text appropriately."""
    keyboard = get_main_menu_keyboard()
    
    # Check that Persian text is used
    button_texts = [btn.text for row in keyboard.inline_keyboard for btn in row]
    
    # Should contain Persian characters
    persian_chars = any(any('\u0600' <= char <= '\u06FF' for char in text) for text in button_texts)
    assert persian_chars, "Keyboards should contain Persian text"
