"""Optional local backend for Personal Assistant Agent.

Run:
    python backend/server.py
Open:
    http://localhost:8000

This server uses only Python standard library modules and SQLite.
The GitHub Pages version works without this backend by using browser LocalStorage.
"""

from __future__ import annotations

import json
import sqlite3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "assistant.db"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            duration INTEGER NOT NULL DEFAULT 60,
            importance TEXT NOT NULL DEFAULT 'medium',
            reminderMinutes INTEGER NOT NULL DEFAULT 30,
            notes TEXT DEFAULT '',
            createdAt TEXT DEFAULT CURRENT_TIMESTAMP,
            updatedAt TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return conn


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        return json.loads(raw or "{}")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/events":
            with connect() as conn:
                rows = conn.execute("SELECT * FROM events ORDER BY date, time").fetchall()
            self._json([row_to_dict(row) for row in rows])
            return
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/events":
            data = self._read_json()
            required = ["id", "title", "date", "time"]
            missing = [key for key in required if not data.get(key)]
            if missing:
                self._json({"error": f"missing fields: {', '.join(missing)}"}, status=400)
                return
            with connect() as conn:
                conn.execute(
                    """
                    INSERT INTO events (id, title, date, time, duration, importance, reminderMinutes, notes, createdAt, updatedAt)
                    VALUES (:id, :title, :date, :time, :duration, :importance, :reminderMinutes, :notes, :createdAt, :updatedAt)
                    """,
                    {
                        "id": data["id"],
                        "title": data["title"],
                        "date": data["date"],
                        "time": data["time"],
                        "duration": int(data.get("duration", 60)),
                        "importance": data.get("importance", "medium"),
                        "reminderMinutes": int(data.get("reminderMinutes", 30)),
                        "notes": data.get("notes", ""),
                        "createdAt": data.get("createdAt"),
                        "updatedAt": data.get("updatedAt"),
                    },
                )
            self._json({"ok": True}, status=201)
            return
        self._json({"error": "not found"}, status=404)

    def do_PUT(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/events/"):
            event_id = parsed.path.rsplit("/", 1)[-1]
            data = self._read_json()
            with connect() as conn:
                conn.execute(
                    """
                    UPDATE events
                    SET title=:title, date=:date, time=:time, duration=:duration,
                        importance=:importance, reminderMinutes=:reminderMinutes,
                        notes=:notes, updatedAt=:updatedAt
                    WHERE id=:id
                    """,
                    {
                        "id": event_id,
                        "title": data.get("title", "Untitled"),
                        "date": data.get("date"),
                        "time": data.get("time"),
                        "duration": int(data.get("duration", 60)),
                        "importance": data.get("importance", "medium"),
                        "reminderMinutes": int(data.get("reminderMinutes", 30)),
                        "notes": data.get("notes", ""),
                        "updatedAt": data.get("updatedAt"),
                    },
                )
            self._json({"ok": True})
            return
        self._json({"error": "not found"}, status=404)

    def do_DELETE(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/events/"):
            event_id = parsed.path.rsplit("/", 1)[-1]
            with connect() as conn:
                conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
            self._json({"ok": True})
            return
        self._json({"error": "not found"}, status=404)


if __name__ == "__main__":
    connect().close()
    server = ThreadingHTTPServer(("localhost", 8000), Handler)
    print("Personal Assistant Agent running at http://localhost:8000")
    print(f"SQLite DB: {DB_PATH}")
    server.serve_forever()
