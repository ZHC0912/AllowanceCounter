"""database.py — All SQLite helpers: schema init, CRUD wrappers, and business logic queries."""

import sqlite3
import hashlib
import datetime

from constants import DB_PATH


# ── Connection helpers ─────────────────────────────────────────────────────────

def db_get(query: str, params: tuple = ()) -> list:
    """Return all rows as sqlite3.Row objects."""
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        return db.execute(query, params).fetchall()


def db_one(query: str, params: tuple = ()):
    """Return first row or None."""
    rows = db_get(query, params)
    return rows[0] if rows else None


def db_run(query: str, params: tuple = ()) -> int:
    """Execute a write query and return the lastrowid."""
    with sqlite3.connect(DB_PATH) as db:
        cur = db.execute(query, params)
        return cur.lastrowid


# ── Schema ─────────────────────────────────────────────────────────────────────

def init_db() -> None:
    """Create tables and apply any migration patches."""
    with sqlite3.connect(DB_PATH) as db:
        db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS categories (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES users(id),
                name       TEXT NOT NULL,
                budget_cap REAL DEFAULT NULL,
                UNIQUE(user_id, name)
            );
            CREATE TABLE IF NOT EXISTS allowances (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                year    INTEGER NOT NULL,
                month   INTEGER NOT NULL,
                amount  REAL NOT NULL DEFAULT 0,
                UNIQUE(user_id, year, month)
            );
            CREATE TABLE IF NOT EXISTS expenses (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL REFERENCES users(id),
                category_id  INTEGER NOT NULL REFERENCES categories(id),
                amount       REAL NOT NULL,
                description  TEXT DEFAULT '',
                expense_date TEXT NOT NULL,
                is_recurring INTEGER DEFAULT 0,
                created_at   TEXT DEFAULT (datetime('now'))
            );
        ''')
        # Migration patches for older databases
        for ddl in [
            'ALTER TABLE categories ADD COLUMN budget_cap REAL DEFAULT NULL',
            'ALTER TABLE expenses   ADD COLUMN is_recurring INTEGER DEFAULT 0',
        ]:
            try:
                db.execute(ddl)
            except Exception:
                pass


# ── Auth helpers ───────────────────────────────────────────────────────────────

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def get_user_by_credentials(username: str, password: str):
    return db_one(
        'SELECT id, username FROM users WHERE username=? AND password=?',
        (username, hash_pw(password)),
    )


def create_user(username: str, password: str) -> int:
    """Insert a new user and seed default categories. Returns new user id."""
    uid = db_run(
        'INSERT INTO users (username, password) VALUES (?, ?)',
        (username, hash_pw(password)),
    )
    for cat in ['Food', 'Transport', 'Entertainment', 'Shopping', 'Health', 'Others']:
        db_run(
            'INSERT OR IGNORE INTO categories (user_id, name) VALUES (?, ?)',
            (uid, cat),
        )
    return uid


# ── Recurring expense auto-add ─────────────────────────────────────────────────

def apply_recurring_expenses(uid: int) -> None:
    """Auto-add recurring expenses for the current month if not already added."""
    today = datetime.date.today()
    ym = f'{today.year:04d}-{today.month:02d}'
    recurrings = db_get(
        'SELECT * FROM expenses WHERE user_id=? AND is_recurring=1 ORDER BY created_at DESC',
        (uid,),
    )
    seen: set = set()
    for r in recurrings:
        key = (r['category_id'], r['description'])
        if key in seen:
            continue
        seen.add(key)
        exists = db_one(
            "SELECT id FROM expenses WHERE user_id=? AND category_id=? "
            "AND description=? AND is_recurring=1 AND strftime('%Y-%m', expense_date)=?",
            (uid, r['category_id'], r['description'], ym),
        )
        if not exists:
            new_date = f"{ym}-{today.day:02d}"
            db_run(
                'INSERT INTO expenses '
                '(user_id, category_id, amount, description, expense_date, is_recurring) '
                'VALUES (?, ?, ?, ?, ?, 1)',
                (uid, r['category_id'], r['amount'], r['description'], new_date),
            )


# ── Convenience query helpers ──────────────────────────────────────────────────

def get_allowance(uid: int, year: int, month: int) -> float:
    r = db_one(
        'SELECT amount FROM allowances WHERE user_id=? AND year=? AND month=?',
        (uid, year, month),
    )
    return r['amount'] if r else 0.0


def get_monthly_spent(uid: int, year: int, month: int) -> float:
    r = db_one(
        "SELECT COALESCE(SUM(amount), 0) AS s FROM expenses "
        "WHERE user_id=? AND strftime('%Y-%m', expense_date)=?",
        (uid, f'{year:04d}-{month:02d}'),
    )
    return r['s'] if r else 0.0


def get_categories(uid: int) -> list:
    return db_get(
        'SELECT id, name, budget_cap FROM categories WHERE user_id=? ORDER BY name',
        (uid,),
    )


def get_expenses_for_month(uid: int, year: int, month: int) -> list:
    return db_get(
        "SELECT e.id, e.expense_date, c.name AS cat, e.amount, e.description, e.is_recurring "
        "FROM expenses e JOIN categories c ON c.id = e.category_id "
        "WHERE e.user_id=? AND strftime('%Y-%m', e.expense_date)=? "
        "ORDER BY e.expense_date DESC, e.created_at DESC",
        (uid, f'{year:04d}-{month:02d}'),
    )
