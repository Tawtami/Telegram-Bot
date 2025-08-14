#!/usr/bin/env python3
"""
Mock Sentry SDK module for running tests without sentry-sdk

This provides the basic Sentry functionality that our test files need
to run without the actual sentry-sdk package.
"""

import sys
from unittest.mock import MagicMock


# Mock Sentry functions
def init(*args, **kwargs):
    """Mock sentry_sdk.init function"""
    pass


def capture_exception(*args, **kwargs):
    """Mock sentry_sdk.capture_exception function"""
    pass


def capture_message(*args, **kwargs):
    """Mock sentry_sdk.capture_message function"""
    pass


def set_tag(*args, **kwargs):
    """Mock sentry_sdk.set_tag function"""
    pass


def set_user(*args, **kwargs):
    """Mock sentry_sdk.set_user function"""
    pass


def set_context(*args, **kwargs):
    """Mock sentry_sdk.set_context function"""
    pass


# Add to sys.modules so imports work
sys.modules['sentry_sdk'] = sys.modules[__name__]
