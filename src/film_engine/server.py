from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from src.film_engine.demo import build_demo_plan_summary
from src.film_engine.platform import JELLYFISH_FILM_WORKFLOW


class LuminAIRequestHandler(BaseHTTPRequestHandler):
    server_version = "LuminAIHTTP/1.0"

    def do_GET(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path == "/":
            self._send_json(
                200,
                {
                    "service": "LuminAI Film Engine",
                    "endpoints": ["/health", "/demo/closed-loop-plan"],
                },
            )
            return
        if path == "/health":
            self._send_json(
                200,
                {
                    "status": "ok",
                    "engine": "LuminAI",
                    "workflow": list(JELLYFISH_FILM_WORKFLOW),
                },
            )
            return
        if path == "/demo/closed-loop-plan":
            self._send_json(200, build_demo_plan_summary())
            return
        self._send_json(
            404,
            {
                "status": "not_found",
                "path": path,
            },
        )

    def log_message(self, format: str, *args: Any) -> None:
        if os.environ.get("LUMINAI_HTTP_LOG") == "1":
            super().log_message(format, *args)

    def _send_json(self, status_code: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def create_server(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), LuminAIRequestHandler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the LuminAI Film Engine server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)

    server = create_server(args.host, args.port)
    host, port = server.server_address[:2]
    print(f"LuminAI Film Engine running at http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
