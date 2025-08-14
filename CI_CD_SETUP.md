# CI/CD Setup and Testing Guide

This document describes the CI/CD pipeline setup and testing procedures for the Ostad Hatami Bot project.

## Overview

The project uses GitHub Actions for continuous integration and deployment. The CI/CD pipeline runs on every push to the main branch and on pull requests.

## CI/CD Pipeline

### GitHub Actions Workflows

Located in `.github/workflows/`:

- **main.yml** - Main CI/CD pipeline for testing and validation
- **benchmark.yml** - Performance benchmarking
- **autoformat.yml** - Code formatting and linting
- **alembic.yml** - Database migration testing

### Main Pipeline Steps

1. **Code Checkout** - Clones the repository
2. **Python Setup** - Sets up Python 3.11 environment
3. **Dependency Installation** - Installs requirements from `requirements.txt`
4. **Syntax Check** - Validates Python syntax for core files
5. **CI/CD Tests** - Runs comprehensive tests using `ci_test.py`
6. **Pytest** - Runs the full test suite
7. **File Structure Check** - Validates required files exist
8. **Success** - Confirms deployment readiness

## Testing Strategy

### 1. Syntax Validation

All Python files are checked for valid syntax using `python -m py_compile`.

### 2. CI/CD Tests (`ci_test.py`)

A comprehensive test suite that runs without external dependencies:

- **Syntax Testing** - Validates all Python files compile
- **Core Module Imports** - Tests core modules can be imported
- **Handler Module Imports** - Tests handler modules (expected to fail without deps)
- **Utility Module Imports** - Tests utility modules
- **Database Module Imports** - Tests database modules (expected to fail without deps)
- **Configuration Testing** - Tests config loading
- **File Structure Testing** - Validates required files exist

### 3. Full Test Suite (`pytest`)

Runs all tests in the `tests/` directory when dependencies are available.

## Running Tests Locally

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)

### Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Unix/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# If requirements.txt fails, try development version
pip install -r requirements-dev.txt
```

### Running Tests

#### Basic CI/CD Tests (No Dependencies)

```bash
python ci_test.py
```

#### Comprehensive Tests (No Dependencies)

```bash
python run_tests.py
```

#### Full Test Suite (Requires Dependencies)

```bash
python -m pytest tests/ -v
```

#### Individual Test Files

```bash
python -m pytest tests/test_core.py -v
python -m pytest tests/test_database_connection.py -v
```

## Troubleshooting

### Network/Proxy Issues

If you encounter SSL or proxy errors when installing dependencies:

1. **Use Development Requirements**:

   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Trusted Hosts**:

   ```bash
   pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org package_name
   ```

3. **Alternative Package Index**:
   ```bash
   pip install --index-url http://pypi.org/simple/ package_name
   ```

### Import Errors

Some modules may fail to import due to missing dependencies. This is expected behavior:

- **Expected Failures**: `telegram`, `sqlalchemy`, `psycopg2`, `cryptography`
- **These failures don't prevent CI/CD tests from passing**

### Test Failures

If tests fail:

1. **Check Python version** - Ensure Python 3.8+ is used
2. **Verify dependencies** - Install required packages
3. **Check file permissions** - Ensure test files are readable
4. **Review error messages** - Look for specific import or syntax issues

## CI/CD Best Practices

### 1. Test Before Commit

Always run tests locally before committing:

```bash
python ci_test.py
```

### 2. Keep Tests Fast

- CI/CD tests should complete in under 5 minutes
- Use mocks for external dependencies
- Avoid heavy operations in tests

### 3. Clear Test Output

- Use descriptive test names
- Provide clear error messages
- Use emojis and formatting for readability

### 4. Dependency Management

- Pin critical dependency versions
- Use flexible constraints for development
- Document optional dependencies

## Deployment

### Railway Deployment

The bot is configured for Railway deployment:

- **railway.json** - Railway configuration
- **Procfile** - Process definition
- **runtime.txt** - Python version specification

### Environment Variables

Required environment variables:

- `BOT_TOKEN` - Telegram bot token
- `ENVIRONMENT` - Production/development mode
- `DATABASE_URL` - Database connection string

## Monitoring and Maintenance

### Performance Monitoring

- Built-in performance monitoring in `utils/performance_monitor.py`
- Metrics collection and logging
- Background task management

### Error Handling

- Comprehensive error handling in `utils/error_handler.py`
- Sentry integration for production monitoring
- Graceful degradation for non-critical failures

## Support

For CI/CD issues:

1. Check GitHub Actions logs
2. Run local tests using `ci_test.py`
3. Review this documentation
4. Check GitHub Issues for known problems

## Future Improvements

- [ ] Add code coverage reporting
- [ ] Implement automated security scanning
- [ ] Add performance regression testing
- [ ] Implement automated dependency updates
- [ ] Add multi-platform testing (Windows, Linux, macOS)
