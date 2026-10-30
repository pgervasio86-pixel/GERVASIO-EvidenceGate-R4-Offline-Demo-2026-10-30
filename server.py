"""Zero-dependency local web server and JSON API."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .engine import InputError, verify
from .nebius import ModelError, advise, enabled

DOCS = Path(__file__).resolve().parent.parent / "docs"
FILES = {"/": ("index.html", "text/html; charset=utf-8"),
         "/index.html": ("index.html", "text/html; charset=utf-8"),
         "/app.js": ("app.js", "text/javascript; charset=utf-8"),
         "/styles.css": ("styles.css", "text/css; charset=utf-8")}
MAX_BYTES = 160000


class Handler(BaseHTTPRequestHandler):
    server_version = "EvidenceGate/1.0"

    def _json(self, status: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/api/status":
            return self._json(200, {"project": "GERVASIO 5.0 EvidenceGate",
                                    "api": "ok", "live_enabled": enabled(),
                                    "model": "NVIDIA Nemotron via Nebius Token Factory",
                                    "mode": "opt-in"})
        if path not in FILES:
            return self._json(404, {"error": "Not found"})
        name, mimetype = FILES[path]
        data = (DOCS / name).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if urlsplit(self.path).path != "/api/verify":
            return self._json(404, {"error": "Not found"})
        raw_length = self.headers.get("Content-Length", "")
        try:
            length = int(raw_length)
        except ValueError:
            return self._json(411, {"error": "Content-Length required"})
        if not (1 <= length <= MAX_BYTES):
            return self._json(413, {"error": "Payload size outside allowed limits"})
        try:
            payload = json.loads(self.rfile.read(length))
            report = verify(payload)
            if payload.get("use_nemotron") is True:
                # The checkbox is a separate explicit end-user action.
                report["nemotron"] = advise(report)
            else:
                report["nemotron"] = {"status": "not_requested"}
            return self._json(200, report)
        except (InputError, json.JSONDecodeError) as exc:
            return self._json(400, {"error": str(exc)})
        except ModelError as exc:
            return self._json(503, {"error": str(exc)})
        except (TypeError, AttributeError):
            return self._json(400, {"error": "Invalid payload"})


def main() -> None:
    host = os.environ.get("EVIDENCEGATE_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    print(f"GERVASIO EvidenceGate: http://{host}:{port}", flush=True)
    with ThreadingHTTPServer((host, port), Handler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
