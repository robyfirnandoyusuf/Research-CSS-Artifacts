from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone
import secrets
import os
import mimetypes

HOST = "0.0.0.0"
PORT = 1337
POC_FILE = "poc.html"
LOG_FILE = "log.txt"
STATIC_DIR = "."

def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def make_user_id():
    return secrets.token_hex(6)

class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, content_type: str, body: bytes):
        try:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        except BrokenPipeError:
            pass
        except ConnectionResetError:
            pass

    def serve_static(self, path):
        base_dir = os.path.abspath(STATIC_DIR)

        target_path = os.path.abspath(os.path.join(base_dir, path.lstrip("/")))

        if not (target_path == base_dir or target_path.startswith(base_dir + os.sep)):
            return self._send(403, "text/plain; charset=utf-8", b"Forbidden")

        if os.path.exists(target_path) and os.path.isfile(target_path):
            content_type, _ = mimetypes.guess_type(target_path)
            if not content_type:
                content_type = "application/octet-stream"

            with open(target_path, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            self.wfile.write(content)
            try:
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
        # Main PoC page
        # ========================
        if path == "/" or path == "/poc":
            user_id = make_user_id()

            if not os.path.exists(POC_FILE):
                return self._send(500, "text/plain", b"poc.html not found")

            with open(POC_FILE, "r", encoding="utf-8") as f:
                html = f.read()

            html = html.replace("{{USER_ID}}", user_id)

            return self._send(200, "text/html; charset=utf-8", html.encode("utf-8"))

        # ========================
        # Logging endpoint
        # ========================
        if path == "/log":
            status = qs.get("status", [""])[0]
            user_id = qs.get("user_id", [""])[0]

            client_ip = self.client_address[0]
            ua = self.headers.get("User-Agent", "Unknown")

            if not status:
                return self._send(
                    400,
                    "text/plain; charset=utf-8",
                    b"error: missing status"
                )

            if not user_id:
                user_id = "-"

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
                    b"success"
                )

            except Exception as e:
                print("Write error:", e)

                return self._send(
                    500,
                    "text/plain; charset=utf-8",
                    b"error: failed to write log"
                )



        # ========================
        # Static file handler
        # ========================
        return self.serve_static(path)

if __name__ == "__main__":
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"[*] Server running at http://{HOST}:{PORT}")
    print(f"[*] Open: http://127.0.0.1:{PORT}/  (or /poc)")
    httpd.serve_forever()