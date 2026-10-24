"""Small deterministic intent/entity parser shared by SPARK entry points."""

import re
import os
from difflib import SequenceMatcher
from difflib import get_close_matches
from dataclasses import asdict, dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


DEFAULT_TIMEZONE = os.environ.get("SPARK_TIMEZONE", "Asia/Kolkata")
ALIASES = {
    "en pending tasks enna": "show my pending tasks",
    "naalaikku": "tomorrow",
    "naalaiku": "tomorrow",
    "naalai": "tomorrow",
    "evening": "evening",
    "manikku": "at",
    "remind pannu": "remind me",
    "panna remind pannu": "to remind me",
    "mark": "mark",
    "ah change pannu": "change",
}

# Only control vocabulary is eligible for fuzzy correction. Entity text (names,
# quoted text, paths, URLs and filenames) is deliberately left untouched.
COMMAND_WORDS = set("""
hello hi hey how are you what can do tell my name who am i find search for open
latest newest recent resume calculator chrome notepad vscode explorer excel show
pending tasks task complete finish first second third remind me tomorrow today
yesterday at from this week photos photo images image videos video audio music pdf
files file mark marks update change set increase all remember recall memory
calculate analyse analyze pattern
clear delete cancel move system network time date please bro thanks help
assignment submit panna pannu naalaiku naalaikku naalai evening morning afternoon
""".split())
COMMAND_WORDS.update({"madhankumar"})


def _correct_command_words(text):
    """Fix obvious misspellings only when a token resembles known control text."""
    corrected = []
    vocabulary = sorted(COMMAND_WORDS)
    for index, token in enumerate(text.split()):
        if not token.isalpha() or len(token) < 3:
            corrected.append(token)
            continue
        # Resolve the shared near-spelling only from its command context:
        # "calculate" is exact arithmetic vocabulary, while "open calculater"
        # is a request to launch Calculator.
        if token == "calculater" and index > 0 and corrected[-1] in {"open", "launch"}:
            corrected.append("calculator")
            continue
        squeezed = re.sub(r"(.)\1+", r"\1", token)
        if squeezed in COMMAND_WORDS:
            corrected.append(squeezed)
            continue
        if len(squeezed) >= 4:
            choices = get_close_matches(squeezed, vocabulary, n=2, cutoff=0.84)
            if choices and (len(choices) == 1 or _similarity(squeezed, choices[0]) - _similarity(squeezed, choices[1]) >= 0.08):
                corrected.append(choices[0])
                continue
        corrected.append(token)
    return " ".join(corrected)


def _similarity(left, right):
    from difflib import SequenceMatcher
    return SequenceMatcher(None, left, right).ratio()


@dataclass
class Intent:
    intent: str
    entities: dict
    confidence: float
    requires_confirmation: bool = False
    clarification: str | None = None


def normalize_language(text):
    raw = (text or "").strip()
    normalized = re.sub(r"[,.!?]+", " ", raw.lower())
    normalized = " ".join(normalized.split())
    # Avoid applying typo edits to literal paths, URLs, quoted content, or
    # extension-bearing names. Routing can still inspect the unchanged text.
    protected = bool(re.search(r"(?:[A-Za-z]:[\\/]|https?://|\"[^\"]*\"|'[^']*'|\b[\w-]+\.[A-Za-z0-9]{2,6}\b)", raw))
    if protected:
        return raw
    else:
        # Preserve user-provided values after name-setting phrases.
        name_value = re.match(r"^(my name is|i am|call me)\s+(.+)$", normalized)
        if name_value:
            normalized = _correct_command_words(name_value.group(1)) + " " + name_value.group(2)
        else:
            normalized = _correct_command_words(normalized)
    normalized = re.sub(r"^(?:hello|hi|hey)\s+bro$", lambda match: match.group(0).split()[0], normalized)
    normalized = re.sub(r"^bro\s+(?=(?:find|search|show|open|what|who|remind|add|create)\b)", "", normalized)
    if normalized == "bro":
        normalized = "hello"
    # Correct the question word only in a short identity-question shape. This
    # avoids interpreting arbitrary text as a memory lookup.
    identity_shape = re.fullmatch(r"([a-z]+)\s+(?:i am|am i)", normalized)
    if identity_shape:
        question_word = get_close_matches(identity_shape.group(1), ("who", "what"), n=1, cutoff=0.8)
        if question_word:
            normalized = "what is my name"
    if normalized in {"who am i", "who i am", "tell me who i am", "tell me my name", "tell me what my name is", "what is my name please"}:
        normalized = "what is my name"
    selection = re.match(r"^(?:open\s+)?(?:the\s+)?(first|second|third|fourth|fifth)(?:\s+(?:one|result))?$", normalized)
    if selection:
        return "open " + selection.group(1)
    if normalized.startswith("hello spark ") and "how are you" in normalized:
        return "how are you"
    find_open = re.match(r"^(find\s+(?:my\s+)?[\w .-]+\s+and\s+open)(?:\s+it)?$", normalized)
    if find_open:
        return find_open.group(1)
    mark_change = re.match(r"^(.+?)\s+mark\s+(\d+(?:\.\d+)?)\s*-?\s*ah\s+change pannu$", normalized)
    if mark_change:
        return f"change {mark_change.group(1)} mark to {mark_change.group(2)}"
    if normalized in {"hello spark how are you", "hello spark, how are you"}:
        return "how are you"
    tanglish = re.match(r"^(?:bro\s+)?(?:naalaiku|naalaikku|naalai)\s+(?:(morning|evening|afternoon)\s+)?(?:(\d{1,2})(?::(\d{2}))?\s+manikku\s+)?(.+?)\s+panna\s+remind pannu$", normalized)
    if tanglish:
        period, hour, minute, title = tanglish.groups()
        title = title.strip()
        if hour:
            if period == "evening" or period == "afternoon":
                suffix = "pm"
            elif period == "morning":
                suffix = "am"
            else:
                suffix = ""
            clock = f"{hour}:{minute or '00'} {suffix}".strip()
            return f"remind me tomorrow at {clock} to {title}"
        return f"remind me tomorrow to {title}"
    for alias, english in sorted(ALIASES.items(), key=lambda item: -len(item[0])):
        normalized = re.sub(rf"\b{re.escape(alias)}\b", english, normalized)
    return normalized


