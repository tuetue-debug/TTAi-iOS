"""
User Authentication Module for TTAi API
Provides JWT-based authentication for end-users with SQLite persistence.
"""
from __future__ import annotations

import hashlib
import logging
import os
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, field_validator

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_AUTH_DB_PATH = BASE_DIR / "data" / "auth_dev.sqlite3"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
REFRESH_TOKEN_EXPIRATION_DAYS = 30
DEV_JWT_SECRET_FALLBACK = "ttai-user-auth-secret-key-change-in-production"
security = HTTPBearer(auto_error=False)


class UserCreate(BaseModel):
    """User registration request"""

    name: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")
        return value


class UserLogin(BaseModel):
    """User login request"""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response (without password)"""

    id: str
    name: str
    email: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    role: str = "user"


class TokenResponse(BaseModel):
    """JWT token response"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int
    user: UserResponse


class UserRepository:
    """Simple SQLite-backed user repository for the dev auth lane."""

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
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    role TEXT NOT NULL DEFAULT 'user'
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS refresh_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token_hash TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    revoked_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id)"
            )
            conn.commit()

        self._initialized = True

    def _row_to_user(self, row: sqlite3.Row | None) -> Optional[Dict[str, Any]]:
        if row is None:
            return None
        return {
            "id": str(row["id"]),
            "name": row["name"],
            "email": row["email"],
            "password_hash": row["password_hash"],
            "created_at": datetime.fromisoformat(row["created_at"]),
            "updated_at": datetime.fromisoformat(row["updated_at"]),
            "is_active": bool(row["is_active"]),
            "role": row["role"],
        }

    def create_user(self, user_data: UserCreate) -> Dict[str, Any]:
        self.init_db()
        if self.get_user_by_email(user_data.email):
            raise HTTPException(status_code=400, detail="Email already registered")

        now = datetime.utcnow().isoformat()
        password_hash = hash_password(user_data.password)

        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO users (name, email, password_hash, created_at, updated_at, is_active, role)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_data.name,
                        user_data.email.lower(),
                        password_hash,
                        now,
                        now,
                        1,
                        "user",
                    ),
                )
                conn.commit()
                user_id = cursor.lastrowid
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=400, detail="Email already registered") from exc

        user = self.get_user_by_id(str(user_id))
        if not user:
            raise HTTPException(status_code=500, detail="Failed to create user")
        return user

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        self.init_db()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE lower(email) = lower(?) LIMIT 1",
                (email,),
            ).fetchone()
        return self._row_to_user(row)

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        self.init_db()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ? LIMIT 1",
                (user_id,),
            ).fetchone()
        return self._row_to_user(row)

    def update_user_profile(
        self,
        *,
        user_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.init_db()
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        new_name = name if name is not None else user["name"]
        new_email = email.lower() if email is not None else user["email"]

        existing_email_user = self.get_user_by_email(new_email)
        if existing_email_user and existing_email_user["id"] != str(user_id):
            raise HTTPException(status_code=400, detail="Email already registered")

        updated_at = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE users
                SET name = ?, email = ?, updated_at = ?
                WHERE id = ?
                """,
                (new_name, new_email, updated_at, user_id),
            )
            conn.commit()

        refreshed = self.get_user_by_id(user_id)
        if not refreshed:
            raise HTTPException(status_code=404, detail="User not found")
        return refreshed

    def update_password(self, *, user_id: str, password_hash: str) -> Dict[str, Any]:
        self.init_db()
        updated_at = datetime.utcnow().isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE users
                SET password_hash = ?, updated_at = ?
                WHERE id = ?
                """,
                (password_hash, updated_at, user_id),
            )
            conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")

        refreshed = self.get_user_by_id(user_id)
        if not refreshed:
            raise HTTPException(status_code=404, detail="User not found")
        return refreshed

    def create_refresh_token(self, *, user_id: str) -> Dict[str, Any]:
        self.init_db()
        raw_token = secrets.token_urlsafe(48)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(days=REFRESH_TOKEN_EXPIRATION_DAYS)

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO refresh_tokens (user_id, token_hash, created_at, expires_at, revoked_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    token_hash,
                    created_at.isoformat(),
                    expires_at.isoformat(),
                    None,
                ),
            )
            conn.commit()

        return {
            "refresh_token": raw_token,
            "expires_in": REFRESH_TOKEN_EXPIRATION_DAYS * 24 * 3600,
            "expires_at": expires_at.isoformat(),
        }

    def verify_refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        self.init_db()
        token_hash = hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM refresh_tokens
                WHERE token_hash = ?
                LIMIT 1
                """,
                (token_hash,),
            ).fetchone()

        if row is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        if row["revoked_at"]:
            raise HTTPException(status_code=401, detail="Refresh token revoked")

        expires_at = datetime.fromisoformat(row["expires_at"])
        if expires_at <= datetime.utcnow():
            raise HTTPException(status_code=401, detail="Refresh token expired")

        user = self.get_user_by_id(str(row["user_id"]))
        if not user or not user["is_active"]:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    def revoke_refresh_token(self, refresh_token: str) -> bool:
        self.init_db()
        token_hash = hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()
        revoked_at = datetime.utcnow().isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE refresh_tokens
                SET revoked_at = ?
                WHERE token_hash = ? AND revoked_at IS NULL
                """,
                (revoked_at, token_hash),
            )
            conn.commit()
        return cursor.rowcount > 0

    def ensure_dev_seed_user(self) -> bool:
        self.init_db()
        environment = get_runtime_environment()
        if environment not in {"dev", "development", "local", "test"}:
            return False

        seed_toggle = (os.getenv("TTAI_AUTH_SEED_TEST_USER", "1") or "").strip().lower()
        if seed_toggle in {"0", "false", "no", "off"}:
            return False

        seed_email = os.getenv("TTAI_AUTH_SEED_EMAIL", "test@example.com")
        if self.get_user_by_email(seed_email):
            return False

        seed_name = os.getenv("TTAI_AUTH_SEED_NAME", "Test User")
        seed_password = os.getenv("TTAI_AUTH_SEED_PASSWORD", "password123")
        self.create_user(
            UserCreate(name=seed_name, email=seed_email, password=seed_password)
        )
        logger.info("Created dev auth seed user: %s", seed_email)
        return True


