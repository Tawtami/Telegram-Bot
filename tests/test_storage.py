#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for storage.py
"""
import pytest
import json
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from utils.storage import StudentStorage


class TestStudentStorage:
    """Test cases for StudentStorage class"""

    def setup_method(self):
        """Set up test environment before each test"""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.storage = StudentStorage(self.temp_dir)

    def teardown_method(self):
        """Clean up test environment after each test"""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """Test StudentStorage initialization"""
        assert self.storage.data_dir == Path(self.temp_dir)
        assert self.storage.students_file == Path(self.temp_dir) / "students.json"
        assert self.storage.courses_file == Path(self.temp_dir) / "courses.json"
        assert self.storage.purchases_file == Path(self.temp_dir) / "purchases.json"
        assert self.storage.banned_file == Path(self.temp_dir) / "banned.json"
        assert hasattr(self.storage, 'lock')
        assert self.storage._cache == {}
        assert self.storage._cache_ttl == 300

    def test_initialize_files(self):
        """Test file initialization"""
        # Check that files were created
        assert self.storage.students_file.exists()
        assert self.storage.purchases_file.exists()
        assert self.storage.banned_file.exists()

        # Check file contents
        with open(self.storage.students_file, 'r', encoding='utf-8') as f:
            students_data = json.load(f)
            assert students_data == {"students": []}

        with open(self.storage.purchases_file, 'r', encoding='utf-8') as f:
            purchases_data = json.load(f)
            assert purchases_data == {"purchases": []}

        with open(self.storage.banned_file, 'r', encoding='utf-8') as f:
            banned_data = json.load(f)
            assert banned_data == {"banned_user_ids": []}

    def test_load_json_cache_hit(self):
        """Test JSON loading with cache hit"""
        # Mock time to control cache behavior
        with patch('time.time') as mock_time:
            mock_time.return_value = 1000.0

            # First load - should hit file
            data1 = self.storage._load_json(self.storage.students_file)
            assert data1 == {"students": []}

            # Second load within TTL - should hit cache
            mock_time.return_value = 1200.0  # 200 seconds later, still within 300s TTL
            data2 = self.storage._load_json(self.storage.students_file)
            assert data2 == {"students": []}

    def test_load_json_cache_expiry(self):
        """Test JSON loading with cache expiry"""
        with patch('time.time') as mock_time:
            mock_time.return_value = 1000.0

            # First load
            data1 = self.storage._load_json(self.storage.students_file)
            assert data1 == {"students": []}

            # Load after cache expiry
            mock_time.return_value = 1400.0  # 400 seconds later, beyond 300s TTL
            data2 = self.storage._load_json(self.storage.students_file)
            assert data2 == {"students": []}

    def test_load_json_file_not_exists(self):
        """Test JSON loading when file doesn't exist"""
        non_existent_file = Path(self.temp_dir) / "nonexistent.json"
        data = self.storage._load_json(non_existent_file)
        assert data == {}

    def test_load_json_invalid_json(self):
        """Test JSON loading with invalid JSON content"""
        invalid_file = Path(self.temp_dir) / "invalid.json"

        # Create file with invalid JSON
        with open(invalid_file, 'w', encoding='utf-8') as f:
            f.write('{"invalid": json}')

        with patch('utils.storage.logger') as mock_logger:
            data = self.storage._load_json(invalid_file)
            assert data == {}
            mock_logger.error.assert_called_once()

    def test_save_json_success(self):
        """Test successful JSON saving"""
        test_data = {"test": "data"}
        test_file = Path(self.temp_dir) / "test.json"

        self.storage._save_json(test_file, test_data)

        # Check file was created and contains correct data
        assert test_file.exists()
        with open(test_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            assert saved_data == test_data

    def test_save_json_error_handling(self):
        """Test JSON saving error handling"""
        test_data = {"test": "data"}
        test_file = Path(self.temp_dir) / "test.json"

        # Mock open to raise an exception
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with patch('utils.storage.logger') as mock_logger:
                self.storage._save_json(test_file, test_data)
                mock_logger.error.assert_called_once()

    def test_save_student_success_new(self):
        """Test successful student saving (new student)"""
        student_data = {
            "user_id": 12345,
            "first_name": "علی",
            "last_name": "احمدی",
            "province": "تهران",
            "city": "تهران",
            "grade": "دوازدهم",
            "field": "ریاضی",
        }

        result = self.storage.save_student(student_data)
        assert result is True

        # Verify student was saved
        saved_student = self.storage.get_student(12345)
        assert saved_student is not None
        assert saved_student["user_id"] == 12345
        assert saved_student["first_name"] == "علی"
        assert "registration_date" in saved_student
        assert "last_updated" in saved_student

    def test_save_student_success_update(self):
        """Test successful student saving (update existing)"""
        # First, save a student
        student_data = {
            "user_id": 12345,
            "first_name": "علی",
            "last_name": "احمدی",
            "province": "تهران",
            "city": "تهران",
            "grade": "دوازدهم",
            "field": "ریاضی",
        }
        self.storage.save_student(student_data)

        # Update the student
        updated_data = student_data.copy()
        updated_data["grade"] = "یازدهم"

        result = self.storage.save_student(updated_data)
        assert result is True

        # Verify update
        updated_student = self.storage.get_student(12345)
        assert updated_student["grade"] == "یازدهم"

    def test_save_student_missing_required_fields(self):
        """Test student saving with missing required fields"""
        incomplete_data = {
            "user_id": 12345,
            "first_name": "علی",
            # Missing other required fields
        }

        with patch('utils.storage.logger') as mock_logger:
            result = self.storage.save_student(incomplete_data)
            assert result is False
            mock_logger.error.assert_called_once()

    def test_save_student_invalid_user_id(self):
        """Test student saving with invalid user_id"""
        invalid_data = {
            "user_id": "invalid_id",
            "first_name": "علی",
            "last_name": "احمدی",
            "province": "تهران",
            "city": "تهران",
            "grade": "دوازدهم",
            "field": "ریاضی",
        }

        with patch('utils.storage.logger') as mock_logger:
            result = self.storage.save_student(invalid_data)
            assert result is False
            mock_logger.error.assert_called_once()

    def test_save_student_with_encryption(self):
        """Test student saving with encryption enabled"""
        with patch('utils.storage.crypto_manager') as mock_crypto:
            mock_crypto.encrypt_text.return_value = "encrypted_text"

            student_data = {
                "user_id": 12345,
                "first_name": "علی",
                "last_name": "احمدی",
                "province": "تهران",
                "city": "تهران",
                "grade": "دوازدهم",
                "field": "ریاضی",
                "phone_number": "09123456789",
            }

            result = self.storage.save_student(student_data)
            assert result is True

            # Verify encryption was called for sensitive fields
            assert mock_crypto.encrypt_text.call_count == 3  # first_name, last_name, phone_number

    def test_save_student_encryption_disabled(self):
        """Test student saving when encryption is disabled"""
        with patch('utils.storage.crypto_manager', None):
            student_data = {
                "user_id": 12345,
                "first_name": "علی",
                "last_name": "احمدی",
                "province": "تهران",
                "city": "تهران",
                "grade": "دوازدهم",
                "field": "ریاضی",
            }

            result = self.storage.save_student(student_data)
            assert result is True

    def test_save_student_exception_handling(self):
        """Test student saving exception handling"""
        with patch.object(self.storage, '_load_json', side_effect=Exception("Test error")):
            with patch('utils.storage.logger') as mock_logger:
                student_data = {
                    "user_id": 12345,
                    "first_name": "علی",
                    "last_name": "احمدی",
                    "province": "تهران",
                    "city": "تهران",
                    "grade": "دوازدهم",
                    "field": "ریاضی",
                }

                result = self.storage.save_student(student_data)
                assert result is False
                mock_logger.error.assert_called_once()

    def test_get_student_success(self):
        """Test successful student retrieval"""
        # Save a student first
        student_data = {
            "user_id": 12345,
            "first_name": "علی",
            "last_name": "احمدی",
            "province": "تهران",
            "city": "تهران",
            "grade": "دوازدهم",
            "field": "ریاضی",
        }
        self.storage.save_student(student_data)

        # Retrieve the student
        retrieved = self.storage.get_student(12345)
        assert retrieved is not None
        assert retrieved["user_id"] == 12345
        assert retrieved["first_name"] == "علی"

    def test_get_student_not_found(self):
        """Test student retrieval when student doesn't exist"""
        result = self.storage.get_student(99999)
        assert result is None

    def test_get_student_with_decryption(self):
        """Test student retrieval with decryption"""
        with patch('utils.storage.crypto_manager') as mock_crypto:
            mock_crypto.decrypt_text.return_value = "decrypted_text"

            # Save encrypted student data
            student_data = {
                "user_id": 12345,
                "first_name": "encrypted_first",
                "last_name": "encrypted_last",
                "province": "تهران",
                "city": "تهران",
                "grade": "دوازدهم",
                "field": "ریاضی",
            }
            self.storage.save_student(student_data)

            # Retrieve and verify decryption
            retrieved = self.storage.get_student(12345)
            assert retrieved is not None
            assert mock_crypto.decrypt_text.call_count >= 2

    def test_get_student_decryption_error(self):
        """Test student retrieval when decryption fails"""
        with patch('utils.storage.crypto_manager') as mock_crypto:
            mock_crypto.decrypt_text.side_effect = Exception("Decryption failed")

            # Save student data
            student_data = {
                "user_id": 12345,
                "first_name": "علی",
                "last_name": "احمدی",
                "province": "تهران",
                "city": "تهران",
                "grade": "دوازدهم",
                "field": "ریاضی",
            }
            self.storage.save_student(student_data)

            # Should still retrieve student even if decryption fails
            retrieved = self.storage.get_student(12345)
            assert retrieved is not None

    def test_get_all_students(self):
        """Test retrieving all students"""
        # Save multiple students
        students = [
            {
                "user_id": 12345,
                "first_name": "علی",
                "last_name": "احمدی",
                "province": "تهران",
                "city": "تهران",
                "grade": "دوازدهم",
                "field": "ریاضی",
            },
            {
                "user_id": 67890,
                "first_name": "فاطمه",
                "last_name": "محمدی",
                "province": "اصفهان",
                "city": "اصفهان",
                "grade": "یازدهم",
                "field": "تجربی",
            },
        ]

        for student in students:
            self.storage.save_student(student)

        all_students = self.storage.get_all_students()
        assert len(all_students) == 2
        assert any(s["user_id"] == 12345 for s in all_students)
        assert any(s["user_id"] == 67890 for s in all_students)

    def test_save_course_registration_paid(self):
        """Test course registration for paid course"""
        # Save a student first
        student_data = {
            "user_id": 12345,
            "first_name": "علی",
            "last_name": "احمدی",
            "province": "تهران",
            "city": "تهران",
            "grade": "دوازدهم",
            "field": "ریاضی",
        }
        self.storage.save_student(student_data)

        # Register for paid course
        result = self.storage.save_course_registration(12345, "course_math_101", is_paid=True)
        assert result is True

        # Verify course was added
        student = self.storage.get_student(12345)
        assert "course_math_101" in student.get("purchased_courses", [])

    def test_save_course_registration_free(self):
        """Test course registration for free course"""
        # Save a student first
        student_data = {
            "user_id": 12345,
            "first_name": "علی",
            "last_name": "احمدی",
            "province": "تهران",
            "city": "تهران",
            "grade": "دوازدهم",
            "field": "ریاضی",
        }
        self.storage.save_student(student_data)

        # Register for free course
        result = self.storage.save_course_registration(12345, "course_intro_101", is_paid=False)
        assert result is True

        # Verify course was added
        student = self.storage.get_student(12345)
        assert "course_intro_101" in student.get("free_courses", [])

    def test_save_course_registration_student_not_found(self):
        """Test course registration when student doesn't exist"""
        result = self.storage.save_course_registration(99999, "course_101", is_paid=True)
        assert result is False

    def test_save_book_purchase(self):
        """Test book purchase saving"""
        # Save a student first
        student_data = {
            "user_id": 12345,
            "first_name": "علی",
            "last_name": "احمدی",
            "province": "تهران",
            "city": "تهران",
            "grade": "دوازدهم",
            "field": "ریاضی",
        }
        self.storage.save_student(student_data)

        book_data = {"book_id": "book_math_101", "title": "ریاضی دوازدهم", "price": 50000}

        result = self.storage.save_book_purchase(12345, book_data)
        assert result is True

        # Verify book purchase was saved
        student = self.storage.get_student(12345)
        assert "book_purchases" in student
        assert len(student["book_purchases"]) == 1
        assert student["book_purchases"][0]["book_id"] == "book_math_101"
        assert "purchase_date" in student["book_purchases"][0]

    def test_confirm_payment_success(self):
        """Test successful payment confirmation"""
        # Save a student with pending payments
        student_data = {
            "user_id": 12345,
            "first_name": "علی",
            "last_name": "احمدی",
            "province": "تهران",
            "city": "تهران",
            "grade": "دوازدهم",
            "field": "ریاضی",
            "pending_payments": ["course_math_101", "course_physics_101"],
        }
        self.storage.save_student(student_data)

        # Confirm payment
        result = self.storage.confirm_payment(12345)
        assert result is True

        # Verify pending payments moved to purchased
        student = self.storage.get_student(12345)
        assert "pending_payments" not in student
        assert "course_math_101" in student.get("purchased_courses", [])
        assert "course_physics_101" in student.get("purchased_courses", [])

    def test_confirm_payment_no_pending(self):
        """Test payment confirmation when no pending payments"""
        # Save a student without pending payments
        student_data = {
            "user_id": 12345,
            "first_name": "علی",
            "last_name": "احمدی",
            "province": "تهران",
            "city": "تهران",
            "grade": "دوازدهم",
            "field": "ریاضی",
        }
        self.storage.save_student(student_data)

        result = self.storage.confirm_payment(12345)
        assert result is False

    def test_add_pending_payment(self):
        """Test adding pending payment"""
        # Save a student first
        student_data = {
            "user_id": 12345,
            "first_name": "علی",
            "last_name": "احمدی",
            "province": "تهران",
            "city": "تهران",
            "grade": "دوازدهم",
            "field": "ریاضی",
        }
        self.storage.save_student(student_data)

        # Add pending payment
        result = self.storage.add_pending_payment(12345, "course_math_101")
        assert result is True

        # Verify pending payment was added
        student = self.storage.get_student(12345)
        assert "pending_payments" in student
        assert "course_math_101" in student["pending_payments"]

    def test_ban_management(self):
        """Test ban management functionality"""
        # Test initial state
        assert not self.storage.is_user_banned(12345)

        # Ban user
        result = self.storage.ban_user(12345)
        assert result is True
        assert self.storage.is_user_banned(12345)

        # Unban user
        result = self.storage.unban_user(12345)
        assert result is True
        assert not self.storage.is_user_banned(12345)

    def test_ban_user_already_banned(self):
        """Test banning already banned user"""
        # Ban user first
        self.storage.ban_user(12345)

        # Try to ban again
        result = self.storage.ban_user(12345)
        assert result is True  # Should still return True

    def test_unban_user_not_banned(self):
        """Test unbanning user who is not banned"""
        result = self.storage.unban_user(12345)
        assert result is True  # Should still return True

    def test_get_user_courses(self):
        """Test getting user courses"""
        # Save a student with courses
        student_data = {
            "user_id": 12345,
            "first_name": "علی",
            "last_name": "احمدی",
            "province": "تهران",
            "city": "تهران",
            "grade": "دوازدهم",
            "field": "ریاضی",
            "free_courses": ["course_intro_101"],
            "purchased_courses": ["course_math_101", "course_physics_101"],
        }
        self.storage.save_student(student_data)

        courses = self.storage.get_user_courses(12345)
        assert courses["free_courses"] == ["course_intro_101"]
        assert courses["purchased_courses"] == ["course_math_101", "course_physics_101"]

    def test_get_user_courses_no_student(self):
        """Test getting courses for non-existent student"""
        courses = self.storage.get_user_courses(99999)
        assert courses == {"free_courses": [], "purchased_courses": []}

    def test_thread_safety(self):
        """Test thread safety of storage operations"""
        import threading

        def save_students():
            for i in range(10):
                student_data = {
                    "user_id": 1000 + i,
                    "first_name": f"Student{i}",
                    "last_name": f"Last{i}",
                    "province": "تهران",
                    "city": "تهران",
                    "grade": "دوازدهم",
                    "field": "ریاضی",
                }
                self.storage.save_student(student_data)

        # Create multiple threads
        threads = [threading.Thread(target=save_students) for _ in range(3)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all students were saved
        all_students = self.storage.get_all_students()
        assert len(all_students) == 30  # 3 threads * 10 students each
