"""SQLite persistence for orders."""

import json
import logging
import sqlite3
from pathlib import Path

from app.models import NormalizedOrder

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent.parent / "orders.db"

_conn: sqlite3.Connection | None = None


def init_db() -> None:
    """Create the database and tables if they don't exist."""
    global _conn
    _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    _conn.execute("PRAGMA journal_mode=WAL")
    _conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id              TEXT NOT NULL,
            confirmation_number TEXT NOT NULL,
            order_date          TEXT NOT NULL,
            customer_name       TEXT NOT NULL,
            phone_number        TEXT,
            ready_time          TEXT,
            order_items_raw     TEXT,
            subtotal            TEXT,
            tax                 TEXT,
            total               TEXT,
            status              TEXT,
            restaurant_name     TEXT,
            restaurant_phone    TEXT,
            restaurant_address  TEXT,
            order_type          TEXT,
            items_json          TEXT,
            created_at          TEXT DEFAULT (datetime('now'))
        )
    """)
    _conn.commit()
    logger.info("SQLite database ready at %s", DB_PATH)


def save_order(order: NormalizedOrder) -> int:
    """Insert an order into the database. Returns the row id."""
    if _conn is None:
        raise RuntimeError("Database not initialized — call init_db() first")

    items_json = json.dumps([item.model_dump() for item in order.items])

    cursor = _conn.execute(
        """
        INSERT INTO orders (
            job_id, confirmation_number, order_date, customer_name,
            phone_number, ready_time, order_items_raw, subtotal, tax, total,
            status, restaurant_name, restaurant_phone, restaurant_address,
            order_type, items_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            order.job_id,
            order.confirmation_number,
            order.order_date,
            order.customer_name,
            order.phone_number,
            order.ready_time,
            order.order_items_raw,
            order.subtotal,
            order.tax,
            order.total,
            order.status,
            order.restaurant_name,
            order.restaurant_phone,
            order.restaurant_address,
            order.order_type,
            items_json,
        ),
    )
    _conn.commit()
    row_id = cursor.lastrowid
    logger.info("Order saved — row_id=%s, confirmation=%s", row_id, order.confirmation_number)
    return row_id