def interpret(text, now=None, timezone=DEFAULT_TIMEZONE):
    """Return structured intent metadata without executing an action."""
    original = " ".join((text or "").strip().split())
    normalized = normalize_language(original)
    local_now = now or datetime.now(ZoneInfo(timezone))

    if not normalized:
        return asdict(Intent("unknown", {}, 0.0, clarification="Please enter a request."))
    if _is_power_control(original, normalized):
        return asdict(Intent("disabled_power_control", {}, 1.0))
    if _has_multiple_actions(original.lower()):
        return asdict(Intent("ambiguous", {}, 0.35, True, "I found more than one requested action. Please send one request at a time."))
    remember_match = re.match(r"^(?:my name is|i am|call me)\s+(.+)$", original, re.I)
    if remember_match:
        return asdict(Intent("remember", {"key": "name", "value": remember_match.group(1).strip().rstrip(".!?")}, 0.98))
    if normalized in {"what is my name", "who am i", "who i am"}:
        return asdict(Intent("recall", {"key": "name"}, 0.98))
    memory_match = re.match(r"^(?:what is|what's|tell me|do you remember) my (.+)$", normalized)
    if memory_match:
        return asdict(Intent("recall", {"key": memory_match.group(1).strip()}, 0.92))
    task_match = re.match(r"^(?:add|create)\s+(?:a\s+)?(?:(low|normal|high)[- ]priority\s+)?task\s+(?:to\s+)?(.+)$", normalized)
    if task_match:
        return asdict(Intent("create_task", {"title": task_match.group(2).strip(" ."), "priority": task_match.group(1) or "normal"}, 0.95))
    if normalized.startswith("cancel my ") and "reminder" in normalized:
        return asdict(Intent("cancel_reminder", {"query": normalized[10:].replace("reminder", "").strip()}, 0.75, True))
    if re.search(r"\breminders?\b", normalized) and re.search(r"\b(show|what|list)\b", normalized):
        return asdict(Intent("list_reminders", {"date": "today" if "today" in normalized else None}, 0.95))
    move_match = re.match(r"^move my (.+?) reminder to (\d{1,2})(?::(\d{2}))?\s*(am|pm)$", normalized)
    if move_match:
        hour = int(move_match.group(2))
        if not 1 <= hour <= 12:
            return asdict(Intent("unknown", {}, 0.2, True, "What time should I use?"))
        hour = hour % 12 + (12 if move_match.group(4) == "pm" else 0)
        return asdict(Intent("move_reminder", {"query": move_match.group(1), "hour": hour, "minute": int(move_match.group(3) or 0)}, 0.84, True))
    if re.search(r"\b(remind me|reminder)\b", normalized):
        return asdict(_parse_reminder(normalized, local_now, timezone))
    if normalized in {"show my pending tasks", "show pending tasks", "what are my pending tasks", "en pending tasks enna"}:
        return asdict(Intent("list_tasks", {}, 0.98))
    if normalized in {"how are you", "hello spark how are you", "hello spark", "hello", "hi", "hey", "what can you do", "help", "thanks", "thank you", "good morning", "good afternoon", "good evening"}:
        return asdict(Intent("conversation", {"text": original}, 0.99))
    if re.search(r"\b(resume|photos?|videos?|audio|pdf|files?)\b", normalized):
        return asdict(Intent("existing_file_command", {"text": original}, 0.9))
    if re.search(r"\b(mark|marks)\b", normalized):
        return asdict(Intent("existing_excel_command", {"text": original}, 0.9))
    return asdict(Intent("existing_or_unknown", {"text": original}, 0.55))


