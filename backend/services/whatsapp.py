"""Local-only parser and conservative action-item suggestion extractor."""

import hashlib
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from backend.services.reminders import _connect, initialize
from config.paths import runtime_file


MAX_CHAT_BYTES = 5 * 1024 * 1024
CHAT_DIR = runtime_file("data", "whatsapp")
CHAT_DIR.mkdir(parents=True, exist_ok=True)
MESSAGE_START = re.compile(
    r"^(?:\[)?(?P<date>\d{1,4}[/-]\d{1,2}[/-]\d{2,4}),?\s+(?P<time>\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)\]?(?:\s+-\s+|\s+)(?P<body>.*)$",
    re.IGNORECASE,
)
ACTION_TERMS = re.compile(r"\b(please|remind|don't forget|dont forget|i will|i'll|we will|we'll|submit|bring|finish|send|meeting|call)\b", re.I)


def parse_export(filename, content):
    if not filename.lower().endswith(".txt"):
        raise ValueError("Choose a WhatsApp .txt chat export.")
    if len(content) > MAX_CHAT_BYTES:
        raise ValueError("Chat export must be 5 MB or smaller.")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("cp1252")

    messages = []
    current = None
    for line in text.splitlines():
        match = MESSAGE_START.match(line)
        if match:
            if current:
                messages.append(current)
            body = match.group("body")
            sender, separator, message = body.partition(": ")
            if not separator:
                current = {"timestamp": None, "sender": None, "text": body}
                continue
            current = {"timestamp": _parse_timestamp(match.group("date"), match.group("time")),
                       "sender": sender[:100], "text": message}
        elif current:
            current["text"] += "\n" + line
    if current:
        messages.append(current)
    return messages


def _parse_timestamp(date_text, time_text):
    formats = ("%d/%m/%y %I:%M %p", "%d/%m/%Y %I:%M %p", "%m/%d/%y %I:%M %p",
               "%d/%m/%y %H:%M", "%d/%m/%Y %H:%M", "%m/%d/%y %H:%M",
               "%d-%m-%Y %H:%M", "%m-%d-%Y %H:%M")
    combined = f"{date_text} {time_text.strip().upper()}"
    for fmt in formats:
        try:
            return datetime.strptime(combined, fmt).isoformat()
        except ValueError:
            continue
    return None


def _suggestion(message, timezone_name="Asia/Kolkata"):
    text = message["text"].strip()
    if len(text) > 300 or not ACTION_TERMS.search(text):
        return None
    lowered = text.lower()
    deadline = None
    confidence = 0.55
    local_now = datetime.now(ZoneInfo(timezone_name))
    if "tomorrow" in lowered:
        day = local_now.date() + timedelta(days=1)
        clock = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", lowered)
        if clock:
            hour = int(clock.group(1)) % 12 + (12 if clock.group(3) == "pm" else 0)
            minute = int(clock.group(2) or 0)
            deadline = datetime.combine(day, datetime.min.time().replace(hour=hour, minute=minute), tzinfo=ZoneInfo(timezone_name)).isoformat()
        confidence = 0.86 if clock else 0.48
    elif re.search(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", lowered):
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        match = re.search(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", lowered)
        offset = (days.index(match.group(1)) - local_now.weekday()) % 7 or 7
        day = local_now.date() + timedelta(days=offset)
        clock = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", lowered)
        if clock:
            hour = int(clock.group(1)) % 12 + (12 if clock.group(3) == "pm" else 0)
            minute = int(clock.group(2) or 0)
            deadline = datetime.combine(day, datetime.min.time().replace(hour=hour, minute=minute), tzinfo=ZoneInfo(timezone_name)).isoformat()
        confidence = 0.8 if clock else 0.48
    else:
        return {"title": _title(text), "evidence": text[:300], "sender": message.get("sender"),
                "message_time": message.get("timestamp"), "deadline": None, "timezone": timezone_name,
                "confidence": 0.35, "needs_clarification": True}
    return {"title": _title(text), "evidence": text[:300], "sender": message.get("sender"),
            "message_time": message.get("timestamp"), "deadline": deadline, "timezone": timezone_name,
            "confidence": confidence, "needs_clarification": confidence < 0.75 or not deadline}


def _title(text):
    return re.sub(r"^(?:bro[, ]*|please\s+|remind me to\s*)", "", text, flags=re.I).strip().rstrip(".!?")[:180]


def analyze_export(filename, content, timezone_name="Asia/Kolkata"):
    messages = parse_export(filename, content)
    source_key = hashlib.sha256(content).hexdigest()
    suggestions = [candidate for message in messages if (candidate := _suggestion(message, timezone_name))]
    initialize()
    saved = []
    with _connect() as db:
        for suggestion in suggestions:
            suggestion_id = hashlib.sha256((source_key + suggestion["title"] + suggestion["evidence"]).encode()).hexdigest()
            db.execute("""INSERT OR IGNORE INTO whatsapp_suggestions
                (id,source_key,title,evidence,sender,message_time,deadline,timezone,confidence,needs_clarification,status,created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,'pending',?)""",
                       (suggestion_id, source_key, suggestion["title"], suggestion["evidence"], suggestion["sender"],
                        suggestion["message_time"], suggestion["deadline"], suggestion["timezone"], suggestion["confidence"],
                        int(suggestion["needs_clarification"]), datetime.now().isoformat()))
            row = db.execute("SELECT * FROM whatsapp_suggestions WHERE id=?", (suggestion_id,)).fetchone()
            saved.append(dict(row))
    return saved


def list_suggestions():
    initialize()
    with _connect() as db:
        return [dict(row) for row in db.execute("SELECT * FROM whatsapp_suggestions WHERE status='pending' ORDER BY created_at DESC")]


def update_suggestion(suggestion_id, status, title=None, deadline=None):
    initialize()
    with _connect() as db:
        row = db.execute("SELECT * FROM whatsapp_suggestions WHERE id=? AND status='pending'", (suggestion_id,)).fetchone()
        if not row:
            return None
        if status in {"approved", "rejected"}:
            db.execute("UPDATE whatsapp_suggestions SET status=? WHERE id=?", (status, suggestion_id))
        if title is not None or deadline is not None:
            db.execute("UPDATE whatsapp_suggestions SET title=?,deadline=?,needs_clarification=? WHERE id=?",
                       (title or row["title"], deadline or row["deadline"], int(not (deadline or row["deadline"])), suggestion_id))
        return dict(db.execute("SELECT * FROM whatsapp_suggestions WHERE id=?", (suggestion_id,)).fetchone())


def clear_suggestions():
    initialize()
    with _connect() as db:
        db.execute("DELETE FROM whatsapp_suggestions")
