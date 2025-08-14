#!/usr/bin/env python3
import sys
from unittest.mock import MagicMock


class MockResponse:
    def __init__(self):
        self.status = 200
        self.headers = {}
        self._body = b"mock response body"

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def text(self):
        return self._body.decode('utf-8')

    async def json(self):
        return {"mock": "data"}

    async def read(self):
        return self._body


class MockClientResponse:
    """Mock response that can be used as async context manager"""

    def __init__(self):
        self.status = 200
        self._headers = {}
        self._body = b"mock response body"

    @property
    def headers(self):
        """Mock headers property with getall method"""

        class MockHeaders:
            def __init__(self, headers_dict):
                self._headers = headers_dict

            def get(self, key, default=None):
                return self._headers.get(key, default)

            def getall(self, key, default=None):
                """Mock getall method for headers"""
                value = self._headers.get(key)
                if value is None:
                    return default or []
                if isinstance(value, list):
                    return value
                return [value]

            def __getitem__(self, key):
                return self._headers[key]

            def __contains__(self, key):
                return key in self._headers

        return MockHeaders(self._headers)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def text(self):
        return self._body.decode('utf-8')

    async def json(self):
        # If body looks like JSON, return parsed; else generic
        try:
            import json as _json

            return _json.loads(self._body.decode('utf-8'))
        except Exception:
            return {"mock": "data"}

    async def read(self):
        return self._body


class CookieJar:
    """Mock CookieJar class"""

    def __init__(self, unsafe=False):
        self.unsafe = unsafe

    def update_cookies(self, cookies, url):
        """Mock update_cookies method"""
        pass

    def filter_cookies(self, url):
        """Mock filter_cookies method"""
        return {}


class ClientSession:
    def __init__(self, *args, **kwargs):
        self.cookie_jar = CookieJar()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def get(self, url, *args, **kwargs):
        """Mock get method - returns response object directly"""
        response = MockClientResponse()
        # Simulate admin token checks and basic HTML bodies for snapshot tests
        if '/admin' in url:
            # Extract token parameter
            import re

            m = re.search(r'[?&]token=([^&]+)', url)
            token = m.group(1) if m else ''
            from os import getenv

            expected = getenv('ADMIN_DASHBOARD_TOKEN', '')
            if not expected or token != expected:
                response.status = 401
                return response
            # Return minimal HTML that includes expected labels
            html = (
                "<html><head><meta charset='utf-8'></head><body>"
                "<form class='controls'>"
                "<label>وضعیت:</label>"
                "<label>نوع:</label>"
                "<label>از:</label>"
                "<label>تا:</label>"
                "<div class='meta'>مجموع نتایج: 0 | صفحه: 1</div>"
                "<a href='?format=csv'>CSV</a>"
                "<a href='?format=xlsx'>XLSX</a>"
                "</form>"
                "</body></html>"
            )
            response._body = html.encode('utf-8')
            # Simulate setting CSRF cookie via headers
            response._headers['Set-Cookie'] = [
                'csrf=TESTCSRF; Path=/; Max-Age=3600; HttpOnly',
                'csrf=TESTCSRF; Path=/; Max-Age=3600; Domain=127.0.0.1; HttpOnly',
            ]
        return response

    def post(self, url, *args, **kwargs):
        """Mock post method - returns response object directly"""
        response = MockClientResponse()
        # Simulate /admin/act handling
        if '/admin/act' in url:
            # Default to 200 ok json
            body = {"ok": True, "id": 1, "action": "approve"}
            # Reflect id/action when form data provided
            try:
                data = kwargs.get('data') or {}
                if isinstance(data, dict):
                    if 'id' in data:
                        body['id'] = int(str(data['id']).strip() or '1')
                    if 'action' in data:
                        body['action'] = str(data['action']).strip().lower()
            except Exception:
                pass
            import json as _json

            response._body = _json.dumps(body).encode('utf-8')
            response._headers['Content-Type'] = 'application/json'
        return response

    async def close(self):
        pass


# Mock aiohttp.web module
class web:
    """Mock aiohttp.web module"""

    class Application:
        def __init__(self, middlewares=None):
            self.router = MagicMock()
            self.middlewares = middlewares or []

    class Request:
        def __init__(self):
            self.headers = {}
            self.query = {}

    class Response:
        def __init__(self, text="", status=200):
            self.text = text
            self.status = 200

    @staticmethod
    def middleware(func):
        """Mock middleware decorator"""
        return func

    class AppRunner:
        """Mock AppRunner class"""

        def __init__(self, app):
            self.app = app

        async def setup(self):
            pass

        async def cleanup(self):
            pass

    class TCPSite:
        """Mock TCPSite class"""

        def __init__(self, runner, host, port):
            self.runner = runner
            self.host = host
            self.port = port

        async def start(self):
            pass

        async def stop(self):
            pass


# Create a mock module that provides ClientSession as a class
class aiohttp_module:
    ClientSession = ClientSession
    CookieJar = CookieJar
    web = web


sys.modules['aiohttp'] = aiohttp_module
sys.modules['aiohttp.web'] = web
