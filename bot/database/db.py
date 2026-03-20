import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "khata.db")

# Sentinel value used as to_user when a transaction is against the group itself
GROUP_SENTINEL = 0


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS groups (
            group_id INTEGER PRIMARY KEY,
            usdt_price_inr REAL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id INTEGER NOT NULL,
            username TEXT,
            first_name TEXT,
            group_id INTEGER NOT NULL,
            UNIQUE(telegram_user_id, group_id),
            FOREIGN KEY (group_id) REFERENCES groups(group_id)
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            from_user INTEGER NOT NULL,
            to_user INTEGER NOT NULL,
            amount_inr REAL NOT NULL,
            amount_usdt REAL NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('debit', 'credit', 'settle')),
            note TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (group_id) REFERENCES groups(group_id)
        );

        CREATE INDEX IF NOT EXISTS idx_txn_group ON transactions(group_id);
        CREATE INDEX IF NOT EXISTS idx_txn_users ON transactions(from_user, to_user);
        CREATE INDEX IF NOT EXISTS idx_users_group ON users(group_id);
    """)
    conn.commit()
    conn.close()


# --- Group operations ---

def ensure_group(group_id: int):
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO groups (group_id) VALUES (?)",
        (group_id,),
    )
    conn.commit()
    conn.close()


def set_price(group_id: int, price: float):
    conn = get_connection()
    ensure_group(group_id)
    conn.execute(
        "UPDATE groups SET usdt_price_inr = ? WHERE group_id = ?",
        (price, group_id),
    )
    conn.commit()
    conn.close()


def get_price(group_id: int) -> float:
    conn = get_connection()
    ensure_group(group_id)
    row = conn.execute(
        "SELECT usdt_price_inr FROM groups WHERE group_id = ?",
        (group_id,),
    ).fetchone()
    conn.close()
    return row["usdt_price_inr"] if row else 0


# --- User operations ---

def add_user(group_id: int, telegram_user_id: int, username: str, first_name: str) -> bool:
    conn = get_connection()
    ensure_group(group_id)
    try:
        conn.execute(
            "INSERT INTO users (telegram_user_id, username, first_name, group_id) VALUES (?, ?, ?, ?)",
            (telegram_user_id, username, first_name, group_id),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def remove_user(group_id: int, telegram_user_id: int) -> bool:
    conn = get_connection()
    rows = conn.execute(
        "DELETE FROM users WHERE telegram_user_id = ? AND group_id = ?",
        (telegram_user_id, group_id),
    ).rowcount
    conn.commit()
    conn.close()
    return rows > 0


def get_user(group_id: int, telegram_user_id: int, username: str = None):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE telegram_user_id = ? AND group_id = ?",
        (telegram_user_id, group_id),
    ).fetchone()

    # Fallback: match by username for users added via @mention (stored with id=0)
    if not row and username:
        row = conn.execute(
            "SELECT * FROM users WHERE LOWER(username) = LOWER(?) AND group_id = ?",
            (username, group_id),
        ).fetchone()
        # Auto-correct the stored telegram_user_id so future lookups work by ID
        if row and telegram_user_id:
            conn.execute(
                "UPDATE users SET telegram_user_id = ? WHERE id = ?",
                (telegram_user_id, row["id"]),
            )
            conn.commit()

    conn.close()
    return row


def get_user_by_username(group_id: int, username: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE LOWER(username) = LOWER(?) AND group_id = ?",
        (username, group_id),
    ).fetchone()
    conn.close()
    return row


def get_all_users(group_id: int):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM users WHERE group_id = ? ORDER BY username",
        (group_id,),
    ).fetchall()
    conn.close()
    return rows


# --- Transaction operations ---

def add_transaction(group_id: int, from_user: int, to_user: int,
                    amount_inr: float, amount_usdt: float, txn_type: str, note: str):
    conn = get_connection()
    conn.execute(
        """INSERT INTO transactions (group_id, from_user, to_user, amount_inr, amount_usdt, type, note)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (group_id, from_user, to_user, amount_inr, amount_usdt, txn_type, note),
    )
    conn.commit()
    conn.close()


