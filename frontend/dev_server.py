"""Development server: serves ``public/`` and proxies ``/api`` to the backend.

Mirrors what the nginx container does, so the frontend can run without Docker:

    python3 dev_server.py                      # http://localhost:8080 -> backend on :8000
    BACKEND_URL=http://localhost:8000 PORT=8080 python3 dev_server.py
"""

import os
import urllib.error
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PUBLIC_DIRECTORY = Path(__file__).parent / "public"
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")
PORT = int(os.environ.get("PORT", "8080"))
PROXY_TIMEOUT_SECONDS = 300

RUNTIME_CONFIG = """window.APP_CONFIG = {{
    environment: "Local (dev server)",
    links: {{
        apiDocs: "{api_docs}",
        grafana: "{grafana}",
        prometheus: "{prometheus}",
        argocd: "",
        ollama: "{ollama}",
        postgres: "{postgres}",
    }},
}};
"""


class DevHandler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path.startswith("/api/"):
            self._proxy()
        elif self.path == "/config.js":
            self._serve_config()
        else:
            super().do_GET()

    def do_POST(self) -> None:
        if self.path.startswith("/api/"):
            self._proxy()
        else:
            self.send_error(405)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _serve_config(self) -> None:
        body = RUNTIME_CONFIG.format(
            api_docs="/api/docs",
            grafana=os.environ.get("LINK_GRAFANA", "http://localhost:3000"),
            prometheus=os.environ.get("LINK_PROMETHEUS", "http://localhost:9090"),
            ollama=os.environ.get("LINK_OLLAMA", "http://localhost:11434"),
            postgres=os.environ.get("LINK_POSTGRES", "localhost:5432"),
        ).encode()

        self.send_response(200)
        self.send_header("Content-Type", "application/javascript")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _proxy(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        request = urllib.request.Request(
            BACKEND_URL + self.path,
            data=self.rfile.read(length) if length else None,
            method=self.command,
            headers={"Accept": self.headers.get("Accept", "*/*")},
        )

        try:
            with urllib.request.urlopen(request, timeout=PROXY_TIMEOUT_SECONDS) as response:
                self._relay(response.status, response.headers, response.read())
        except urllib.error.HTTPError as error:
            self._relay(error.code, error.headers, error.read())
        except urllib.error.URLError as error:
            self.send_error(502, f"Backend unreachable at {BACKEND_URL}: {error.reason}")

    def _relay(self, status: int, headers, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", headers.get("Content-Type", "application/json"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    handler = partial(DevHandler, directory=str(PUBLIC_DIRECTORY))
    print(f"Frontend on http://localhost:{PORT}  (API proxied to {BACKEND_URL})")
    ThreadingHTTPServer(("0.0.0.0", PORT), handler).serve_forever()
