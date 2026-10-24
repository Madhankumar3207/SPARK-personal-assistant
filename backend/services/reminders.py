"""Persistent SQLite reminder store and idempotent due-reminder polling."""

import sqlite3
import threading
from contextlib import contextmanager
import uuid
from datetime import datetime, timedelta, timezone

from config.paths import runtime_file


DB_PATH = runtime_file("data", "spark.sqlite3")
_scheduler_thread = None
_scheduler_stop = threading.Event()


@contextmanager
def _connect():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize():
    with _connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS reminders (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, scheduled_at TEXT NOT NULL,
            timezone TEXT NOT NULL, recurrence TEXT, status TEXT NOT NULL,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL, last_delivery TEXT,
            source TEXT NOT NULL DEFAULT 'manual', dedupe_key TEXT UNIQUE
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS whatsapp_suggestions (
            id TEXT PRIMARY KEY, source_key TEXT NOT NULL, title TEXT NOT NULL,
            evidence TEXT NOT NULL, sender TEXT, message_time TEXT, deadline TEXT,
            timezone TEXT, confidence REAL NOT NULL, needs_clarification INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending', created_at TEXT NOT NULL,
            UNIQUE(source_key, title, evidence)
        )""")


def list_reminders(status=None):
    initialize()
    with _connect() as db:
        query = "SELECT * FROM reminders"
        params = ()
        if status:
            query += " WHERE status=?"
            params = (status,)
        query += " ORDER BY scheduled_at"
        return [dict(row) for row in db.execute(query, params)]


def create_reminder(title, scheduled_at, timezone_name="Asia/Kolkata", recurrence=None, source="manual", dedupe_key=None):
    initialize()
    if recurrence not in {None, "daily", "weekly"}:
        raise ValueError("Only daily and weekly recurrence are supported.")
    parsed = datetime.fromisoformat(scheduled_at)
    if parsed.tzinfo is None:
        raise ValueError("scheduled_at must include a timezone offset.")
    now = datetime.now(timezone.utc).isoformat()
    reminder_id = str(uuid.uuid4())
    with _connect() as db:
        if dedupe_key:
            existing = db.execute("SELECT * FROM reminders WHERE dedupe_key=?", (dedupe_key,)).fetchone()
            if existing:
                return dict(existing), False
        db.execute("""INSERT INTO reminders
            (id,title,scheduled_at,timezone,recurrence,status,created_at,updated_at,source,dedupe_key)
            VALUES (?,?,?,?,?,'scheduled',?,?,?,?)""",
                   (reminder_id, title.strip(), parsed.astimezone(timezone.utc).isoformat(),
                    timezone_name, recurrence, now, now, source, dedupe_key))
        row = db.execute("SELECT * FROM reminders WHERE id=?", (reminder_id,)).fetchone()
        return dict(row), True


def update_reminder(reminder_id, title=None, scheduled_at=None, recurrence=None):
    initialize()
    fields, values = [], []
    if title is not None:
        fields.append("title=?"); values.append(title.strip())
    if scheduled_at is not None:
        parsed = datetime.fromisoformat(scheduled_at)
        if parsed.tzinfo is None:
            raise ValueError("scheduled_at must include a timezone offset.")
        fields.append("scheduled_at=?"); values.append(parsed.astimezone(timezone.utc).isoformat())
    if recurrence is not None:
        if recurrence not in {"daily", "weekly"}:
            raise ValueError("Only daily and weekly recurrence are supported.")
        fields.append("recurrence=?"); values.append(recurrence)
    if not fields:
        raise ValueError("Provide a title, schedule, or recurrence to update.")
    fields.extend(["updated_at=?", "status='scheduled'"])
    values.extend([datetime.now(timezone.utc).isoformat(), reminder_id])
    with _connect() as db:
        cursor = db.execute(f"UPDATE reminders SET {', '.join(fields)} WHERE id=? AND status!='cancelled'", values)
        return cursor.rowcount == 1


def cancel_reminder(reminder_id):
    initialize()
    with _connect() as db:
        return db.execute("UPDATE reminders SET status='cancelled',updated_at=? WHERE id=? AND status!='cancelled'",
                          (datetime.now(timezone.utc).isoformat(), reminder_id)).rowcount == 1


def snooze_reminder(reminder_id, minutes):
    if not 1 <= minutes <= 10080:
        raise ValueError("Snooze must be between 1 minute and 7 days.")
    new_time = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    return update_reminder(reminder_id, scheduled_at=new_time.isoformat())


def claim_due(now=None):
    initialize()
    now_iso = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
    claimed = []
    with _connect() as db:
        db.execute("BEGIN IMMEDIATE")
        rows = db.execute("SELECT * FROM reminders WHERE status='scheduled' AND scheduled_at<=?", (now_iso,)).fetchall()
        for row in rows:
            db.execute("UPDATE reminders SET status='delivered',last_delivery=?,updated_at=? WHERE id=? AND status='scheduled'",
                       (now_iso, now_iso, row['id']))
            if row['recurrence'] in {"daily", "weekly"}:
                old = datetime.fromisoformat(row['scheduled_at'])
                step = timedelta(days=1 if row['recurrence'] == "daily" else 7)
                next_time = old + step
                while next_time <= (now or datetime.now(timezone.utc)):
                    next_time += step
                next_id = str(uuid.uuid4())
                db.execute("""INSERT INTO reminders
                    (id,title,scheduled_at,timezone,recurrence,status,created_at,updated_at,source,dedupe_key)
                    VALUES (?,?,?,?,?,'scheduled',?,?,?,?)""",
                           (next_id, row['title'], next_time.isoformat(), row['timezone'], row['recurrence'],
                            row['created_at'], now_iso, row['source'], f"{row['id']}:{next_time.isoformat()}"))
            claimed.append(dict(row))
    return claimed


def start_scheduler(on_delivery):
    """Start one daemon poller per process; SQLite claims each due item once."""
    global _scheduler_thread
    initialize()
    if _scheduler_thread is not None and _scheduler_thread.is_alive():
        return
    _scheduler_stop.clear()

    def run():
        while not _scheduler_stop.wait(1):
            for item in claim_due():
                try:
                    on_delivery(item)
                except Exception:
                    continue

    _scheduler_thread = threading.Thread(target=run, name="SPARK-reminder-scheduler", daemon=True)
    _scheduler_thread.start()


def stop_scheduler():
    _scheduler_stop.set()
