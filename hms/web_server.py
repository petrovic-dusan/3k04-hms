from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional
from hms.config import WEB_ADDRESS

PAGE = Path(__file__).parent / "web" / "index.html"


class WebServer:
    def __init__(self, address: tuple[str, int] =WEB_ADDRESS ) -> None:
        self._lock = threading.Lock()
        self._snapshot: Optional[dict[str, Any]] = None
        self._updated_at = 0.0
        self._httpd = ThreadingHTTPServer(address, self._handler())
        self._httpd.daemon_threads = True
        threading.Thread(target=self._httpd.serve_forever, daemon=True).start()

    def update(self, snapshot: dict[str, Any]) -> None:
        with self._lock:
            self._snapshot = snapshot
            self._updated_at = time.monotonic()

    def payload(self) -> tuple[int, dict[str, Any]]:
        with self._lock:
            if self._snapshot is None:
                return 503, {"error": "No data yet."}
            return 200, {**self._snapshot, "age": time.monotonic() - self._updated_at, "error": None}

    def stop(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()

    def _handler(self):
        server = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                path = self.path.split("?", 1)[0]
                if path in ("/", "/index.html"):
                    self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
                elif path == "/api/snapshot":
                    code, body = server.payload()
                    self._send(code, json.dumps(body).encode(), "application/json")
                else:
                    self._send(404, b"Not found.", "text/plain")

            def _send(self, code: int, body: bytes, content_type: str) -> None:
                self.send_response(code)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args) -> None:
                pass

        return Handler
