"""Payment store — SQLite persistence for subscriptions, payments, invoices."""
from __future__ import annotations

import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_AUTH_DB_PATH = BASE_DIR / "data" / "auth_dev.sqlite3"


def _connect(db_path: Path = DEFAULT_AUTH_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_payment_tables(db_path: Path = DEFAULT_AUTH_DB_PATH) -> None:
    """Create payment-related tables if they don't exist. Called on startup."""
    with _connect(db_path) as conn:
        # Subscription columns on users table
        try:
            conn.execute("ALTER TABLE users ADD COLUMN subscription_tier TEXT NOT NULL DEFAULT 'free'")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN subscription_status TEXT NOT NULL DEFAULT 'active'")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN subscription_expires_at TEXT NULL")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN paypal_subscription_id TEXT NULL")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN stripe_customer_id TEXT NULL")
        except sqlite3.OperationalError:
            pass

        # Payments table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                provider_order_id TEXT NULL,
                provider_capture_id TEXT NULL,
                plan TEXT NOT NULL,
                billing_cycle TEXT NOT NULL,
                amount_usd REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'USD',
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                completed_at TEXT NULL,
                metadata TEXT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments (user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_payments_status ON payments (status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_payments_provider_order ON payments (provider_order_id)")

        # Invoices table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                payment_id TEXT NULL,
                plan TEXT NOT NULL,
                billing_cycle TEXT NOT NULL,
                amount_usd REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'USD',
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'paid',
                created_at TEXT NOT NULL,
                viettel_invoice_id TEXT NULL,
                viettel_invoice_no TEXT NULL,
                viettel_transaction_id TEXT NULL,
                viettel_status TEXT NOT NULL DEFAULT 'pending',
                buyer_name TEXT NULL,
                buyer_tax_code TEXT NULL,
                buyer_address TEXT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_invoices_user_id ON invoices (user_id)")

        # Migrate: add Viettel columns to existing invoices table
        for col, definition in [
            ("viettel_invoice_id",     "TEXT NULL"),
            ("viettel_invoice_no",     "TEXT NULL"),
            ("viettel_transaction_id", "TEXT NULL"),
            ("viettel_status",         "TEXT NOT NULL DEFAULT 'pending'"),
            ("buyer_name",             "TEXT NULL"),
            ("buyer_tax_code",         "TEXT NULL"),
            ("buyer_address",          "TEXT NULL"),
        ]:
            try:
                conn.execute(f"ALTER TABLE invoices ADD COLUMN {col} {definition}")
            except sqlite3.OperationalError:
                pass

        conn.commit()


# ── Subscription helpers ──────────────────────────────────────────────────────

def get_user_subscription(user_id: str, db_path: Path = DEFAULT_AUTH_DB_PATH) -> Dict:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT subscription_tier, subscription_status, subscription_expires_at, paypal_subscription_id FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
    if not row:
        return {"tier": "free", "status": "active", "expires_at": None}
    return {
        "tier": row["subscription_tier"] or "free",
        "status": row["subscription_status"] or "active",
        "expires_at": row["subscription_expires_at"],
        "paypal_subscription_id": row["paypal_subscription_id"],
    }


def update_user_subscription(
    user_id: str,
    tier: str,
    status: str,
    expires_at: Optional[str],
    paypal_subscription_id: Optional[str] = None,
    db_path: Path = DEFAULT_AUTH_DB_PATH,
) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """UPDATE users SET
                subscription_tier = ?,
                subscription_status = ?,
                subscription_expires_at = ?,
                paypal_subscription_id = COALESCE(?, paypal_subscription_id)
               WHERE id = ?""",
            (tier, status, expires_at, paypal_subscription_id, user_id),
        )
        conn.commit()


# ── Payment helpers ───────────────────────────────────────────────────────────

def create_payment(
    user_id: str,
    provider: str,
    plan: str,
    billing_cycle: str,
    amount_usd: float,
    provider_order_id: Optional[str] = None,
    db_path: Path = DEFAULT_AUTH_DB_PATH,
) -> str:
    payment_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            """INSERT INTO payments
               (id, user_id, provider, provider_order_id, plan, billing_cycle, amount_usd, currency, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'USD', 'pending', ?)""",
            (payment_id, user_id, provider, provider_order_id, plan, billing_cycle, amount_usd, now),
        )
        conn.commit()
    return payment_id


def complete_payment(
    payment_id: str,
    provider_order_id: str,
    provider_capture_id: str,
    db_path: Path = DEFAULT_AUTH_DB_PATH,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            """UPDATE payments SET
                status = 'completed',
                provider_order_id = ?,
                provider_capture_id = ?,
                completed_at = ?
               WHERE id = ?""",
            (provider_order_id, provider_capture_id, now, payment_id),
        )
        conn.commit()


def get_payment_by_order_id(provider_order_id: str, db_path: Path = DEFAULT_AUTH_DB_PATH) -> Optional[Dict]:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM payments WHERE provider_order_id = ?", (provider_order_id,)
        ).fetchone()
    return dict(row) if row else None


def list_payments(user_id: str, db_path: Path = DEFAULT_AUTH_DB_PATH) -> List[Dict]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM payments WHERE user_id = ? ORDER BY created_at DESC LIMIT 50",
            (user_id,)
        ).fetchall()
    return [dict(r) for r in rows]


# ── Invoice helpers ───────────────────────────────────────────────────────────

def create_invoice(
    user_id: str,
    payment_id: str,
    plan: str,
    billing_cycle: str,
    amount_usd: float,
    period_start: str,
    period_end: str,
    db_path: Path = DEFAULT_AUTH_DB_PATH,
) -> str:
    invoice_id = "INV-" + str(uuid.uuid4())[:8].upper()
    now = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            """INSERT INTO invoices
               (id, user_id, payment_id, plan, billing_cycle, amount_usd, currency, period_start, period_end, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 'USD', ?, ?, 'paid', ?)""",
            (invoice_id, user_id, payment_id, plan, billing_cycle, amount_usd, period_start, period_end, now),
        )
        conn.commit()
    return invoice_id


def list_invoices(user_id: str, db_path: Path = DEFAULT_AUTH_DB_PATH) -> List[Dict]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM invoices WHERE user_id = ? ORDER BY created_at DESC LIMIT 50",
            (user_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_invoice(invoice_id: str, db_path: Path = DEFAULT_AUTH_DB_PATH) -> Optional[Dict]:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM invoices WHERE id = ?", (invoice_id,)
        ).fetchone()
    return dict(row) if row else None


def update_invoice_viettel(
    invoice_id: str,
    viettel_invoice_id: str,
    viettel_invoice_no: str,
    viettel_transaction_id: str,
    viettel_status: str = "issued",
    db_path: Path = DEFAULT_AUTH_DB_PATH,
) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """UPDATE invoices SET
                viettel_invoice_id = ?,
                viettel_invoice_no = ?,
                viettel_transaction_id = ?,
                viettel_status = ?
               WHERE id = ?""",
            (viettel_invoice_id, viettel_invoice_no, viettel_transaction_id, viettel_status, invoice_id),
        )
        conn.commit()


def update_invoice_buyer_info(
    invoice_id: str,
    buyer_name: str,
    buyer_tax_code: str,
    buyer_address: str,
    db_path: Path = DEFAULT_AUTH_DB_PATH,
) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            "UPDATE invoices SET buyer_name=?, buyer_tax_code=?, buyer_address=? WHERE id=?",
            (buyer_name, buyer_tax_code, buyer_address, invoice_id),
        )
        conn.commit()