USER_REPOSITORY = UserRepository(
    Path(os.getenv("TTAI_AUTH_DB_PATH") or DEFAULT_AUTH_DB_PATH)
)


def get_runtime_environment() -> str:
    return (
        os.getenv("ENVIRONMENT")
        or os.getenv("ENV")
        or os.getenv("APP_ENV")
        or os.getenv("TTAI_ENV")
        or "development"
    ).strip().lower()


def get_jwt_secret() -> str:
    configured_secret = (
        os.getenv("TTAI_JWT_SECRET")
        or os.getenv("JWT_SECRET")
        or os.getenv("FASTAPI_JWT_SECRET")
        or ""
    ).strip()

    if configured_secret:
        return configured_secret

    environment = get_runtime_environment()
    if environment in {"prod", "production", "staging"}:
        raise RuntimeError(
            "JWT secret is required via TTAI_JWT_SECRET or JWT_SECRET outside development"
        )

    logger.warning(
        "JWT secret not configured; using development fallback secret. "
        "Set TTAI_JWT_SECRET or JWT_SECRET for stable non-dev deployments."
    )
    return DEV_JWT_SECRET_FALLBACK


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_user(user_data: UserCreate) -> Dict[str, Any]:
    """Create new user in persistent storage."""
    return USER_REPOSITORY.create_user(user_data)


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user with email and password."""
    user = USER_REPOSITORY.get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user


def create_access_token(user: Dict[str, Any]) -> str:
    """Create JWT access token."""
    expires_delta = timedelta(hours=JWT_EXPIRATION_HOURS)
    expire = datetime.utcnow() + expires_delta

    payload = {
        "sub": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "type": "access",
        "exp": expire,
        "iat": datetime.utcnow(),
    }

    token = jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)
    return token


def create_refresh_token(user: Dict[str, Any]) -> Dict[str, Any]:
    """Create persisted refresh token."""
    return USER_REPOSITORY.create_refresh_token(user_id=str(user["id"]))


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        token_type = payload.get("type")
        if token_type and token_type != "access":
            raise HTTPException(status_code=401, detail="Invalid access token")
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """Get current user from JWT token."""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = credentials.credentials
    payload = verify_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not found")

    user = USER_REPOSITORY.get_user_by_id(str(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not user["is_active"]:
        raise HTTPException(status_code=401, detail="User account is disabled")

    return user


def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get current active user."""
    if not current_user["is_active"]:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def init_auth_storage() -> None:
    """Initialize auth persistence and optional dev seed user."""
    USER_REPOSITORY.init_db()
    USER_REPOSITORY.ensure_dev_seed_user()


init_auth_storage()
