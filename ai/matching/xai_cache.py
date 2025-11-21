"""
Lightweight SQLite caching for XAI match explanations.

Uses (talent_id, jd_id, request_hash) to reuse previously generated
explanations and avoid re-running the LangGraph pipeline when inputs
are identical.
"""

import json
import os
import sqlite3
from datetime import datetime
from hashlib import sha256
from typing import Optional, Tuple

from config.settings import get_settings

DEFAULT_CACHE_PATH = "data/xai_cache.db"


def compute_request_hash(payload: dict) -> str:
    """Create a deterministic hash of the request payload."""
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return sha256(serialized.encode("utf-8")).hexdigest()


def _get_cache_path(cache_path: Optional[str] = None) -> str:
    settings = get_settings()
    path = cache_path or getattr(settings, "XAI_CACHE_PATH", DEFAULT_CACHE_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS xai_cache (
            talent_id INTEGER NOT NULL,
            jd_id INTEGER NOT NULL,
            request_hash TEXT NOT NULL,
            response_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (talent_id, jd_id)
        )
        """
    )
    conn.commit()


def get_cached_response(
    talent_id: int,
    jd_id: int,
    request_hash: str,
    cache_path: Optional[str] = None,
) -> Optional[dict]:
    """Return cached response if request hash matches, else None."""
    path = _get_cache_path(cache_path)
    with sqlite3.connect(path) as conn:
        _ensure_table(conn)
        row = conn.execute(
            """
            SELECT response_json FROM xai_cache
            WHERE talent_id = ? AND jd_id = ? AND request_hash = ?
            """,
            (talent_id, jd_id, request_hash),
        ).fetchone()
        if not row:
            return None
        try:
            return json.loads(row[0])
        except json.JSONDecodeError:
            return None


def upsert_cached_response(
    talent_id: int,
    jd_id: int,
    request_hash: str,
    response: dict,
    cache_path: Optional[str] = None,
) -> None:
    """Insert or update cached response."""
    path = _get_cache_path(cache_path)
    now = datetime.utcnow().isoformat()
    payload = json.dumps(response, ensure_ascii=False)

    with sqlite3.connect(path) as conn:
        _ensure_table(conn)
        conn.execute(
            """
            INSERT INTO xai_cache (talent_id, jd_id, request_hash, response_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(talent_id, jd_id) DO UPDATE SET
                request_hash = excluded.request_hash,
                response_json = excluded.response_json,
                updated_at = excluded.updated_at
            """,
            (talent_id, jd_id, request_hash, payload, now, now),
        )
        conn.commit()
