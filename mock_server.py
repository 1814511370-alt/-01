import http.server
import json
import os
import urllib.parse
import socketserver

WEB_DIR = os.path.join(os.path.dirname(__file__), 'web')

MOCK_TOKEN = "eyJhbGciOiJIUzI1NiJ9.mock"
MOCK_REFRESH = "eyJhbGciOiJIUzI1NiJ9.mock-refresh"

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

class MockHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Connection', 'keep-alive')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def send_error(self, code, message=None, explain=None):
        if code == 404:
            self._json({"error": "not found"}, 404)
        else:
            self._json({"error": message or "error"}, code)

    def log_message(self, format, *args):
        pass

    def do_OPTIONS(self):
        self._json({})

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        length = int(self.headers.get('Content-Length', 0))
        body = {}
        if length:
            try:
                body = json.loads(self.rfile.read(length))
            except:
                body = {}

        if path in ('/auth/login', '/api/auth/login'):
            self._json({
                "data": {
                    "access_token": MOCK_TOKEN,
                    "refresh_token": MOCK_REFRESH,
                    "token_type": "Bearer",
                    "expires_in": 1728000
                }
            })
        elif path in ('/auth/init', '/api/auth/init'):
            self._json({
                "data": {
                    "access_token": MOCK_TOKEN,
                    "refresh_token": MOCK_REFRESH,
                    "token_type": "Bearer",
                    "expires_in": 1728000
                }
            })
        elif path in ('/auth/logout', '/api/auth/logout'):
            self._json({"message": "ok"})
        elif path in ('/api/auth/refresh', '/auth/refresh'):
            self._json({
                "data": {
                    "access_token": MOCK_TOKEN,
                    "refresh_token": MOCK_REFRESH,
                }
            })
        else:
            self._json({"message": "ok", "data": {}})

    def do_PUT(self):
        self._json({"message": "ok", "data": {}})

    def do_DELETE(self):
        self._json({"message": "ok"})

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        auth_routes = {
            '/auth/check-init': {"data": {"initialized": True}},
            '/auth/captcha-config': {"data": {"enabled": False}},
            '/auth/user': {
                "data": {
                    "id": 1, "username": "admin", "role": "admin",
                    "avatar": "", "created_at": "2026-01-01T00:00:00",
                    "last_login": "2026-06-24T08:00:00"
                }
            },
        }

        if path in auth_routes:
            self._json(auth_routes[path])
            return

        api_routes = {
            '/api/system/dashboard': {
                "data": {
                    "today_completed": 12, "today_failed": 1,
                    "total_tasks": 8, "total_scripts": 15, "total_envs": 24,
                    "system_load": "0.5", "memory_used": "45%",
                    "disk_used": "32%", "uptime": "3d 12h",
                    "recent_logs": [
                        {"id": 1, "task_name": "签到任务", "status": 0,
                         "started_at": "2026-06-24T08:00:00", "duration": 2.5},
                        {"id": 2, "task_name": "md定时保活-电信", "status": 0,
                         "started_at": "2026-06-24T07:00:00", "duration": 1.8},
                        {"id": 3, "task_name": "md定时保活-联通", "status": 2,
                         "started_at": "2026-06-24T06:00:00", "duration": 0},
                    ]
                }
            },
            '/api/system/info': {
                "data": {
                    "version": "v2.1.0", "go_version": "go1.22",
                    "build_time": "2026-03-10T00:00:00Z",
                    "panel_name": "呆呆面板"
                }
            },
            '/api/system/stats': {
                "data": {
                    "cpu_percent": 12.5, "memory_percent": 45.2,
                    "disk_percent": 32.1, "uptime_seconds": 302400,
                    "process_count": 28
                }
            },
            '/api/tasks': {
                "data": [
                    {"id": 1, "name": "签到任务", "command": "task sign.py",
                     "status": 0, "cron": "0 8 * * *", "enabled": True},
                    {"id": 2, "name": "md定时保活-电信", "command": "task md_keepalive_dx.py",
                     "status": 0, "cron": "0 */6 * * *", "enabled": True},
                    {"id": 3, "name": "md定时保活-联通", "command": "task md_keepalive_lt.py",
                     "status": 2, "cron": "30 */6 * * *", "enabled": True},
                    {"id": 4, "name": "环境检测", "command": "task check_env.py",
                     "status": 0, "cron": "0 0 * * 0", "enabled": False},
                ], "total": 4
            },
            '/api/envs': {
                "data": [
                    {"id": 1, "name": "DX_KEEPALIVE_URL", "value": "****",
                     "remarks": "电信保活地址"},
                    {"id": 2, "name": "DX_KEEPALIVE_COOKIE", "value": "****",
                     "remarks": "电信保活Cookie"},
                    {"id": 3, "name": "LT_KEEPALIVE_URL", "value": "****",
                     "remarks": "联通保活地址"},
                    {"id": 4, "name": "LT_KEEPALIVE_COOKIE", "value": "****",
                     "remarks": "联通保活Cookie"},
                    {"id": 5, "name": "TZ", "value": "Asia/Shanghai",
                     "remarks": "时区"},
                ], "total": 5
            },
            '/api/scripts': {
                "data": [
                    {"path": "sign.py", "size": 2048,
                     "modified": "2026-06-20T10:00:00"},
                    {"path": "md_keepalive_dx.py", "size": 4096,
                     "modified": "2026-06-19T08:00:00"},
                    {"path": "md_keepalive_lt.py", "size": 4096,
                     "modified": "2026-06-19T08:00:00"},
                    {"path": "check_env.py", "size": 1024,
                     "modified": "2026-06-18T12:00:00"},
                ], "total": 4
            },
            '/api/users': {
                "data": [
                    {"id": 1, "username": "admin", "role": "admin",
                     "created_at": "2026-01-01T00:00:00",
                     "last_login": "2026-06-24T08:00:00"}
                ], "total": 1
            },
            '/api/security/login-logs': {
                "data": [
                    {"id": 1, "username": "admin", "ip": "127.0.0.1",
                     "status": "success",
                     "created_at": "2026-06-24T08:00:00"}
                ], "total": 1
            },
            '/api/system/public-version': {"data": {"version": "v2.1.0"}},
            '/api/system/version': {
                "data": {"version": "v2.1.0", "commit": "abc1234",
                         "build_time": "2026-03-10T00:00:00Z"}
            },
            '/api/system/check-update': {"data": {"has_update": False}},
            '/api/system/health-check': {"data": {"status": "healthy", "uptime": "3d 12h"}},
            '/api/security/2fa/status': {"data": {"enabled": False}},
            '/api/system/panel-settings': {"data": {}},
        }

        if path in api_routes:
            self._json(api_routes[path])
            return

        if path.startswith('/api/scripts/content'):
            self._json({
                "data": {
                    "path": "sign.py",
                    "content": '#!/usr/bin/env python3\nprint("hello world")\n',
                    "binary": False, "is_binary": False
                }
            })
            return

        if path.startswith('/api/'):
            self._json({"data": {}, "total": 0})
            return

        super().do_GET()


if __name__ == '__main__':
    port = 5700
    server = ThreadedHTTPServer(('0.0.0.0', port), MockHandler)
    server.timeout = 0.5
    print(f"Mock server running on http://0.0.0.0:{port}")
    server.serve_forever()