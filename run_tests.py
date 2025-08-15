#!/usr/bin/env python3
"""
Comprehensive test runner for CI/CD without external dependencies

This module provides a comprehensive testing framework that can run without
external dependencies like pytest. It performs:

- Python syntax validation
- Import dependency analysis
- Code quality checks
- CI/CD readiness validation
- File encoding verification

This is useful for environments where package installation is restricted
or for quick validation before running full test suites.
"""

import os
import sys
import importlib
import traceback
import ast
from pathlib import Path


def check_python_syntax(file_path):
    """Check if a Python file has valid syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            ast.parse(f.read())
        return None
    except SyntaxError as e:
        return f"{file_path}:{e.lineno}: {e}"
    except Exception as e:
        return f"{file_path}: {e}"


def check_imports(file_path):
    """Check if a Python file can be imported without external dependencies"""
    try:
        # Skip test files and files that likely need external deps
        if 'test_' in file_path or 'requirements' in file_path:
            return None

        # Try to compile and check for obvious import issues
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for common problematic imports
        problematic_imports = [
            'telegram',
            'sqlalchemy',
            'psycopg2',
            'aiohttp',
            'cryptography',
            'sentry_sdk',
            'openpyxl',
            'locust',
        ]

        for imp in problematic_imports:
            if f'import {imp}' in content or f'from {imp}' in content:
                return f"{file_path}: Requires external dependency '{imp}'"

        return None
    except Exception as e:
        return f"{file_path}: {e}"


def check_file_encoding(file_path):
    """Check if a file can be read with different encodings"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1)
        return None
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='cp1252') as f:
                f.read(1)
            return f"{file_path}: Uses CP1252 encoding (should be UTF-8)"
        except:
            return f"{file_path}: Encoding issues"
    except Exception as e:
        return f"{file_path}: {e}"


def run_comprehensive_tests():
    """Run comprehensive tests that don't require external dependencies"""
    print("Running comprehensive tests...")

    # Test 1: Check all Python files compile
    print("\nChecking Python syntax...")
    python_files = []
    for root, dirs, files in os.walk('.'):
        if 'venv' in root or '__pycache__' in root or '.git' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    syntax_errors = []
    import_issues = []
    encoding_issues = []

    for file_path in python_files:
        # Check syntax
        syntax_error = check_python_syntax(file_path)
        if syntax_error:
            syntax_errors.append(syntax_error)

        # Check imports
        import_issue = check_imports(file_path)
        if import_issue:
            import_issues.append(import_issue)

        # Check encoding
        encoding_issue = check_file_encoding(file_path)
        if encoding_issue:
            encoding_issues.append(encoding_issue)

    if syntax_errors:
        print("Syntax errors found:")
        for error in syntax_errors:
            print(f"  {error}")
    else:
        print("All Python files compile successfully")

    if import_issues:
        print(f"\n{len(import_issues)} files have external dependency requirements:")
        for issue in import_issues[:5]:  # Show first 5
            print(f"  {issue}")
        if len(import_issues) > 5:
            print(f"  ... and {len(import_issues) - 5} more")

    if encoding_issues:
        print(f"\n{len(encoding_issues)} files have encoding issues:")
        for issue in encoding_issues[:5]:  # Show first 5
            print(f"  {issue}")
        if len(encoding_issues) > 5:
            print(f"  ... and {len(encoding_issues) - 5} more")

    # Test 2: Check core modules can be imported
    print("\nChecking core module imports...")
    core_modules = ['core', 'config']

    import_errors = []
    for module in core_modules:
        try:
            importlib.import_module(module)
            print(f"OK: {module} imported successfully")
        except Exception as e:
            import_errors.append(f"{module}: {e}")
            print(f"FAIL: {module} import failed: {e}")

    # Test 3: Check for obvious issues in test files
    print("\nChecking test files...")
    test_files = [f for f in python_files if 'test_' in f]
    print(f"Found {len(test_files)} test files")

    # Test 4: Check configuration
    print("\nChecking configuration...")
    try:
        import config

        print("config.py loaded successfully")
    except Exception as e:
        print(f"config.py load failed: {e}")
        import_errors.append(f"config: {e}")

    # Test 5: Check for common code quality issues
    print("\nChecking code quality...")
    quality_issues = []

    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

                # Check for hardcoded secrets
                if (
                    'password' in content.lower()
                    or 'secret' in content.lower()
                    or 'token' in content.lower()
                ):
                    if not any(env_var in content for env_var in ['os.getenv', 'os.environ']):
                        quality_issues.append(f"{file_path}: Potential hardcoded secrets")

                # Check for long lines
                long_lines = [i + 1 for i, line in enumerate(lines) if len(line) > 120]
                if long_lines:
                    quality_issues.append(f"{file_path}: Long lines at {long_lines[:3]}")

                # Check for missing docstrings in functions/classes
                if 'def ' in content or 'class ' in content:
                    if not content.strip().startswith('"""') and not content.strip().startswith(
                        "'''"
                    ):
                        quality_issues.append(f"{file_path}: Missing module docstring")

        except Exception as e:
            quality_issues.append(f"{file_path}: Error during quality check - {e}")

    if quality_issues:
        print(f"{len(quality_issues)} quality issues found:")
        for issue in quality_issues[:5]:  # Show first 5
            print(f"  {issue}")
        if len(quality_issues) > 5:
            print(f"  ... and {len(quality_issues) - 5} more")
    else:
        print("No obvious quality issues found")

    # Test 6: Check for CI/CD specific issues
    print("\nChecking CI/CD readiness...")
    ci_issues = []

    # Check if requirements.txt exists and is readable
    if os.path.exists('requirements.txt'):
        try:
            with open('requirements.txt', 'r') as f:
                requirements = f.read()
            print("requirements.txt exists and is readable")
        except Exception as e:
            ci_issues.append(f"requirements.txt: {e}")
    else:
        ci_issues.append("requirements.txt: Missing")

    # Check if pytest.ini exists
    if os.path.exists('pytest.ini'):
        print("pytest.ini exists")
    else:
        ci_issues.append("pytest.ini: Missing")

    # Check if there are any obvious CI/CD configuration files
    ci_files = ['.github', '.gitlab-ci.yml', 'azure-pipelines.yml', 'Jenkinsfile', 'circle.yml']
    found_ci = False
    for ci_file in ci_files:
        if os.path.exists(ci_file):
            print(f"CI/CD config found: {ci_file}")
            found_ci = True
            break

    if not found_ci:
        ci_issues.append("No CI/CD configuration files found")

    if ci_issues:
        print(f"{len(ci_issues)} CI/CD issues found:")
        for issue in ci_issues:
            print(f"  {issue}")
    else:
        print("CI/CD configuration looks good")

    # Summary
    print("\n" + "=" * 60)
    print("COMPREHENSIVE TEST SUMMARY")
    print("=" * 60)

    total_issues = len(syntax_errors) + len(import_errors) + len(quality_issues) + len(ci_issues)

    if syntax_errors:
        print(f"{len(syntax_errors)} syntax errors found")
        return False

    if total_issues == 0:
        print("All tests passed! Code is ready for CI/CD")
        return True
    else:
        print(f"{total_issues} issues found that should be addressed")
        print("\nTo run full tests, install dependencies:")
        print("   pip install -r requirements.txt")
        print("   python -m pytest tests/")
        return False


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
