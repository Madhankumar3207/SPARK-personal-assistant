"""CLI entry point and shared, serialized SPARK command controller."""
import re
import sys
import threading
import time

from agents.brain import understand_command
from tools.router import execute_action
from tools.tool_selector import select_tool
from voice.speech import listen
from backend.services.nlp import DEFAULT_TIMEZONE, interpret, normalize_language
from backend.services.reminders import cancel_reminder, create_reminder, list_reminders, start_scheduler, update_reminder
from tools.tasks import add_task, show_tasks


voice_enabled = threading.Event()
chat_enabled = threading.Event()
stop_event = threading.Event()
command_lock = threading.RLock()
voice_thread = None
voice_callback = None

# One input mode is active from startup, matching the legacy voice-first default.
voice_enabled.set()


def normalize_command(command):
    return re.sub(r"[.!?]+$", "", str(command or "").strip()).strip()


def get_mode_state():
    return {"voice": voice_enabled.is_set(), "chat": chat_enabled.is_set()}


def process_user_command(command):
    """Run the existing command pipeline and return its response text."""
    command = normalize_command(command)
    if not command:
        return ""
    with command_lock:
        parsed = interpret(command)
        if parsed["intent"] == "ambiguous":
            return parsed["clarification"] or "Please send one request at a time."
        if parsed["intent"] == "disabled_power_control":
            return execute_action({"action": "POWER_CONTROL_DISABLED"})
        if parsed["intent"] == "remember":
            return execute_action({"action": "MEMORY", "type": "REMEMBER", **parsed["entities"]})
        if parsed["intent"] == "recall":
            return execute_action({"action": "MEMORY", "type": "RECALL", **parsed["entities"]})
        if parsed["intent"] == "create_reminder":
            if parsed.get("clarification"):
                return parsed["clarification"]
            entities = parsed["entities"]
            try:
                reminder, created = create_reminder(
                    entities["title"], entities["scheduled_at"],
                    entities["timezone"], entities.get("recurrence"),
                    dedupe_key=f"manual:{entities['title'].casefold()}:{entities['scheduled_at']}",
                )
            except (KeyError, ValueError) as error:
                return f"I couldn't create that reminder: {error}"
            status = "Reminder created: " if created else "That reminder already exists: "
            return status + reminder["title"]
        if parsed["intent"] == "list_reminders":
            reminders = list_reminders("scheduled")
            if parsed["entities"].get("date") == "today":
                from datetime import datetime
                from zoneinfo import ZoneInfo
                today = datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).date()
                reminders = [item for item in reminders if datetime.fromisoformat(item["scheduled_at"]).astimezone(ZoneInfo(DEFAULT_TIMEZONE)).date() == today]
            return "\n".join(f"{item['id'][:8]} — {item['title']} at {item['scheduled_at']} ({item['timezone']})" for item in reminders) or "You have no upcoming reminders."
        if parsed["intent"] == "list_tasks":
            return show_tasks()
        if parsed["intent"] == "create_task":
            entities = parsed["entities"]
            return add_task(entities["title"], entities["priority"])
        if parsed["intent"] == "cancel_reminder":
            query = parsed["entities"].get("query", "")
            match = next((item for item in list_reminders("scheduled") if query in item["title"].lower() or item["id"].startswith(query)), None)
            if match and cancel_reminder(match["id"]):
                return f"Cancelled reminder: {match['title']}."
            return "I couldn't find a matching reminder to cancel."
        if parsed["intent"] == "move_reminder":
            query = parsed["entities"]["query"].lower()
            matches = [item for item in list_reminders("scheduled") if query in item["title"].lower()]
            if len(matches) != 1:
                return "I found no unique matching reminder. Please include more of its title."
            from datetime import datetime
            from zoneinfo import ZoneInfo
            item = matches[0]
            zone = ZoneInfo(item["timezone"])
            scheduled = datetime.fromisoformat(item["scheduled_at"]).astimezone(zone)
            updated_time = scheduled.replace(hour=parsed["entities"]["hour"], minute=parsed["entities"]["minute"])
            update_reminder(item["id"], scheduled_at=updated_time.isoformat())
            return f"Moved {item['title']} to {updated_time.strftime('%I:%M %p')} ({item['timezone']})."
        command_for_brain = normalize_language(command)
        understood = select_tool(understand_command(command_for_brain))
        if understood.get("action") == "MODE_CONTROL":
            mode, enabled = understood.get("mode"), understood.get("enabled")
            if mode == "voice":
                voice_enabled.set() if enabled else voice_enabled.clear()
                chat_enabled.clear() if enabled else chat_enabled.set()
                if enabled:
                    start_voice_listener()
            elif mode == "chat":
                chat_enabled.set() if enabled else chat_enabled.clear()
                voice_enabled.clear() if enabled else voice_enabled.set()
                if voice_enabled.is_set():
                    start_voice_listener()
            understood["message"] = (
                f"Voice mode {'enabled' if voice_enabled.is_set() else 'disabled'}. "
                f"Chat mode {'enabled' if chat_enabled.is_set() else 'disabled'}."
                if mode == "voice" else
                f"Chat mode {'enabled' if chat_enabled.is_set() else 'disabled'}. "
                f"Voice mode {'enabled' if voice_enabled.is_set() else 'disabled'}."
            )
        response = execute_action(understood)
        if understood.get("action") == "EXIT":
            stop_event.set()
            voice_enabled.clear()
            chat_enabled.clear()
        return str(response)


def process_command(command, from_voice=False):
    command = normalize_command(command)
    if not command:
        return False
    print("SPARK:", process_user_command(command))
    return command.lower() in {"exit", "quit", "exit spark", "quit spark", "bye", "bye spark"}


def voice_loop():
    last_command, last_command_time = "", 0.0
    unavailable_reported = False
    while not stop_event.is_set():
        if not voice_enabled.is_set():
            time.sleep(0.2)
            continue
        try:
            command = listen()
        except Exception:
            command = None
        if command is None:
            if voice_callback and not unavailable_reported:
                voice_callback("", "Voice input is temporarily unavailable.")
            unavailable_reported = True
            time.sleep(1)
            continue
        unavailable_reported = False
        if not command:
            time.sleep(0.3)
            continue
        command = normalize_command(command)
        current_time = time.monotonic()
        if command == last_command and current_time - last_command_time < 2:
            continue
        last_command, last_command_time = command, current_time
        response = process_user_command(command)
        if voice_callback:
            voice_callback(command, response)
        if stop_event.is_set():
            break


def start_voice_listener(callback=None):
    global voice_thread, voice_callback
    if callback is not None:
        voice_callback = callback
    if voice_thread is None or not voice_thread.is_alive():
        voice_thread = threading.Thread(target=voice_loop, name="SPARK-voice", daemon=True)
        voice_thread.start()


def _run_cli():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("⚡ SPARK is starting...")
    print("SPARK: Voice and chat are ready.")
    start_scheduler(lambda item: print(f"SPARK reminder: {item['title']}"))
    print("\nYou: ", end="", flush=True)
    start_voice_listener()
    while not stop_event.is_set():
        try:
            command = input()
        except (EOFError, KeyboardInterrupt):
            stop_event.set()
            voice_enabled.clear()
            chat_enabled.clear()
            print()
            break
        process_command(command)
        if not stop_event.is_set():
            print("\nYou: ", end="", flush=True)


if __name__ == "__main__":
    _run_cli()