def _parse_reminder(text, now, timezone):
    title_match = re.search(r"\bto\s+(.+)$", text)
    title = title_match.group(1).strip(" .") if title_match else ""
    recurrence = "weekly" if re.search(r"every\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)|weekly", text) else (
        "daily" if re.search(r"every\s+day|daily", text) else None
    )
    weekday = re.search(r"every\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", text)
    time_match = re.search(r"\b(?:at\s*)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", text)
    if not time_match and "evening" in text:
        time_hour, time_minute = 17, 0
    elif time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        if hour < 1 or hour > 12 or minute > 59:
            return Intent("create_reminder", {"title": title}, 0.2, True, "What time should I set the reminder for?")
        time_hour = hour % 12 + (12 if time_match.group(3) == "pm" else 0)
        time_minute = minute
    else:
        return Intent("create_reminder", {"title": title}, 0.4, True, "What time should I remind you?")

    scheduled_date = now.date()
    if "tomorrow" in text:
        scheduled_date += timedelta(days=1)
    elif "today" not in text and not recurrence:
        return Intent("create_reminder", {"title": title}, 0.5, True, "What day should I set the reminder for?")

    if weekday:
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        offset = (days.index(weekday.group(1)) - scheduled_date.weekday()) % 7
        scheduled_date += timedelta(days=offset or 7)

    zone = ZoneInfo(timezone)
    scheduled = datetime.combine(scheduled_date, time(time_hour, time_minute), tzinfo=zone)
    if scheduled <= now and not recurrence and "today" in text:
        return Intent("create_reminder", {"title": title}, 0.5, True, "That time has passed today. What future date should I use?")
    entities = {
        "title": title,
        "scheduled_at": scheduled.isoformat(),
        "timezone": timezone,
        "recurrence": recurrence,
    }
    confidence = 0.92 if title and ("today" in text or "tomorrow" in text or recurrence) else 0.72
    return Intent("create_reminder", entities, confidence, False)


def _is_power_control(original, normalized):
    """Conservatively route direct device-power requests to the disabled action."""
    text = re.sub(r"[,.!?]+", " ", (original or "").lower())
    text = " ".join(text.split())
    verbs = r"(?:shut\s*down|shutdown|restart|reboot|lock|sleep|hibernate|sign\s*out|log\s*out|power\s*off)"
    device = r"(?:my\s+)?(?:computer|pc|laptop|device|system|windows)"
    direct = re.match(rf"^({verbs})(?:\s+{device})?(?:\s+(?:now|please))?$", text)
    paired = re.search(rf"\b{verbs}\b.*\b{device}\b|\bturn\s+(?:off\s+{device}|{device}\s+off)\b|\bput\s+{device}\s+(?:to\s+)?sleep\b|\b(?:sign|log)\s+me\s+out\b", text)
    if direct or paired:
        return True

    # Typo-tolerant matching is limited to a direct power verb at the start
    # of a request and requires either a device target or a standalone verb.
    parts = text.split()
    if not parts:
        return False
    protected_verbs = ("shutdown", "restart", "reboot", "lock", "sleep", "hibernate")
    closest = max(protected_verbs, key=lambda verb: SequenceMatcher(None, parts[0], verb).ratio())
    if SequenceMatcher(None, parts[0], closest).ratio() < 0.82:
        return False
    remainder = " ".join(parts[1:])
    return not remainder or bool(re.match(rf"^{device}(?:\s|$)", remainder))


def _has_multiple_actions(text):
    text = re.sub(r"[.!?]+$", "", text.strip())
    if re.match(r"^(?:find|search for|search)\b.+\band\s+open(?:\s+it)?$", text):
        return False
    if re.match(r"^open\s+chrome\s+and\s+search\b", text):
        return False
    action = r"\b(?:find|search(?:\s+for)?|show|open|add|create|remember|update|change|delete|remove|calculate|check|finish|complete|tell me|what is)\b"
    actions = list(re.finditer(action, text))
    if len(actions) < 2:
        return False
    connectors = r"(?:\b(?:and|then|also)\b|;|\n)"
    for first, second in zip(actions, actions[1:]):
        if re.search(connectors, text[first.end():second.start()]):
            return True
    return False
