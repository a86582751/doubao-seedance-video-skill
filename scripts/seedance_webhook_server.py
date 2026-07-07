#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class WebhookHandler(BaseHTTPRequestHandler):
    db_path: Path = Path("seedance_webhook.sqlite3")

    def do_POST(self) -> None:
        if self.path.rstrip("/") != "/webhook/callback":
            self.send_error(404, "Not found")
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            self.send_error(400, "Invalid JSON")
            return
        task_id = str(data.get("id") or "")
        status = str(data.get("status") or "")
        model = str(data.get("model") or "")
        if not task_id:
            self.send_error(400, "Missing id")
            return
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS callbacks (
                    task_id TEXT PRIMARY KEY,
                    model TEXT,
                    status TEXT,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO callbacks(task_id, model, status, payload, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (task_id, model, status, json.dumps(data, ensure_ascii=False), datetime.now().isoformat(timespec="seconds")),
            )
        body = json.dumps({"ok": True, "task_id": task_id, "status": status}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        print(f"[{datetime.now().isoformat(timespec='seconds')}] {self.address_string()} {format % args}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Minimal local Seedance webhook receiver.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--db", type=Path, default=Path("seedance_webhook.sqlite3"))
    args = parser.parse_args()
    WebhookHandler.db_path = args.db
    server = ThreadingHTTPServer((args.host, args.port), WebhookHandler)
    print(f"Listening on http://{args.host}:{args.port}/webhook/callback")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
