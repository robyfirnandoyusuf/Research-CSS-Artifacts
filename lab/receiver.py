from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from datetime import datetime

LOG_FILE = "log.txt"
HOST = "0.0.0.0"
PORT = 1337


class SimpleLoggerHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        status = query_params.get("status", [""])[0]
        user_id = query_params.get("user_id", [""])[0]

        client_ip = self.client_address[0]
        user_agent = self.headers.get("User-Agent", "Unknown")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if status:
            log_entry = (
                f"[{timestamp}] "
                f"IP={client_ip} | "
                f"user_id={user_id} | "
                f"status={status} | "
                f"UA={user_agent}\n"
            )

            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_entry)

            print(log_entry.strip())

        self.send_response(200)
        self.send_header("Content-Type", "image/gif")
        self.end_headers()
        self.wfile.write(b"GIF89a")


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), SimpleLoggerHandler)
    print(f"[*] Listening on http://{HOST}:{PORT}")
    server.serve_forever()
