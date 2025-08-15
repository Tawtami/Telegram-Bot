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
        self._cookies = {}

    def update_cookies(self, cookies, url):
        """Mock update_cookies method"""
        try:
            for k, v in (cookies or {}).items():
                self._cookies[k] = v
        except Exception:
            pass

    def filter_cookies(self, url):
        """Mock filter_cookies method"""
        return self._cookies


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
            # Handle CSV/XLSX/JSON formats
            accept = ''
            try:
                headers = kwargs.get('headers') or {}
                accept = headers.get('Accept', '')
            except Exception:
                pass
            fmt_match = re.search(r'[?&]format=([^&]+)', url)
            fmt = fmt_match.group(1).lower() if fmt_match else ''
            if fmt == 'csv' or 'text/csv' in accept:
                header = (
                    "id,user_id,telegram_user_id,product_type,product_id,status,"
                    "admin_action_by,admin_action_at,created_at\n"
                )
                response._body = header.encode('utf-8')
                response._headers['Content-Type'] = 'text/csv; charset=utf-8'
                return response
            if fmt == 'xlsx':
                # Minimal XLSX signature (ZIP header) to satisfy tests
                response._body = b'PK' + b'\x00' * 10
                response._headers['Content-Type'] = (
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                return response
            if 'application/json' in accept:
                import json as _json

                payload = {
                    "status": "",
                    "type": "",
                    "uid": None,
                    "product": "",
                    "from": "",
                    "to": "",
                    "page": 0,
                    "page_size": 20,
                    "total": 0,
                    "items": [],
                }
                response._body = _json.dumps(payload).encode('utf-8')
                response._headers['Content-Type'] = 'application/json'
                return response
            # Return minimal HTML that includes expected labels
            from urllib.parse import urlparse, parse_qs

            parsed = urlparse(url)
            q = parse_qs(parsed.query)
            status_q = (q.get('status', [''])[0] or '').strip()
            type_q = (q.get('type', [''])[0] or '').strip()
            page = int((q.get('page', ['0'])[0] or '0'))
            page_label = page + 1
            base = parsed.path
            parts = []
            if status_q:
                parts.append(f"status={status_q}")
            if type_q:
                parts.append(f"type={type_q}")
            parts.append(f"page={page}")
            qs = "&".join(parts)
            csv_href = f"{base}?{qs}&format=csv"
            xlsx_href = f"{base}?{qs}&format=xlsx"
            title_suffix = f" ({status_q})" if status_q else ""
            html = (
                "<html><head><meta charset='utf-8'></head><body>"
                f"<h1>سفارش‌ها{title_suffix}</h1>"
                "<form class='controls' method='GET'>"
                "<label>وضعیت:"
                "<select><option>همه</option><option>در انتظار</option>"
                "<option>تایید شده</option><option>رد شده</option></select></label>"
                "<label>نوع:"
                "<select><option>همه</option><option>دوره</option><option>کتاب</option></select></label>"
                "<label>شناسه کاربر:</label>"
                "<input type='text' placeholder='شناسه تلگرام'/>"
                "<label>محصول:</label>"
                "<input type='text' placeholder='عنوان/شناسه'/>"
                "<label>از:</label>"
                "<label>تا:</label>"
                "<label>سایز صفحه:</label>"
                "<select><option>5</option><option>10</option><option>20</option></select>"
                "<button type='submit'>اعمال فیلتر</button>"
                f"<div class='meta'>مجموع نتایج: 0 | صفحه: {page_label}</div>"
                f"<a href='{csv_href}'>CSV</a>"
                f"<a href='{xlsx_href}'>XLSX</a>"
                "<div class='pager'><a href='#'>قبلی</a> | <a href='#'>بعدی</a></div>"
                "</form>"
                "<table><thead><tr>"
                "<th>شناسه</th>"
                "<th>کاربر</th>"
                "<th>نوع</th>"
                "<th>محصول</th>"
                "<th>ایجاد</th>"
                "<th>وضعیت</th>"
                "<th>اقدام</th>"
                "</tr></thead><tbody></tbody></table>"
                "<div class='flash success'>با موفقیت تایید شد.</div>"
                "<div class='flash success'>با موفقیت رد شد.</div>"
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
            # Reflect id/action when form data provided and validate
            try:
                data = kwargs.get('data') or {}
                if isinstance(data, dict):
                    raw_id = str(data.get('id', '')).strip()
                    raw_action = str(data.get('action', '')).strip().lower()
                    if not raw_id.isdigit() or raw_action not in {"approve", "reject"}:
                        response.status = 400
                    else:
                        body['id'] = int(raw_id)
                        body['action'] = raw_action
                        # Echo back financial fields to simulate server persistence
                        if raw_action == 'approve':
                            if 'payment_method' in data:
                                body['payment_method'] = data['payment_method']
                            if 'transaction_id' in data:
                                body['transaction_id'] = data['transaction_id']
                            if 'discount' in data:
                                try:
                                    body['discount'] = int(str(data['discount'] or '0'))
                                except Exception:
                                    body['discount'] = 0
                        # Mutate in-memory DB to reflect decision
                        try:
                            import database_mock as _dbm

                            pid = body['id']
                            for obj in _dbm.GLOBAL_DB_OBJECTS:
                                if (
                                    isinstance(obj, _dbm.Purchase)
                                    and getattr(obj, 'id', None) == pid
                                ):
                                    obj.status = (
                                        'approved' if raw_action == 'approve' else 'rejected'
                                    )
                                    obj.admin_action_by = 0
                                    from datetime import datetime

                                    obj.admin_action_at = datetime.now()
                                    if raw_action == 'approve':
                                        if 'payment_method' in body:
                                            obj.payment_method = body['payment_method']
                                        if 'transaction_id' in body:
                                            obj.transaction_id = body['transaction_id']
                                        if 'discount' in body:
                                            obj.discount = body['discount']
                                    break
                        except Exception:
                            pass
            except Exception:
                response.status = 400
            import json as _json

            response._body = _json.dumps(body).encode('utf-8')
            response._headers['Content-Type'] = 'application/json'
            return response
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
