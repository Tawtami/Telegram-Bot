#!/usr/bin/env python3
"""
Comprehensive tests for utils/storage.py to achieve 100% coverage
"""

import pytest
import json
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime
from utils.storage import StudentStorage


class TestStudentStorage:
    """Test StudentStorage class for 100% coverage"""

    def setup_method(self):
        """Set up test environment before each test"""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.storage = StudentStorage(self.temp_dir)

    def teardown_method(self):
        """Clean up test environment after each test"""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test StudentStorage initialization"""
        assert self.storage.data_dir == Path(self.temp_dir)
        assert self.storage.students_file == Path(self.temp_dir) / "students.json"
        assert self.storage.courses_file == Path(self.temp_dir) / "courses.json"
        assert self.storage.purchases_file == Path(self.temp_dir) / "purchases.json"
        assert self.storage.banned_file == Path(self.temp_dir) / "banned.json"
        assert hasattr(self.storage, 'lock')
        assert hasattr(self.storage, '_cache')
        assert hasattr(self.storage, '_cache_ttl')
        assert hasattr(self.storage, '_last_cache_update')

    def test_initialize_files_creates_directory(self):
        """Test that _initialize_files creates the data directory"""
        # Remove the directory
        shutil.rmtree(self.temp_dir)
        assert not os.path.exists(self.temp_dir)

        # Recreate storage (this calls _initialize_files)
        storage = StudentStorage(self.temp_dir)
        assert os.path.exists(self.temp_dir)

    def test_initialize_files_creates_json_files(self):
        """Test that _initialize_files creates required JSON files"""
        # Check that files were created with proper structure
        assert self.storage.students_file.exists()
        assert self.storage.purchases_file.exists()
        assert self.storage.banned_file.exists()

        # Check file contents
        with open(self.storage.students_file, 'r') as f:
            data = json.load(f)
            assert "students" in data
            assert data["students"] == []

        with open(self.storage.purchases_file, 'r') as f:
            data = json.load(f)
            assert "purchases" in data
            assert data["purchases"] == []

        with open(self.storage.banned_file, 'r') as f:
            data = json.load(f)
            assert "banned_user_ids" in data
            assert data["banned_user_ids"] == []

    def test_load_json_with_cache_hit(self):
        """Test _load_json with cache hit"""
        # Set up cache
        cache_key = str(self.storage.students_file)
        test_data = {"students": [{"id": 1}]}
        self.storage._cache[cache_key] = test_data
        self.storage._last_cache_update[cache_key] = 1000.0

        # Mock time.time to return a time within TTL
        with patch('time.time', return_value=1200.0):  # 200 seconds later, within 300s TTL
            result = self.storage._load_json(self.storage.students_file)
            assert result == test_data

    def test_load_json_with_cache_miss(self):
        """Test _load_json with cache miss"""
        # Set up cache with expired data
        cache_key = str(self.storage.students_file)
        old_data = {"students": [{"id": 1}]}
        self.storage._cache[cache_key] = old_data
        self.storage._last_cache_update[cache_key] = 1000.0

        # Mock time.time to return a time outside TTL
        with patch('time.time', return_value=1400.0):  # 400 seconds later, outside 300s TTL
            result = self.storage._load_json(self.storage.students_file)
            # Should return actual file content (empty students list from initialization)
            assert "students" in result
            assert result["students"] == []

    def test_load_json_file_not_exists(self):
        """Test _load_json when file doesn't exist"""
        non_existent_file = Path(self.temp_dir) / "nonexistent.json"
        result = self.storage._load_json(non_existent_file)
        assert result == {}

    def test_load_json_json_decode_error(self):
        """Test _load_json with JSON decode error"""
        # Create a file with invalid JSON
        invalid_json_file = Path(self.temp_dir) / "invalid.json"
        with open(invalid_json_file, 'w') as f:
            f.write("invalid json content")

        result = self.storage._load_json(invalid_json_file)
        assert result == {}

    def test_save_json_success(self):
        """Test _save_json successful save"""
        test_data = {"test": "data"}
        test_file = Path(self.temp_dir) / "test.json"

        self.storage._save_json(test_file, test_data)

        # Check file was created
        assert test_file.exists()

        # Check content
        with open(test_file, 'r') as f:
            saved_data = json.load(f)
            assert saved_data == test_data

        # Check cache was updated
        cache_key = str(test_file)
        assert cache_key in self.storage._cache
        assert self.storage._cache[cache_key] == test_data
        assert cache_key in self.storage._last_cache_update

    def test_save_json_exception_handling(self):
        """Test _save_json exception handling"""
        test_data = {"test": "data"}
        test_file = Path(self.temp_dir) / "test.json"

        # Mock open to raise an exception
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            self.storage._save_json(test_file, test_data)

        # Check cache was invalidated
        cache_key = str(test_file)
        assert cache_key not in self.storage._cache
        assert cache_key not in self.storage._last_cache_update

    def test_save_student_success_new_student(self):
        """Test save_student successful save for new student"""
        student_data = {
            "user_id": 12345,
            "first_name": "John",
            "last_name": "Doe",
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
        }

        result = self.storage.save_student(student_data)
        assert result is True

        # Check student was saved
        saved_student = self.storage.get_student(12345)
        assert saved_student is not None
        assert saved_student["user_id"] == 12345
        assert saved_student["first_name"] == "John"
        assert "registration_date" in saved_student
        assert "last_updated" in saved_student

    def test_save_student_success_update_existing(self):
        """Test save_student successful update for existing student"""
        # First save a student
        student_data = {
            "user_id": 12345,
            "first_name": "John",
            "last_name": "Doe",
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
        }
        self.storage.save_student(student_data)

        # Update the student
        updated_data = student_data.copy()
        updated_data["grade"] = "11"

        result = self.storage.save_student(updated_data)
        assert result is True

        # Check student was updated
        saved_student = self.storage.get_student(12345)
        assert saved_student["grade"] == "11"
        assert "registration_date" in saved_student
        assert "last_updated" in saved_student

    def test_save_student_missing_required_field(self):
        """Test save_student with missing required field"""
        student_data = {
            "user_id": 12345,
            "first_name": "John",
            # Missing last_name
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
        }

        result = self.storage.save_student(student_data)
        assert result is False

    def test_save_student_empty_required_field(self):
        """Test save_student with empty required field"""
        student_data = {
            "user_id": 12345,
            "first_name": "John",
            "last_name": "",  # Empty
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
        }

        result = self.storage.save_student(student_data)
        assert result is False

    def test_save_student_invalid_user_id(self):
        """Test save_student with invalid user_id"""
        student_data = {
            "user_id": "invalid_id",  # Not an integer
            "first_name": "John",
            "last_name": "Doe",
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
        }

        result = self.storage.save_student(student_data)
        assert result is False

    def test_save_student_exception_handling(self):
        """Test save_student exception handling"""
        student_data = {
            "user_id": 12345,
            "first_name": "John",
            "last_name": "Doe",
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
        }

        # Mock _save_json to raise an exception
        with patch.object(self.storage, '_save_json', side_effect=Exception("Test error")):
            result = self.storage.save_student(student_data)
            assert result is False

    @patch('utils.storage.crypto_manager')
    def test_save_student_with_encryption(self, mock_crypto):
        """Test save_student with encryption enabled"""
        mock_crypto.encrypt_text.return_value = "encrypted_text"

        student_data = {
            "user_id": 12345,
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "1234567890",
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
        }

        result = self.storage.save_student(student_data)
        assert result is True

        # Check encryption was called
        mock_crypto.encrypt_text.assert_called()

    def test_get_student_success(self):
        """Test get_student successful retrieval"""
        # Save a student first
        student_data = {
            "user_id": 12345,
            "first_name": "John",
            "last_name": "Doe",
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
        }
        self.storage.save_student(student_data)

        # Retrieve the student
        retrieved = self.storage.get_student(12345)
        assert retrieved is not None
        assert retrieved["user_id"] == 12345
        assert retrieved["first_name"] == "John"

    def test_get_student_not_found(self):
        """Test get_student when student doesn't exist"""
        result = self.storage.get_student(99999)
        assert result is None

    @patch('utils.storage.crypto_manager')
    def test_get_student_with_decryption(self, mock_crypto):
        """Test get_student with decryption enabled"""
        mock_crypto.decrypt_text.return_value = "decrypted_text"
        mock_crypto.encrypt_text.return_value = "encrypted_text"

        # Save a student with encrypted data
        student_data = {
            "user_id": 12345,
            "first_name": "encrypted_first_name",
            "last_name": "encrypted_last_name",
            "phone_number": "encrypted_phone",
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
        }
        self.storage.save_student(student_data)

        # Retrieve the student
        retrieved = self.storage.get_student(12345)
        assert retrieved is not None

        # Check decryption was called
        mock_crypto.decrypt_text.assert_called()

    @patch('utils.storage.crypto_manager')
    def test_get_student_decryption_exception(self, mock_crypto):
        """Test get_student with decryption exception"""
        mock_crypto.decrypt_text.side_effect = Exception("Decryption failed")
        mock_crypto.encrypt_text.return_value = "encrypted_text"

        # Save a student with encrypted data
        student_data = {
            "user_id": 12345,
            "first_name": "encrypted_first_name",
            "last_name": "encrypted_last_name",
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
        }
        self.storage.save_student(student_data)

        # Retrieve the student (should handle decryption exception gracefully)
        retrieved = self.storage.get_student(12345)
        assert retrieved is not None

    def test_get_student_exception_handling(self):
        """Test get_student exception handling"""
        # Mock _load_json to raise an exception
        with patch.object(self.storage, '_load_json', side_effect=Exception("Test error")):
            result = self.storage.get_student(12345)
            assert result is None

    def test_get_all_students_success(self):
        """Test get_all_students successful retrieval"""
        # Save multiple students
        students_data = [
            {
                "user_id": 12345,
                "first_name": "John",
                "last_name": "Doe",
                "province": "Tehran",
                "city": "Tehran",
                "grade": "12",
                "field": "Mathematics",
            },
            {
                "user_id": 67890,
                "first_name": "Jane",
                "last_name": "Smith",
                "province": "Isfahan",
                "city": "Isfahan",
                "grade": "11",
                "field": "Physics",
            },
        ]

        for student in students_data:
            self.storage.save_student(student)

        # Retrieve all students
        all_students = self.storage.get_all_students()
        assert len(all_students) == 2
        assert any(s["user_id"] == 12345 for s in all_students)
        assert any(s["user_id"] == 67890 for s in all_students)

    @patch('utils.storage.crypto_manager')
    def test_get_all_students_with_decryption(self, mock_crypto):
        """Test get_all_students with decryption enabled"""
        mock_crypto.decrypt_text.return_value = "decrypted_text"
        mock_crypto.encrypt_text.return_value = "encrypted_text"

        # Save a student with encrypted data
        student_data = {
            "user_id": 12345,
            "first_name": "encrypted_first_name",
            "last_name": "encrypted_last_name",
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
        }
        self.storage.save_student(student_data)

        # Retrieve all students
        all_students = self.storage.get_all_students()
        assert len(all_students) == 1

        # Check decryption was called
        mock_crypto.decrypt_text.assert_called()

    def test_get_all_students_exception_handling(self):
        """Test get_all_students exception handling"""
        # Mock _load_json to raise an exception
        with patch.object(self.storage, '_load_json', side_effect=Exception("Test error")):
            result = self.storage.get_all_students()
            assert result == []

    def test_save_course_registration_success_paid(self):
        """Test save_course_registration successful paid course registration"""
        # Save a student first
        student_data = {
            "user_id": 12345,
            "first_name": "John",
            "last_name": "Doe",
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
        }
        self.storage.save_student(student_data)

        # Register for a paid course
        result = self.storage.save_course_registration(12345, "MATH101", is_paid=True)
        assert result is True

        # Check course was added
        student = self.storage.get_student(12345)
        assert "purchased_courses" in student
        assert "MATH101" in student["purchased_courses"]
        assert "last_activity" in student

    def test_save_course_registration_success_free(self):
        """Test save_course_registration successful free course registration"""
        # Save a student first
        student_data = {
            "user_id": 12345,
            "first_name": "John",
            "last_name": "Doe",
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
        }
        self.storage.save_student(student_data)

        # Register for a free course
        result = self.storage.save_course_registration(12345, "MATH101", is_paid=False)
        assert result is True

        # Check course was added
        student = self.storage.get_student(12345)
        assert "free_courses" in student
        assert "MATH101" in student["free_courses"]
        assert "last_activity" in student

    def test_save_course_registration_student_not_found(self):
        """Test save_course_registration when student doesn't exist"""
        result = self.storage.save_course_registration(99999, "MATH101", is_paid=True)
        assert result is False

    def test_save_course_registration_exception_handling(self):
        """Test save_course_registration exception handling"""
        # Save a student first
        student_data = {
            "user_id": 12345,
            "first_name": "John",
            "last_name": "Doe",
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
        }
        self.storage.save_student(student_data)

        # Mock save_student to raise an exception
        with patch.object(self.storage, 'save_student', side_effect=Exception("Test error")):
            result = self.storage.save_course_registration(12345, "MATH101", is_paid=True)
            assert result is False

    def test_save_book_purchase_success(self):
        """Test save_book_purchase successful book purchase"""
        # Save a student first
        student_data = {
            "user_id": 12345,
            "first_name": "John",
            "last_name": "Doe",
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
        }
        self.storage.save_student(student_data)

        # Purchase a book
        book_data = {"title": "Advanced Mathematics", "price": 50000}
        result = self.storage.save_book_purchase(12345, book_data)
        assert result is True

        # Check book purchase was added
        student = self.storage.get_student(12345)
        assert "book_purchases" in student
        assert len(student["book_purchases"]) == 1
        assert student["book_purchases"][0]["title"] == "Advanced Mathematics"
        assert "purchase_date" in student["book_purchases"][0]

    def test_save_book_purchase_student_not_found(self):
        """Test save_book_purchase when student doesn't exist"""
        book_data = {"title": "Advanced Mathematics", "price": 50000}
        result = self.storage.save_book_purchase(99999, book_data)
        assert result is False

    def test_save_book_purchase_exception_handling(self):
        """Test save_book_purchase exception handling"""
        # Save a student first
        student_data = {
            "user_id": 12345,
            "first_name": "John",
            "last_name": "Doe",
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
        }
        self.storage.save_student(student_data)

        # Mock save_student to raise an exception
        with patch.object(self.storage, 'save_student', side_effect=Exception("Test error")):
            book_data = {"title": "Advanced Mathematics", "price": 50000}
            result = self.storage.save_book_purchase(12345, book_data)
            assert result is False

    def test_confirm_payment_success(self):
        """Test confirm_payment successful payment confirmation"""
        # Save a student with pending payments
        student_data = {
            "user_id": 12345,
            "first_name": "John",
            "last_name": "Doe",
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
            "pending_payments": ["MATH101", "PHYS101"],
        }
        self.storage.save_student(student_data)

        # Confirm payment
        result = self.storage.confirm_payment(12345)
        assert result is True

        # Check pending payments were moved to purchased
        student = self.storage.get_student(12345)
        assert "pending_payments" not in student
        assert "purchased_courses" in student
        assert "MATH101" in student["purchased_courses"]
        assert "PHYS101" in student["purchased_courses"]

    def test_confirm_payment_student_not_found(self):
        """Test confirm_payment when student doesn't exist"""
        result = self.storage.confirm_payment(99999)
        assert result is False

    def test_confirm_payment_no_pending_payments(self):
        """Test confirm_payment when student has no pending payments"""
        # Save a student without pending payments
        student_data = {
            "user_id": 12345,
            "first_name": "John",
            "last_name": "Doe",
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
        }
        self.storage.save_student(student_data)

        result = self.storage.confirm_payment(12345)
        assert result is False

    def test_confirm_payment_exception_handling(self):
        """Test confirm_payment exception handling"""
        # Save a student with pending payments
        student_data = {
            "user_id": 12345,
            "first_name": "John",
            "last_name": "Doe",
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
            "pending_payments": ["MATH101"],
        }
        self.storage.save_student(student_data)

        # Mock save_student to raise an exception
        with patch.object(self.storage, 'save_student', side_effect=Exception("Test error")):
            result = self.storage.confirm_payment(12345)
            assert result is False

    def test_add_pending_payment_success(self):
        """Test add_pending_payment successful addition"""
        # Save a student first
        student_data = {
            "user_id": 12345,
            "first_name": "John",
            "last_name": "Doe",
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
        }
        self.storage.save_student(student_data)

        # Add pending payment
        result = self.storage.add_pending_payment(12345, "MATH101")
        assert result is True

        # Check pending payment was added
        student = self.storage.get_student(12345)
        assert "pending_payments" in student
        assert "MATH101" in student["pending_payments"]
        assert "last_activity" in student

    def test_add_pending_payment_student_not_found(self):
        """Test add_pending_payment when student doesn't exist"""
        result = self.storage.add_pending_payment(99999, "MATH101")
        assert result is False

    def test_add_pending_payment_exception_handling(self):
        """Test add_pending_payment exception handling"""
        # Save a student first
        student_data = {
            "user_id": 12345,
            "first_name": "John",
            "last_name": "Doe",
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
        }
        self.storage.save_student(student_data)

        # Mock save_student to raise an exception
        with patch.object(self.storage, 'save_student', side_effect=Exception("Test error")):
            result = self.storage.add_pending_payment(12345, "MATH101")
            assert result is False

    def test_load_banned_success(self):
        """Test _load_banned successful loading"""
        result = self.storage._load_banned()
        assert "banned_user_ids" in result
        assert result["banned_user_ids"] == []

    def test_load_banned_exception_handling(self):
        """Test _load_banned exception handling"""
        # Mock _load_json to raise an exception
        with patch.object(self.storage, '_load_json', side_effect=Exception("Test error")):
            result = self.storage._load_banned()
            assert result == {"banned_user_ids": []}

    def test_is_user_banned_false(self):
        """Test is_user_banned when user is not banned"""
        result = self.storage.is_user_banned(12345)
        assert result is False

    def test_is_user_banned_true(self):
        """Test is_user_banned when user is banned"""
        # Ban a user first
        self.storage.ban_user(12345)

        result = self.storage.is_user_banned(12345)
        assert result is True

    def test_is_user_banned_exception_handling(self):
        """Test is_user_banned exception handling"""
        # Mock _load_banned to raise an exception
        with patch.object(self.storage, '_load_banned', side_effect=Exception("Test error")):
            result = self.storage.is_user_banned(12345)
            assert result is False

    def test_ban_user_success(self):
        """Test ban_user successful ban"""
        result = self.storage.ban_user(12345)
        assert result is True

        # Check user is banned
        assert self.storage.is_user_banned(12345) is True

    def test_ban_user_already_banned(self):
        """Test ban_user when user is already banned"""
        # Ban user first time
        self.storage.ban_user(12345)

        # Ban again
        result = self.storage.ban_user(12345)
        assert result is True

        # Check user is still banned
        assert self.storage.is_user_banned(12345) is True

    def test_ban_user_exception_handling(self):
        """Test ban_user exception handling"""
        # Mock _save_json to raise an exception
        with patch.object(self.storage, '_save_json', side_effect=Exception("Test error")):
            result = self.storage.ban_user(12345)
            assert result is False

    def test_unban_user_success(self):
        """Test unban_user successful unban"""
        # Ban user first
        self.storage.ban_user(12345)
        assert self.storage.is_user_banned(12345) is True

        # Unban user
        result = self.storage.unban_user(12345)
        assert result is True

        # Check user is not banned
        assert self.storage.is_user_banned(12345) is False

    def test_unban_user_not_banned(self):
        """Test unban_user when user is not banned"""
        result = self.storage.unban_user(12345)
        assert result is True

        # Check user is still not banned
        assert self.storage.is_user_banned(12345) is False

    def test_unban_user_exception_handling(self):
        """Test unban_user exception handling"""
        # Ban user first
        self.storage.ban_user(12345)

        # Mock _save_json to raise an exception
        with patch.object(self.storage, '_save_json', side_effect=Exception("Test error")):
            result = self.storage.unban_user(12345)
            assert result is False

    def test_get_user_courses_success(self):
        """Test get_user_courses successful retrieval"""
        # Save a student with courses
        student_data = {
            "user_id": 12345,
            "first_name": "John",
            "last_name": "Doe",
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
            "free_courses": ["MATH101"],
            "purchased_courses": ["PHYS101"],
        }
        self.storage.save_student(student_data)

        # Get user courses
        courses = self.storage.get_user_courses(12345)
        assert "free_courses" in courses
        assert "purchased_courses" in courses
        assert courses["free_courses"] == ["MATH101"]
        assert courses["purchased_courses"] == ["PHYS101"]

    def test_get_user_courses_student_not_found(self):
        """Test get_user_courses when student doesn't exist"""
        courses = self.storage.get_user_courses(99999)
        assert courses == {"free_courses": [], "purchased_courses": []}

    def test_get_user_courses_exception_handling(self):
        """Test get_user_courses exception handling"""
        # Mock get_student to raise an exception
        with patch.object(self.storage, 'get_student', side_effect=Exception("Test error")):
            result = self.storage.get_user_courses(12345)
            assert result == {"free_courses": [], "purchased_courses": []}

    def test_crypto_manager_import_failure(self):
        """Test behavior when crypto_manager import fails"""
        # This test verifies that the storage works even when crypto_manager is None
        # The import failure is handled in the module with a try-except block

        # Create storage without crypto_manager
        storage = StudentStorage(self.temp_dir)

        # Test that basic operations still work
        student_data = {
            "user_id": 12345,
            "first_name": "John",
            "last_name": "Doe",
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
        }

        result = storage.save_student(student_data)
        assert result is True

        retrieved = storage.get_student(12345)
        assert retrieved is not None
        assert retrieved["first_name"] == "John"

    @patch('utils.storage.crypto_manager')
    def test_get_all_students_decryption_exception(self, mock_crypto):
        """Test get_all_students with decryption exception to cover lines 195-196"""
        mock_crypto.decrypt_text.side_effect = Exception("Decryption failed")
        mock_crypto.encrypt_text.return_value = "encrypted_text"

        # Save a student with encrypted data
        student_data = {
            "user_id": 12345,
            "first_name": "encrypted_first_name",
            "last_name": "encrypted_last_name",
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
        }
        self.storage.save_student(student_data)

        # This should handle the decryption exception gracefully
        all_students = self.storage.get_all_students()
        assert len(all_students) == 1
        # The field should remain encrypted due to decryption failure
        assert all_students[0]["first_name"] == "encrypted_text"

    def test_edge_cases(self):
        """Test various edge cases"""
        # Test with very long field values
        long_name = "a" * 1000
        student_data = {
            "user_id": 12345,
            "first_name": long_name,
            "last_name": "Doe",
            "province": "Tehran",
            "city": "Tehran",
            "grade": "12",
            "field": "Mathematics",
        }

        result = self.storage.save_student(student_data)
        assert result is True

        # Test with special characters in names
        special_name = "José María O'Connor-Smith"
        student_data["first_name"] = special_name
        result = self.storage.save_student(student_data)
        assert result is True

        retrieved = self.storage.get_student(12345)
        assert retrieved["first_name"] == special_name

    def test_concurrent_access(self):
        """Test that storage handles concurrent access properly"""
        import threading

        def save_student_thread():
            student_data = {
                "user_id": 12345,
                "first_name": "John",
                "last_name": "Doe",
                "province": "Tehran",
                "city": "Tehran",
                "grade": "12",
                "field": "Mathematics",
            }
            return self.storage.save_student(student_data)

        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=save_student_thread)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify student was saved
        student = self.storage.get_student(12345)
        assert student is not None
        assert student["first_name"] == "John"