def get_balance(group_id: int, user_a: int, user_b: int) -> dict:
    """Get balance between user_a and user_b.
    Returns total given by A to B, total received by A from B, and net balance."""
    conn = get_connection()

    # Total A gave to B (debits from A to B)
    row = conn.execute(
        """SELECT COALESCE(SUM(amount_inr), 0) as total_inr
           FROM transactions
           WHERE group_id = ? AND from_user = ? AND to_user = ? AND type = 'debit'""",
        (group_id, user_a, user_b),
    ).fetchone()
    gave_inr = row["total_inr"]

    # Total A received from B (credits from A where to_user is B)
    row = conn.execute(
        """SELECT COALESCE(SUM(amount_inr), 0) as total_inr
           FROM transactions
           WHERE group_id = ? AND from_user = ? AND to_user = ? AND type = 'credit'""",
        (group_id, user_a, user_b),
    ).fetchone()
    received_inr = row["total_inr"]

    # Settlements
    row = conn.execute(
        """SELECT COALESCE(SUM(amount_inr), 0) as total_inr
           FROM transactions
           WHERE group_id = ? AND from_user = ? AND to_user = ? AND type = 'settle'""",
        (group_id, user_a, user_b),
    ).fetchone()
    settled_inr = row["total_inr"]

    net_inr = gave_inr - received_inr - settled_inr

    conn.close()
    return {
        "gave_inr": round(gave_inr, 2),
        "received_inr": round(received_inr, 2),
        "net_inr": round(net_inr, 2),
    }


def get_net_balance_inr(group_id: int, user_a: int, user_b: int) -> float:
    """Net amount user_b owes user_a. Positive = B owes A."""
    bal = get_balance(group_id, user_a, user_b)
    return bal["net_inr"]


def get_transactions(group_id: int, user_a: int, user_b: int,
                     limit: int = 10, offset: int = 0):
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM transactions
           WHERE group_id = ? AND from_user = ? AND to_user = ?
           ORDER BY created_at DESC
           LIMIT ? OFFSET ?""",
        (group_id, user_a, user_b, limit, offset),
    ).fetchall()
    conn.close()
    return rows


def count_transactions(group_id: int, user_a: int, user_b: int) -> int:
    conn = get_connection()
    row = conn.execute(
        """SELECT COUNT(*) as cnt FROM transactions
           WHERE group_id = ? AND from_user = ? AND to_user = ?""",
        (group_id, user_a, user_b),
    ).fetchone()
    conn.close()
    return row["cnt"]


def get_all_transactions_for_export(group_id: int, user_a: int = None, user_b: int = None):
    """
    Fetch transactions joined with usernames for CSV export.
    If user_a and user_b given: only between those two users.
    If only group_id given: all group transactions.
    """
    conn = get_connection()
    if user_a is not None and user_b is not None:
        rows = conn.execute(
            """SELECT t.id, t.created_at, t.type,
                      fu.username AS from_username,
                      tu.username AS to_username,
                      t.amount_inr, t.amount_usdt, t.note
               FROM transactions t
               LEFT JOIN users fu ON fu.telegram_user_id = t.from_user AND fu.group_id = t.group_id
               LEFT JOIN users tu ON tu.telegram_user_id = t.to_user   AND tu.group_id = t.group_id
               WHERE t.group_id = ? AND t.from_user = ? AND t.to_user = ?
               ORDER BY t.created_at DESC""",
            (group_id, user_a, user_b),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT t.id, t.created_at, t.type,
                      fu.username AS from_username,
                      tu.username AS to_username,
                      t.amount_inr, t.amount_usdt, t.note
               FROM transactions t
               LEFT JOIN users fu ON fu.telegram_user_id = t.from_user AND fu.group_id = t.group_id
               LEFT JOIN users tu ON tu.telegram_user_id = t.to_user   AND tu.group_id = t.group_id
               WHERE t.group_id = ?
               ORDER BY t.created_at DESC""",
            (group_id,),
        ).fetchall()
    conn.close()
    return rows
