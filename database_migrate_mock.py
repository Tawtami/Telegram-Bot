#!/usr/bin/env python3
"""
Mock database.migrate module for running tests without real database
"""

import sys
from unittest.mock import MagicMock


# Mock functions
def init_db():
    """Mock init_db function"""
    return True


def _upgrade_schema_if_needed():
    """Mock _upgrade_schema_if_needed function"""
    return True


def _create_tables_individually():
    """Mock _create_tables_individually function"""
    return True


# Mock constants
ENGINE = MagicMock()
Base = MagicMock()


# Add to sys.modules so imports work
sys.modules['database.migrate'] = sys.modules[__name__]
