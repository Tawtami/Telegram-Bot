#!/usr/bin/env python3
"""
Custom Test Runner for Existing Test Files

This script runs our existing test files without requiring pytest.
It imports and executes test functions from our test modules.
"""

import os
import sys
import importlib
import inspect
import traceback
from pathlib import Path


# Set up mocks globally before any imports
def setup_global_mocks():
    """Set up all mocks globally before importing test modules"""
    # Import mock modules first
    import pytest_mock
    import sqlalchemy_mock
    import telegram_mock
    import cryptography_mock
    import sentry_mock
    import aiohttp_mock
    import database_mock
    import database_service_mock
    import database_migrate_mock
    import yarl_mock

    # Make mocks available globally
    globals()['pytest_mock'] = pytest_mock
    globals()['sqlalchemy_mock'] = sqlalchemy_mock
    globals()['telegram_mock'] = telegram_mock
    globals()['cryptography_mock'] = cryptography_mock
    globals()['sentry_mock'] = sentry_mock
    globals()['aiohttp_mock'] = aiohttp_mock
    globals()['database_mock'] = database_mock
    globals()['database_service_mock'] = database_service_mock
    globals()['database_migrate_mock'] = database_migrate_mock
    globals()['yarl_mock'] = yarl_mock

    # Ensure our mocks are used BEFORE any imports
    sys.modules['sqlalchemy'] = sqlalchemy_mock
    sys.modules['sqlalchemy.exc'] = database_mock
    sys.modules['telegram'] = telegram_mock
    sys.modules['cryptography'] = cryptography_mock
    sys.modules['sentry_sdk'] = sentry_mock
    sys.modules['aiohttp'] = aiohttp_mock
    sys.modules['database.models_sql'] = database_mock
    sys.modules['database.db'] = database_mock.database_db_module
    sys.modules['database.service'] = database_mock.database_service_module
    sys.modules['database.migrate'] = database_migrate_mock
    sys.modules['yarl'] = yarl_mock

    # Also mock specific aiohttp imports that tests might use
    sys.modules['aiohttp.ClientSession'] = aiohttp_mock.ClientSession
    sys.modules['aiohttp.CookieJar'] = aiohttp_mock.CookieJar


# Set up mocks immediately
setup_global_mocks()


def run_test_file(test_file_path):
    """Run all test functions in a test file"""
    print(f"\nRunning tests from: {test_file_path}")
    print("-" * 60)

    try:
        # Import the test module
        module_name = str(test_file_path).replace('/', '.').replace('\\', '.').replace('.py', '')
        if module_name.startswith('.'):
            module_name = module_name[1:]

        # Add tests directory to path
        sys.path.insert(0, os.path.dirname(test_file_path))

        # Import the module
        module = importlib.import_module(module_name)

        # Find all test functions
        test_functions = []
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) and name.startswith('test_'):
                test_functions.append((name, obj))

        if not test_functions:
            print("⚠️ No test functions found")
            return True

        print(f"Found {len(test_functions)} test functions")

        # Run each test function
        passed = 0
        failed = 0

        for test_name, test_func in test_functions:
            try:
                print(f"  Running {test_name}...", end=" ")

                # Check if test function expects pytest fixtures
                sig = inspect.signature(test_func)
                params = list(sig.parameters.keys())

                # Provide mock fixtures if needed
                kwargs = {}
                # Provide simple fallbacks if pytest_mock isn't available in this context
                try:
                    if 'monkeypatch' in params:
                        kwargs['monkeypatch'] = pytest_mock.monkeypatch()
                    if 'caplog' in params:
                        kwargs['caplog'] = pytest_mock.caplog()
                    if 'tmp_path' in params:
                        kwargs['tmp_path'] = pytest_mock.tmp_path()
                except NameError:
                    pass
                if 'session' in params:
                    # Import and create a mock session from our database_mock
                    import database_mock

                    kwargs['session'] = database_mock.Session()

                # Check if test function is async
                if inspect.iscoroutinefunction(test_func):
                    # Handle async tests
                    import asyncio

                    try:
                        result = asyncio.run(test_func(**kwargs))
                        if result is False:
                            print("FAILED")
                            failed += 1
                        else:
                            print("PASSED")
                            passed += 1
                    except Exception as e:
                        print(f"ASYNC ERROR: {e}")
                        failed += 1
                        traceback.print_exc()
                else:
                    # Handle sync tests
                    result = test_func(**kwargs)

                    if result is False:
                        print("FAILED")
                        failed += 1
                    else:
                        print("PASSED")
                        passed += 1

            except Exception as e:
                print(f"ERROR: {e}")
                failed += 1
                # Print traceback for debugging
                traceback.print_exc()

        print(f"\nResults: {passed} passed, {failed} failed")
        return failed == 0

    except Exception as e:
        print(f"Failed to run tests: {e}")
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all test files"""
    print("Running All Existing Tests")
    print("=" * 60)

    # Find all test files
    test_dir = Path("tests")
    test_files = list(test_dir.glob("test_*.py"))

    if not test_files:
        print("No test files found in tests/ directory")
        return False

    print(f"Found {len(test_files)} test files")

    # Run tests
    total_passed = 0
    total_failed = 0

    for test_file in test_files:
        try:
            if run_test_file(test_file):
                total_passed += 1
            else:
                total_failed += 1
        except Exception as e:
            print(f"Error running {test_file}: {e}")
            total_failed += 1

    # Summary
    print("\n" + "=" * 60)
    print("FINAL TEST RESULTS")
    print("=" * 60)
    print(f"Test files passed: {total_passed}")
    print(f"Test files failed: {total_failed}")
    print(f"Total test files: {len(test_files)}")

    if total_failed == 0:
        print("\nAll test files passed!")
        return True
    else:
        print(f"\n{total_failed} test files had issues")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
