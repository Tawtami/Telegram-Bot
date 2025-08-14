#!/usr/bin/env python3
import sys
from unittest.mock import MagicMock


class URL:
    """Mock URL class"""

    def __init__(self, url_string):
        self._url = url_string

    def __str__(self):
        return self._url

    def __repr__(self):
        return f"URL('{self._url}')"

    @property
    def path(self):
        """Mock path property"""
        if '?' in self._url:
            return self._url.split('?')[0]
        return self._url

    @property
    def query(self):
        """Mock query property"""
        if '?' in self._url:
            query_part = self._url.split('?')[1]
            return dict(item.split('=') for item in query_part.split('&') if '=' in item)
        return {}


sys.modules['yarl'] = sys.modules[__name__]
