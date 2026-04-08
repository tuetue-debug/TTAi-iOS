"""API key persistence helpers for TTAi FastAPI."""
from __future__ import annotations

import hashlib
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from user_auth import USER_REPOSITORY

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_API_KEYS_DB_PATH = BASE_DIR / "data" / "auth_dev.sqlite3"
API_KEY_PREFIX = "sk-ttai-"


class APIKeyRepository:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialized = False

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        if self._initialized:
            return

        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    key_prefix TEXT NOT NULL,
                    key_hash TEXT NOT NULL UNIQUE,
                    scopes_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_used_at TEXT,
                    revoked_at TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(key_prefix)"
            )
            conn.commit()

        self._initialized = True

    def _row_to_api_key(self, row: sqlite3.Row | None) -> Optional[Dict[str, Any]]:
        if row is None:
            return None
        import json

        return {
            "id": f"key_{row['id']}",
            "user_id": str(row["user_id"]),
            "name": row["name"],
            "key_prefix": row["key_prefix"],
            "scopes": json.loads(row["scopes_json"] or "[]"),
            "created_at": row["created_at"],
            "last_used_at": row["last_used_at"],
            "revoked_at": row["revoked_at"],
            "is_active": bool(row["is_active"]),
        }

    def list_user_api_keys(self, user_id: str) -> List[Dict[str, Any]]:
        self.init_db()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM api_keys
                WHERE user_id = ?
                ORDER BY id DESC
                """,
                (user_id,),
            ).fetchall()
        return [self._row_to_api_key(row) for row in rows if row is not None]

    def create_api_key(self, *, user_id: str, name: str, scopes: List[str]) -> Dict[str, Any]:
        self.init_db()
        import json

        raw_secret = f"{API_KEY_PREFIX}{secrets.token_urlsafe(24)}"
        key_hash = hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()
        key_prefix = raw_secret[:16]
        created_at = datetime.utcnow().isoformat()

        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO api_keys (user_id, name, key_prefix, key_hash, scopes_json, created_at, last_used_at, revoked_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    name,
                    key_prefix,
                    key_hash,
                    json.dumps(scopes or []),
                    created_at,
                    None,
                    None,
                    1,
                ),
            )
            conn.commit()
            api_key_id = cursor.lastrowid

        stored = self.get_api_key_by_numeric_id(api_key_id)
        if not stored:
            raise HTTPException(status_code=500, detail="Failed to create API key")

        return {
            **stored,
            "key": raw_secret,
        }

    def get_api_key_by_numeric_id(self, api_key_id: int) -> Optional[Dict[str, Any]]:
        self.init_db()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM api_keys WHERE id = ? LIMIT 1",
                (api_key_id,),
            ).fetchone()
        return self._row_to_api_key(row)

    def revoke_api_key(self, *, user_id: str, api_key_id: str) -> Dict[str, Any]:
        self.init_db()
        numeric_id = self._parse_api_key_id(api_key_id)
        revoked_at = datetime.utcnow().isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE api_keys
                SET is_active = 0, revoked_at = ?
                WHERE id = ? AND user_id = ? AND is_active = 1
                """,
                (revoked_at, numeric_id, user_id),
            )
            conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="API key not found")

        stored = self.get_api_key_by_numeric_id(numeric_id)
        if not stored:
            raise HTTPException(status_code=404, detail="API key not found")
        return stored

    def authenticate_api_key(self, raw_api_key: str) -> Dict[str, Any]:
        self.init_db()
        token_hash = hashlib.sha256(raw_api_key.encode("utf-8")).hexdigest()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM api_keys
                WHERE key_hash = ? AND is_active = 1 AND revoked_at IS NULL
                LIMIT 1
                """,
                (token_hash,),
            ).fetchone()
            if row is None:
                raise HTTPException(status_code=401, detail="Invalid API key")

            now = datetime.utcnow().isoformat()
            conn.execute(
                "UPDATE api_keys SET last_used_at = ? WHERE id = ?",
                (now, row["id"]),
            )
            conn.commit()

        api_key = self._row_to_api_key(row)
        if not api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")

        user = USER_REPOSITORY.get_user_by_id(str(api_key["user_id"]))
        if not user or not user["is_active"]:
            raise HTTPException(status_code=401, detail="User not found")

        return {
            "user": user,
            "api_key": api_key,
        }

    @staticmethod
    def _parse_api_key_id(api_key_id: str) -> int:
        value = str(api_key_id)
        if value.startswith("key_"):
            value = value[4:]
        if not value.isdigit():
            raise HTTPException(status_code=400, detail="Invalid API key id")
        return int(value)


API_KEY_REPOSITORY = APIKeyRepository(DEFAULT_API_KEYS_DB_PATH)
API_KEY_REPOSITORY.init_db()
