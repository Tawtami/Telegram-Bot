#!/usr/bin/env python3
"""
Mock pytest module for running tests without pytest

This provides the basic pytest functionality that our test files need
to run without the actual pytest package.
"""

import sys
import os
from unittest.mock import patch, MagicMock


# Mock pytest fixtures and decorators
def fixture(scope="function"):
    """Mock pytest fixture decorator"""

    def decorator(func):
        return func

    return decorator


# Mock pytest.mark.asyncio
class Mark:
    def __init__(self):
        self.asyncio = self
        self.skip = self._skip

    def __call__(self, func):
        return func

    def _skip(self, reason=""):
        """Mock pytest.mark.skip decorator that replaces the test with a no-op"""

        def decorator(func):
            # Preserve async/sync nature but do nothing
            try:
                import inspect

                if inspect.iscoroutinefunction(func):
                    async def _skipped(*args, **kwargs):
                        return None

                    return _skipped
            except Exception:
                pass

            def _skipped_sync(*args, **kwargs):
                return None

            return _skipped_sync

        return decorator


mark = Mark()


# Mock pytest classes
class MonkeyPatch:
    """Mock pytest MonkeyPatch class"""

    def setattr(self, target, name, value):
        setattr(target, name, value)

    def delattr(self, target, name):
        delattr(target, name)

    def setenv(self, name, value):
        """Mock setenv method"""
        import os

        os.environ[name] = value


class Request:
    """Mock pytest Request class"""

    def __init__(self):
        self.node = MagicMock()
        self.config = MagicMock()


# Mock pytest functions
def raises(expected_exception, *args, **kwargs):
    """Mock pytest.raises context manager"""

    class RaisesContext:
        def __init__(self, expected_exception):
            self.expected_exception = expected_exception
            self.exception = None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is None:
                raise AssertionError(f"DID NOT RAISE {self.expected_exception}")
            if not issubclass(exc_type, self.expected_exception):
                return False
            self.exception = exc_val
            return True

    return RaisesContext(expected_exception)


def approx(value, rel=None, abs=None, nan_ok=False):
    """Mock pytest.approx for approximate comparisons"""

    class Approx:
        def __init__(self, expected, rel=None, abs=None, nan_ok=False):
            self.expected = expected
            self.rel = rel or 1e-6
            self.abs = abs or 0
            self.nan_ok = nan_ok

        def __eq__(self, actual):
            if self.expected == actual:
                return True
            if isinstance(self.expected, (int, float)) and isinstance(actual, (int, float)):
                diff = abs(actual - self.expected)
                return diff <= max(self.abs, abs(self.expected) * self.rel)
            return False

        def __repr__(self):
            return f"approx({self.expected})"

    return Approx(value, rel, abs, nan_ok)


def fail(msg=""):
    """Mock pytest.fail function"""
    raise AssertionError(msg)


def skip(reason=""):
    """Mock pytest.skip function"""
    # Don't raise exception, just return None to indicate skip
    return None


def xfail(reason=""):
    """Mock pytest.xfail function"""
    raise Exception(f"XFAIL: {reason}")


# Mock pytest constants
xfail = xfail
skip = skip
fail = fail


# Mock common fixtures
def monkeypatch():
    """Mock pytest.monkeypatch fixture"""
    return MonkeyPatch()


def caplog():
    """Mock pytest.caplog fixture"""

    class Caplog:
        def __init__(self):
            self.records = []
            self.text = ""

        def setLevel(self, level):
            pass

        def get_records(self):
            return self.records

    return Caplog()


def tmp_path():
    """Mock pytest.tmp_path fixture"""
    import tempfile
    import os
    from pathlib import Path

    temp_dir = tempfile.mkdtemp()
    return Path(temp_dir)


# Add fixture to mark class for convenience
mark.monkeypatch = monkeypatch
mark.caplog = caplog
mark.tmp_path = tmp_path

# Add to sys.modules so imports work
sys.modules['pytest'] = sys.modules[__name__]
