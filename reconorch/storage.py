"""
Lightweight SQLite persistence for scan results.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .tools.base import ScanResult

SCHEMA = """
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool TEXT NOT NULL,
    target TEXT NOT NULL,
    started_at REAL NOT NULL,
    finished_at REAL NOT NULL,
    duration REAL NOT NULL,
    returncode INTEGER NOT NULL,
    ok INTEGER NOT NULL,
    command TEXT NOT NULL,
    stdout TEXT,
    stderr TEXT,
    parsed_json TEXT,
    error TEXT
);
CREATE INDEX IF NOT EXISTS idx_results_tool_target ON results(tool, target);
CREATE INDEX IF NOT EXISTS idx_results_started_at ON results(started_at);
"""


class ResultStore:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        with self._conn() as conn:
            conn.executescript(SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def save(self, result: ScanResult) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO results
                   (tool, target, started_at, finished_at, duration, returncode,
                    ok, command, stdout, stderr, parsed_json, error)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    result.tool, result.target, result.started_at, result.finished_at,
                    result.duration, result.returncode, int(result.ok), result.command,
                    result.stdout, result.stderr, json.dumps(result.parsed), result.error,
                ),
            )

    def latest(self, tool: str | None = None, target: str | None = None, limit: int = 50):
        query = "SELECT * FROM results WHERE 1=1"
        params: list = []
        if tool:
            query += " AND tool = ?"
            params.append(tool)
        if target:
            query += " AND target = ?"
            params.append(target)
        query += " ORDER BY started_at DESC LIMIT ?"
        params.append(limit)

        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
