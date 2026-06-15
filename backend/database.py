import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "crm.db"

CONN = sqlite3.connect(DB_PATH, check_same_thread=False)
CONN.row_factory = sqlite3.Row

CREATE_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        tags TEXT,
        signup_date TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        category TEXT,
        order_date TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(customer_id) REFERENCES customers(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS segments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        criteria_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS campaigns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        segment_id INTEGER NOT NULL,
        channel TEXT NOT NULL,
        subject TEXT,
        body TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(segment_id) REFERENCES segments(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS communications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id INTEGER NOT NULL,
        customer_id INTEGER NOT NULL,
        channel TEXT NOT NULL,
        message TEXT NOT NULL,
        status TEXT NOT NULL,
        outcome TEXT,
        last_event_time TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(campaign_id) REFERENCES campaigns(id),
        FOREIGN KEY(customer_id) REFERENCES customers(id)
    )
    """
]


def init_db() -> None:
    for stmt in CREATE_STATEMENTS:
        CONN.execute(stmt)
    CONN.commit()


def now() -> str:
    return datetime.utcnow().isoformat()


def insert_customer(customer: dict) -> None:
    CONN.execute(
        "INSERT OR REPLACE INTO customers (id, name, email, phone, tags, signup_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            customer.get("id"),
            customer["name"],
            customer.get("email"),
            customer.get("phone"),
            customer.get("tags"),
            customer.get("signup_date"),
            now(),
        ),
    )
    CONN.commit()


def insert_order(order: dict) -> None:
    CONN.execute(
        "INSERT OR REPLACE INTO orders (id, customer_id, amount, category, order_date, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (
            order.get("id"),
            order["customer_id"],
            order["amount"],
            order.get("category"),
            order["order_date"],
            now(),
        ),
    )
    CONN.commit()


def query_customers() -> list[dict]:
    cursor = CONN.execute("SELECT * FROM customers ORDER BY id")
    return [dict(row) for row in cursor.fetchall()]


def query_orders() -> list[dict]:
    cursor = CONN.execute("SELECT * FROM orders ORDER BY id")
    return [dict(row) for row in cursor.fetchall()]


def get_customer_by_id(customer_id: int) -> dict | None:
    cursor = CONN.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def create_segment(name: str, criteria: dict) -> int:
    cursor = CONN.execute(
        "INSERT INTO segments (name, criteria_json, created_at) VALUES (?, ?, ?)",
        (name, json.dumps(criteria), now()),
    )
    CONN.commit()
    return cursor.lastrowid


def list_segments() -> list[dict]:
    cursor = CONN.execute("SELECT * FROM segments ORDER BY id")
    return [{**dict(row), "criteria": json.loads(row["criteria_json"])} for row in cursor.fetchall()]


def list_campaigns() -> list[dict]:
    cursor = CONN.execute("SELECT * FROM campaigns ORDER BY id DESC")
    return [dict(row) for row in cursor.fetchall()]


def get_segment_criteria(segment_id: int) -> dict | None:
    cursor = CONN.execute("SELECT criteria_json FROM segments WHERE id = ?", (segment_id,))
    row = cursor.fetchone()
    return json.loads(row["criteria_json"]) if row else None


def customer_segment_ids(criteria: dict) -> list[int]:
    query = ["SELECT c.id FROM customers c"]
    clauses = []
    params: list = []

    if criteria.get("category"):
        query.append("JOIN orders o ON o.customer_id = c.id")
        clauses.append("LOWER(o.category) = LOWER(?)")
        params.append(criteria["category"])

    if criteria.get("min_total_spend") is not None:
        query.append(
            "LEFT JOIN (SELECT customer_id, SUM(amount) AS total_spend FROM orders GROUP BY customer_id) s ON s.customer_id = c.id"
        )
        clauses.append("COALESCE(s.total_spend, 0) >= ?")
        params.append(criteria["min_total_spend"])

    if criteria.get("max_total_spend") is not None:
        if "s" not in " ".join(query):
            query.append(
                "LEFT JOIN (SELECT customer_id, SUM(amount) AS total_spend FROM orders GROUP BY customer_id) s ON s.customer_id = c.id"
            )
        clauses.append("COALESCE(s.total_spend, 0) <= ?")
        params.append(criteria["max_total_spend"])

    if criteria.get("min_last_order_days") is not None or criteria.get("max_last_order_days") is not None:
        query.append(
            "LEFT JOIN (SELECT customer_id, MAX(order_date) AS last_order_date FROM orders GROUP BY customer_id) r ON r.customer_id = c.id"
        )
        if criteria.get("min_last_order_days") is not None:
            clauses.append("julianday('now') - julianday(r.last_order_date) >= ?")
            params.append(criteria["min_last_order_days"])
        if criteria.get("max_last_order_days") is not None:
            clauses.append("julianday('now') - julianday(r.last_order_date) <= ?")
            params.append(criteria["max_last_order_days"])

    if criteria.get("tag"):
        clauses.append("LOWER(c.tags) LIKE LOWER(?)")
        params.append(f"%{criteria['tag']}%")

    if criteria.get("source"):
        clauses.append("LOWER(c.tags) LIKE LOWER(?)")
        params.append(f"%{criteria['source']}%")

    query_str = " ".join(query)
    if not clauses:
        query_str += " ORDER BY c.id"
    else:
        query_str += " WHERE " + " AND ".join(clauses) + " GROUP BY c.id ORDER BY c.id"

    cursor = CONN.execute(query_str, params)
    return [row["id"] for row in cursor.fetchall()]


def create_campaign(name: str, segment_id: int, channel: str, subject: str | None, body: str) -> int:
    cursor = CONN.execute(
        "INSERT INTO campaigns (name, segment_id, channel, subject, body, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (name, segment_id, channel, subject, body, now()),
    )
    CONN.commit()
    return cursor.lastrowid


def create_communication(campaign_id: int, customer_id: int, channel: str, message: str) -> int:
    cursor = CONN.execute(
        "INSERT INTO communications (campaign_id, customer_id, channel, message, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (campaign_id, customer_id, channel, message, "queued", now()),
    )
    CONN.commit()
    return cursor.lastrowid


def update_communication_status(communication_id: int, status: str, outcome: str | None = None) -> None:
    CONN.execute(
        "UPDATE communications SET status = ?, outcome = ?, last_event_time = ? WHERE id = ?",
        (status, outcome, now(), communication_id),
    )
    CONN.commit()


def list_communications(campaign_id: int | None = None) -> list[dict]:
    if campaign_id is None:
        cursor = CONN.execute("SELECT * FROM communications ORDER BY id DESC")
    else:
        cursor = CONN.execute("SELECT * FROM communications WHERE campaign_id = ? ORDER BY id DESC", (campaign_id,))
    return [dict(row) for row in cursor.fetchall()]


def campaign_metrics(campaign_id: int) -> dict:
    cursor = CONN.execute(
        "SELECT status, COUNT(*) AS count FROM communications WHERE campaign_id = ? GROUP BY status",
        (campaign_id,),
    )
    result = {row["status"]: row["count"] for row in cursor.fetchall()}
    cursor = CONN.execute(
        "SELECT outcome, COUNT(*) AS count FROM communications WHERE campaign_id = ? AND outcome IS NOT NULL GROUP BY outcome",
        (campaign_id,),
    )
    result.update({row["outcome"]: row["count"] for row in cursor.fetchall()})
    return result


def get_campaign(campaign_id: int) -> dict | None:
    cursor = CONN.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

init_db()
