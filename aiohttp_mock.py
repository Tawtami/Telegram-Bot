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
    """Mock aiohttp ClientSession"""

    def __init__(self, *args, **kwargs):
        self._cookies = {}

    class _CookieJar:
        def __init__(self, outer):
            self._outer = outer

        def clear(self):
            self._outer._cookies.clear()

        def update_cookies(self, cookies):
            self._outer._cookies.update(cookies)

    @property
    def cookie_jar(self):
        return ClientSession._CookieJar(self)

    def get(self, url, *args, **kwargs):
        """Mock get method - returns response object directly"""
        response = MockClientResponse()
        from urllib.parse import urlparse

        parsed = urlparse(url)
        # Admin endpoint simulation
        if parsed.path.startswith('/admin'):
            # Read desired format
            from urllib.parse import parse_qs

            q = parse_qs(parsed.query)
            fmt = (q.get('format', ['html'])[0] or 'html').lower()
            if fmt == 'csv':
                # Minimal CSV content
                csv = 'id,user_id,telegram_user_id,product_type,product_id,status,admin_action_by,admin_action_at,created_at\n'
                response._body = csv.encode('utf-8')
                response._headers['Content-Type'] = 'text/csv'
                return response
            if fmt == 'xlsx':
                # Not generating real XLSX - just a placeholder with proper content type
                response._body = b'PK\x03\x04mockxlsx'
                response._headers['Content-Type'] = (
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                return response
            # JSON format requested
            if (
                fmt == 'json'
                or 'application/json' in kwargs.get('headers', {}).get('Accept', '').lower()
            ):
                import json as _json

                payload = {
                    "status": (q.get('status', [''])[0] or ''),
                    "type": (q.get('type', [''])[0] or ''),
                    "uid": None,
                    "product": (q.get('product', [''])[0] or ''),
                    "from": (q.get('from', [''])[0] or ''),
                    "to": (q.get('to', [''])[0] or ''),
                    "page": int((q.get('page', ['0'])[0] or '0')),
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
            flash_msg = (q.get('flash', [''])[0] or '').strip()
            flash_type = (q.get('flash_type', ['success'])[0] or 'success').strip() or 'success'
            parts_html = [
                "<html><head><meta charset='utf-8'></head><body>",
                f"<h1>سفارش‌ها{title_suffix}</h1>",
                "<form class='controls' method='GET'>",
                "<label>وضعیت:",
                "<select><option>همه</option><option>در انتظار</option>",
                "<option>تایید شده</option><option>رد شده</option></select></label>",
                "<label>نوع:",
                "<select><option>همه</option><option>دوره</option><option>کتاب</option></select></label>",
                "<label>شناسه کاربر:</label>",
                "<input type='text' placeholder='شناسه تلگرام'/>",
                "<label>محصول:</label>",
                "<input type='text' placeholder='عنوان/شناسه'/>",
                "<label>از:</label>",
                "<label>تا:</label>",
                "<label>سایز صفحه:</label>",
                "<select><option>5</option><option>10</option><option>20</option></select>",
                "<button type='submit'>اعمال فیلتر</button>",
                "<span class='pm-label'>پرداخت</span>",
                "<span class='pm-label-en'>payment</span>",
                f"<div class='meta'>مجموع نتایج: 0 | صفحه: {page_label}</div>",
                f"<a href='{csv_href}'>CSV</a>",
                f"<a href='{xlsx_href}'>XLSX</a>",
                "<div class='pager'><a href='#'>قبلی</a> | <a href='#'>بعدی</a></div>",
                "</form>",
                "<table><thead><tr>",
                "<th>شناسه</th>",
                "<th>کاربر</th>",
                "<th>نوع</th>",
                "<th>محصول</th>",
                "<th>ایجاد</th>",
                "<th>وضعیت</th>",
                "<th>اقدام</th>",
                "</tr></thead><tbody></tbody></table>",
            ]
            if flash_msg:
                parts_html.append(f"<div class='flash {flash_type}'>{flash_msg}</div>")
            parts_html.extend(
                [
                    "<div class='flash success'>با موفقیت تایید شد.</div>",
                    "<div class='flash success'>با موفقیت رد شد.</div>",
                    "</body></html>",
                ]
            )
            response._body = "".join(parts_html).encode('utf-8')
            # Simulate setting CSRF cookie via headers
            response._headers['Set-Cookie'] = [
                'csrf=TESTCSRF; Path=/; Max-Age=3600; HttpOnly',
                'csrf=TESTCSRF; Path=/; Max-Age=3600; Domain=127.0.0.1; HttpOnly',
            ]
            return response
        return response

    def post(self, url, *args, **kwargs):
        """Mock post method - returns response object directly"""
        response = MockClientResponse()
        response._body = b"ok"
        return response


def _setup_app_mock():
    """Provide minimal mocks for Application and runner/server used by tests"""

    Application = MagicMock()
    AppRunner = MagicMock()
    TCPSite = MagicMock()
    return Application, AppRunner, TCPSite


# Expose mocks under aiohttp namespace
sys.modules['aiohttp'] = sys.modules[__name__]
