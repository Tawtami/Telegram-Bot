#!/usr/bin/env python3
"""
Tests for setup_dev.py to achieve 100% coverage
"""

import pytest
import os
import sys
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from setup_dev import (
    check_python_version,
    check_dependencies,
    check_environment,
    check_data_files,
    check_file_permissions,
    provide_setup_instructions,
    main,
)


class TestSetupDev:
    """Test setup_dev.py module functions"""

    def test_check_python_version_compatible(self):
        """Test check_python_version with compatible Python version"""
        with patch('sys.version_info') as mock_version:
            # Create a mock that behaves like a version info tuple
            mock_version.major = 3
            mock_version.minor = 9
            mock_version.micro = 0

            # Make the mock comparable to tuples
            def mock_lt(self, other):
                return (mock_version.major, mock_version.minor, mock_version.micro) < other

            mock_version.__lt__ = mock_lt

            result = check_python_version()
            assert result is True

    def test_check_python_version_old(self):
        """Test check_python_version with old Python version"""
        with patch('sys.version_info') as mock_version:
            # Create a mock that behaves like a version info tuple
            mock_version.major = 3
            mock_version.minor = 7
            mock_version.micro = 0

            # Make the mock comparable to tuples
            def mock_lt(self, other):
                return (mock_version.major, mock_version.minor, mock_version.micro) < other

            mock_version.__lt__ = mock_lt

            result = check_python_version()
            assert result is False

    def test_check_python_version_recommended(self):
        """Test check_python_version with recommended Python version"""
        with patch('sys.version_info') as mock_version:
            # Create a mock that behaves like a version info tuple
            mock_version.major = 3
            mock_version.minor = 11
            mock_version.micro = 0

            # Make the mock comparable to tuples
            def mock_lt(self, other):
                return (mock_version.major, mock_version.minor, mock_version.micro) < other

            mock_version.__lt__ = mock_lt

            result = check_python_version()
            assert result is True

    @patch('builtins.print')
    def test_check_dependencies_all_installed(self, mock_print):
        """Test check_dependencies when all packages are installed"""
        # Mock the actual imports that exist in setup_dev.py
        with patch('builtins.__import__') as mock_import:
            # Mock successful imports
            mock_import.return_value = MagicMock(__version__="20.7")

            missing = check_dependencies()

            assert missing == []
            # Verify print calls for successful packages
            assert mock_print.call_count >= 4

    @patch('builtins.print')
    def test_check_dependencies_missing_packages(self, mock_print):
        """Test check_dependencies when some packages are missing"""
        with patch('builtins.__import__') as mock_import:
            # Mock some successful imports and some failed ones
            def mock_import_side_effect(name, *args, **kwargs):
                if name in ['telegram', 'dotenv']:
                    mock_module = MagicMock()
                    mock_module.__version__ = "20.7" if name == 'telegram' else "1.0.1"
                    return mock_module
                else:
                    raise ImportError(f"No module named '{name}'")

            mock_import.side_effect = mock_import_side_effect

            missing = check_dependencies()

            # Should have missing packages
            assert len(missing) > 0

    @patch('builtins.print')
    def test_check_environment_all_vars_set(self, mock_print):
        """Test check_environment when all required variables are set"""
        with patch.dict(
            os.environ,
            {
                'BOT_TOKEN': 'test_token',
                'ENVIRONMENT': 'production',
                'WEBHOOK_URL': 'https://test.com',
                'PORT': '8080',
            },
        ):
            missing = check_environment()

            assert missing == []
            # Verify print calls for environment variables
            assert mock_print.call_count >= 4

    @patch('builtins.print')
    def test_check_environment_missing_required(self, mock_print):
        """Test check_environment when required variables are missing"""
        with patch.dict(
            os.environ,
            {
                'ENVIRONMENT': 'production',
                'WEBHOOK_URL': 'https://test.com',
                # BOT_TOKEN is missing
            },
            clear=True,
        ):
            missing = check_environment()

            assert "BOT_TOKEN" in missing
            assert len(missing) == 1

    @patch('builtins.print')
    def test_check_data_files_all_exist(self, mock_print):
        """Test check_data_files when all required files exist"""
        with (
            patch('pathlib.Path.exists') as mock_exists,
            patch('pathlib.Path.read_text') as mock_read_text,
        ):

            mock_exists.return_value = True
            mock_read_text.side_effect = lambda: "{}"

            result = check_data_files()

            assert result == []  # No missing files
            assert mock_print.call_count >= 5

    @patch('builtins.print')
    def test_check_data_files_missing_files(self, mock_print):
        """Test check_data_files when some files are missing"""
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False

            result = check_data_files()

            assert len(result) == 5  # All files missing
            assert mock_print.call_count >= 1

    @patch('builtins.print')
    def test_check_data_files_data_dir_not_found(self, mock_print):
        """Test check_data_files when data directory doesn't exist"""
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False

            result = check_data_files()

            assert result == [
                "students.json",
                "courses.json",
                "books.json",
                "purchases.json",
                "notifications.json",
            ]

    @patch('builtins.print')
    def test_check_file_permissions_success(self, mock_print):
        """Test check_file_permissions when all files are readable"""
        with (
            patch('pathlib.Path.exists') as mock_exists,
            patch('builtins.open', mock_open(read_data="test")),
        ):

            mock_exists.return_value = True

            check_file_permissions()

            # Verify print calls for file permissions
            assert mock_print.call_count >= 3

    @patch('builtins.print')
    def test_check_file_permissions_unicode_error(self, mock_print):
        """Test check_file_permissions with Unicode decode error"""
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True

            # Mock open to raise UnicodeDecodeError first, then succeed with cp1252
            with patch('builtins.open') as mock_open:
                mock_open.side_effect = [
                    UnicodeDecodeError('utf-8', b'test', 0, 1, 'test'),
                    mock_open(read_data="test").return_value,
                ]

                check_file_permissions()

                assert mock_print.call_count >= 3

    @patch('builtins.print')
    def test_check_file_permissions_permission_error(self, mock_print):
        """Test check_file_permissions with permission error"""
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True

            with patch('builtins.open') as mock_open:
                mock_open.side_effect = PermissionError("Permission denied")

                check_file_permissions()

                assert mock_print.call_count >= 3

    @patch('builtins.print')
    def test_check_file_permissions_file_not_found(self, mock_print):
        """Test check_file_permissions when file doesn't exist"""
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False

            check_file_permissions()

            assert mock_print.call_count >= 3

    @patch('builtins.print')
    def test_provide_setup_instructions_with_missing_items(self, mock_print):
        """Test provide_setup_instructions with missing packages, env vars, and files"""
        missing_packages = ["telegram", "aiohttp"]
        missing_env_vars = ["BOT_TOKEN"]
        missing_files = ["students.json"]

        provide_setup_instructions(missing_packages, missing_env_vars, missing_files)

        # Verify instructions were printed
        assert mock_print.call_count >= 10

    @patch('builtins.print')
    def test_provide_setup_instructions_no_missing_items(self, mock_print):
        """Test provide_setup_instructions with no missing items"""
        provide_setup_instructions([], [], [])

        # Verify basic instructions were printed
        assert mock_print.call_count >= 5

    @patch('builtins.print')
    def test_main_success(self, mock_print):
        """Test main function when all checks pass"""
        with (
            patch('setup_dev.check_python_version', return_value=True),
            patch('setup_dev.check_dependencies', return_value=[]),
            patch('setup_dev.check_environment', return_value=[]),
            patch('setup_dev.check_data_files', return_value=[]),
            patch('setup_dev.check_file_permissions') as mock_check_perms,
            patch('setup_dev.provide_setup_instructions') as mock_provide,
        ):

            result = main()

            assert result is True
            mock_check_perms.assert_called_once()
            mock_provide.assert_called_once()

    @patch('builtins.print')
    def test_main_python_version_failure(self, mock_print):
        """Test main function when Python version check fails"""
        with (
            patch('setup_dev.check_python_version', return_value=False),
            patch('setup_dev.check_dependencies', return_value=[]),
            patch('setup_dev.check_environment', return_value=[]),
            patch('setup_dev.check_data_files', return_value=[]),
            patch('setup_dev.check_file_permissions') as mock_check_perms,
            patch('setup_dev.provide_setup_instructions') as mock_provide,
        ):

            result = main()

            assert result is False
            mock_check_perms.assert_called_once()
            mock_provide.assert_called_once()

    @patch('builtins.print')
    def test_main_with_missing_items(self, mock_print):
        """Test main function when some items are missing"""
        with (
            patch('setup_dev.check_python_version', return_value=True),
            patch('setup_dev.check_dependencies', return_value=['missing_package']),
            patch('setup_dev.check_environment', return_value=['BOT_TOKEN']),
            patch('setup_dev.check_data_files', return_value=['students.json']),
            patch('setup_dev.check_file_permissions') as mock_check_perms,
            patch('setup_dev.provide_setup_instructions') as mock_provide,
        ):

            result = main()

            assert result is False
            mock_check_perms.assert_called_once()
            mock_provide.assert_called_once()
