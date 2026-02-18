# Usage:
#   export LAB_SECRET="change-this-to-a-long-random-secret"
#   python3 server.py
#

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone
from http import cookies
from html import escape
import secrets
import os
import mimetypes
import hmac
import hashlib

HOST = "0.0.0.0"
PORT = 1337

POC_FILE = "poc.html"
LOG_FILE = "log.txt"
STATIC_DIR = "."

COOKIE_NAME = "uid"
COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days

SECRET_KEY = os.environ.get("LAB_SECRET", "SUPER_SECRET").encode("utf-8")


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def make_user_id() -> str:
    return secrets.token_hex(6)


def get_cookie_uid(cookie_header: str | None) -> str | None:
    if not cookie_header:
        return None
    c = cookies.SimpleCookie()
    try:
        c.load(cookie_header)
    except Exception:
        return None
    morsel = c.get(COOKIE_NAME)
    return morsel.value if morsel else None


def build_set_cookie(uid: str, secure: bool = False) -> str:
    c = cookies.SimpleCookie()
    c[COOKIE_NAME] = uid
    c[COOKIE_NAME]["path"] = "/"
    c[COOKIE_NAME]["max-age"] = str(COOKIE_MAX_AGE)
    c[COOKIE_NAME]["samesite"] = "Lax"
    c[COOKIE_NAME]["httponly"] = True
    if secure:
        c[COOKIE_NAME]["secure"] = True
    return c.output(header="").strip()


def sign_pid(pid: str) -> str:
    return hmac.new(SECRET_KEY, pid.encode("utf-8"), hashlib.sha256).hexdigest()


def valid_pid(pid: str, sig: str) -> bool:
    if not pid or not sig:
        return False
    expected = sign_pid(pid)
    return hmac.compare_digest(expected, sig)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def _send(self, code: int, content_type: str, body: bytes, extra_headers: dict | None = None):
        try:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            if extra_headers:
                for k, v in extra_headers.items():
                    self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def serve_static(self, path: str):
        base_dir = os.path.abspath(STATIC_DIR)
        target_path = os.path.abspath(os.path.join(base_dir, path.lstrip("/")))

        if not (target_path == base_dir or target_path.startswith(base_dir + os.sep)):
            return self._send(403, "text/plain; charset=utf-8", b"Forbidden")

        if os.path.exists(target_path) and os.path.isfile(target_path):
            content_type, _ = mimetypes.guess_type(target_path)
            if not content_type:
                content_type = "application/octet-stream"

            try:
                with open(target_path, "rb") as f:
                    content = f.read()
            except Exception:
                return self._send(500, "text/plain; charset=utf-8", b"error: failed to read file")

            try:
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "public, max-age=3600")
                self.end_headers()
                self.wfile.write(content)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return

        return self._send(404, "text/plain; charset=utf-8", b"Not Found")

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        # ========================
        # /log endpoint
        # ========================
        if path == "/log":
            status = qs.get("status", [""])[0]
            user_id = qs.get("user_id", [""])[0] or "-"

            if not status:
                return self._send(400, "text/plain; charset=utf-8", b"error: missing status")

            client_ip = self.client_address[0]
            ua = self.headers.get("User-Agent", "Unknown")

            line = (
                f"[{now_iso()}] "
                f"ip={client_ip} "
                f"user_id={user_id} "
                f"status={status} "
                f"ua={ua}\n"
            )

            try:
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(line)
                print(line.strip())
                return self._send(
                    200,
                    "text/plain; charset=utf-8",
                    b"success",
                    extra_headers={"Cache-Control": "no-store", "Connection": "close"},
                )
            except Exception as e:
                print("Write error:", e)
                return self._send(500, "text/plain; charset=utf-8", b"error: failed to write log")

        # ========================
        # Main PoC page: / or /poc
        # Supports signed PID override:
        #   /?pid=A01&sig=<hmac>
        # ========================
        if path == "/" or path == "/poc":
            pid = qs.get("pid", [""])[0]
            sig = qs.get("sig", [""])[0]

            cookie_uid = get_cookie_uid(self.headers.get("Cookie"))

            user_id = None
            set_cookie_header = None

            if pid and sig and valid_pid(pid, sig):
                user_id = pid
                set_cookie_header = build_set_cookie(user_id, secure=False)
            elif cookie_uid:
                user_id = cookie_uid
            else:
                user_id = make_user_id()
                set_cookie_header = build_set_cookie(user_id, secure=False)

            if not os.path.exists(POC_FILE):
                return self._send(500, "text/plain; charset=utf-8", b"poc.html not found")

            try:
                with open(POC_FILE, "r", encoding="utf-8") as f:
                    html = f.read()
            except Exception:
                return self._send(500, "text/plain; charset=utf-8", b"error: failed to read poc.html")

            html = html.replace("{{USER_ID}}", escape(user_id))

            headers = {"Cache-Control": "no-store"}
            if set_cookie_header:
                headers["Set-Cookie"] = set_cookie_header

            return self._send(200, "text/html; charset=utf-8", html.encode("utf-8"), headers)

        
        return self.serve_static(path)


if __name__ == "__main__":
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"[*] Server running at http://{HOST}:{PORT}")
    print(f"[*] Open: http://127.0.0.1:{PORT}/  (or /poc)")
    print("[*] Optional: signed participant links: /?pid=A01&sig=<hmac>")
    httpd.serve_forever()
