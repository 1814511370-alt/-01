import http.server
import urllib.request
import urllib.parse
import json
import os
import socketserver

WEB_DIR = os.path.join(os.path.dirname(__file__), 'web')
BACKEND = 'http://localhost:5701'

API_PREFIXES = (
    '/api/', '/auth/', '/tasks/', '/envs/', '/scripts/',
    '/system/', '/users/', '/security/', '/configs/',
    '/deps/', '/sponsors/', '/logs/',
)

REGISTER_PAGE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>注册 - 呆呆面板</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
.card { background: #fff; border-radius: 12px; padding: 40px; width: 380px; box-shadow: 0 2px 12px rgba(0,0,0,.08); }
.card h1 { font-size: 22px; text-align: center; margin-bottom: 8px; }
.card .sub { text-align: center; color: #999; font-size: 14px; margin-bottom: 28px; }
.field { margin-bottom: 16px; }
.field label { display: block; font-size: 13px; color: #666; margin-bottom: 4px; }
.field input { width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; outline: none; transition: border .2s; }
.field input:focus { border-color: #409eff; }
.btn { width: 100%; padding: 10px; background: #409eff; color: #fff; border: none; border-radius: 6px; font-size: 14px; cursor: pointer; }
.btn:hover { background: #66b1ff; }
.btn:disabled { background: #a0cfff; cursor: not-allowed; }
.error { color: #f56c6c; font-size: 13px; margin-top: 8px; text-align: center; }
.success { color: #67c23a; font-size: 13px; margin-top: 8px; text-align: center; }
.link { text-align: center; margin-top: 16px; font-size: 13px; }
.link a { color: #409eff; text-decoration: none; }
.link a:hover { text-decoration: underline; }
</style>
</head>
<body>
<div class="card">
<h1>创建账号</h1>
<p class="sub">注册后即可登录呆呆面板</p>
<div class="field">
<label>用户名</label>
<input type="text" id="username" placeholder="请输入用户名" autocomplete="username">
</div>
<div class="field">
<label>密码</label>
<input type="password" id="password" placeholder="请输入密码" autocomplete="new-password">
</div>
<div class="field">
<label>确认密码</label>
<input type="password" id="confirm" placeholder="请再次输入密码" autocomplete="new-password">
</div>
<button class="btn" id="btn" onclick="register()">注册</button>
<div id="msg"></div>
<div class="link">已有账号？<a href="/login">去登录</a></div>
</div>
<script>
async function register() {
  const u = document.getElementById('username').value.trim()
  const p = document.getElementById('password').value
  const c = document.getElementById('confirm').value
  const btn = document.getElementById('btn')
  const msg = document.getElementById('msg')
  msg.className = ''
  msg.textContent = ''
  if (!u || !p) { msg.className = 'error'; msg.textContent = '请填写用户名和密码'; return }
  if (p !== c) { msg.className = 'error'; msg.textContent = '两次密码不一致'; return }
  if (p.length < 6) { msg.className = 'error'; msg.textContent = '密码至少6位'; return }
  btn.disabled = true; btn.textContent = '注册中...'
  try {
    const r = await fetch('/auth/register', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username:u,password:p}) })
    const d = await r.json()
    if (r.ok) {
      msg.className = 'success'; msg.textContent = '注册成功！即将跳转登录...'
      setTimeout(() => { window.location.href = '/login' }, 1500)
    } else {
      msg.className = 'error'; msg.textContent = d.error || '注册失败'
      btn.disabled = false; btn.textContent = '注册'
    }
  } catch(e) {
    msg.className = 'error'; msg.textContent = '网络错误'
    btn.disabled = false; btn.textContent = '注册'
  }
}
</script>
</body>
</html>'''

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

_admin_token_cache = None

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def _call_backend(self, method, path, body=None, headers=None):
        url = f"{BACKEND}/api{path}" if not path.startswith('/api/') else f"{BACKEND}{path}"
        hdrs = {'Content-Type': 'application/json'}
        if headers:
            hdrs.update(headers)
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        return urllib.request.urlopen(req, timeout=10)

    def _get_admin_token(self):
        global _admin_token_cache
        if _admin_token_cache:
            return _admin_token_cache
        resp = self._call_backend('POST', '/auth/login', {'username': 'admin', 'password': 'admin123'})
        d = json.loads(resp.read())
        _admin_token_cache = d['access_token']
        return _admin_token_cache

    def _proxy(self, method):
        path = self.path
        headers = {k: v for k, v in self.headers.items()}
        headers.pop('Host', None)
        headers.pop('Connection', None)

        body = None
        length = self.headers.get('Content-Length')
        if length:
            body = self.rfile.read(int(length))

        url = f"{BACKEND}/api{path}" if not path.startswith('/api/') else f"{BACKEND}{path}"

        try:
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            resp = urllib.request.urlopen(req, timeout=10)
            self.send_response(resp.status)
            for k, v in resp.headers.items():
                if k.lower() in ('content-length', 'content-type', 'set-cookie', 'cache-control', 'x-'):
                    self.send_header(k, v)
            self.end_headers()
            self.wfile.write(resp.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(502)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(f'{{"error":"proxy error: {e}"}}'.encode())

    def _handle_register(self, body):
        username = body.get('username', '').strip()
        password = body.get('password', '')

        if not username or not password:
            self._json({'error': '用户名和密码不能为空'}, 400)
            return
        if len(username) < 2:
            self._json({'error': '用户名至少2个字符'}, 400)
            return
        if len(password) < 6:
            self._json({'error': '密码至少6位'}, 400)
            return

        try:
            token = self._get_admin_token()
            resp = self._call_backend('POST', '/users', {'username': username, 'password': password, 'role': 'operator'},
                                       headers={'Authorization': f'Bearer {token}'})
            d = json.loads(resp.read())
            self._json({'message': '注册成功', 'user': {'username': d['data']['username'], 'role': d['data']['role']}})
        except urllib.error.HTTPError as e:
            err = json.loads(e.read())
            self._json({'error': err.get('error', '注册失败')}, e.code)
        except Exception as e:
            self._json({'error': f'注册失败: {e}'}, 500)

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def _serve_index_with_inject(self):
        path = os.path.join(WEB_DIR, 'index.html')
        if not os.path.isfile(path):
            self.send_error(404)
            return
        with open(path, 'rb') as f:
            content = f.read()
        inject = '''<div id="register-bar" style="display:none;position:fixed;bottom:0;left:0;right:0;text-align:center;z-index:999999;padding:10px;background:linear-gradient(0deg,rgba(255,255,255,.95),rgba(255,255,255,.8));border-top:1px solid #eee">
<a href="/register" style="color:#409eff;text-decoration:none;font-size:14px;font-weight:500">没有账号？立即注册</a>
</div>
<script>
(function(){
  var bar = document.getElementById('register-bar');
  function check() {
    var p = window.location.pathname;
    bar.style.display = (p === '/' || p === '/login') ? '' : 'none';
  }
  check();
  setInterval(check, 300);
  window.addEventListener('popstate', check);
})();
</script>'''
        content = content.replace(b'</body>', inject.encode() + b'</body>')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _is_api_path(self):
        return any(self.path.startswith(p) for p in API_PREFIXES)

    def _is_static(self):
        ext = os.path.splitext(self.path)[1].lower()
        return ext in ('.js', '.css', '.svg', '.png', '.jpg', '.ico', '.woff2', '.ttf', '.json')

    def log_message(self, format, *args):
        pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/register':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(REGISTER_PAGE.encode())
        elif path == '/login':
            self._serve_index_with_inject()
        elif self._is_api_path():
            self._proxy('GET')
        elif self._is_static():
            super().do_GET()
        else:
            file_path = os.path.join(WEB_DIR, path.lstrip('/'))
            if os.path.isfile(file_path):
                super().do_GET()
            else:
                self._serve_index_with_inject()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/auth/register':
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            self._handle_register(body)
        else:
            self._proxy('POST')

    def do_PUT(self):
        self._proxy('PUT')

    def do_DELETE(self):
        self._proxy('DELETE')


if __name__ == '__main__':
    port = 5700
    server = ThreadedHTTPServer(('0.0.0.0', port), ProxyHandler)
    print(f"Proxy server on :{port} -> Go backend :5701")
    server.serve_forever()