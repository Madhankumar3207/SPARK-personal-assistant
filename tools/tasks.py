"""Persistent, local task management for SPARK."""

import json
from pathlib import Path


TASK_FILE = Path(__file__).resolve().parent.parent / "data" / "tasks.json"


def _load_tasks():
    try:
        with TASK_FILE.open("r", encoding="utf-8") as file:
            tasks = json.load(file)
        return tasks if isinstance(tasks, list) else []
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def _save_tasks(tasks):
    try:
        TASK_FILE.parent.mkdir(parents=True, exist_ok=True)
        with TASK_FILE.open("w", encoding="utf-8") as file:
            json.dump(tasks, file, indent=2, ensure_ascii=False)
        return True
    except OSError:
        return False


def _pending(tasks):
    return [task for task in tasks if not task.get("completed", False)]


def _display_task(text):
    text = text.strip()
    return text[:1].upper() + text[1:]


def add_task(text):
    if not text or not text.strip():
        return "Please tell me what task you want me to add."
    tasks = _load_tasks()
    next_id = max((task.get("id", 0) for task in tasks), default=0) + 1
    task_text = _display_task(text)
    tasks.append({"id": next_id, "task": task_text, "completed": False})
    if not _save_tasks(tasks):
        return "I couldn't save that task."
    return f"Task added: {task_text}. ⚡"


def show_tasks():
    tasks = _pending(_load_tasks())
    if not tasks:
        return "You have no pending tasks. ⚡"
    lines = ["My Tasks:", ""]
    lines.extend(f"{number}. {task['task']}" for number, task in enumerate(tasks, 1))
    return "\n".join(lines)


def _task_at_pending_number(number):
    if not isinstance(number, int) or number < 1:
        return None, None
    tasks = _load_tasks()
    pending = _pending(tasks)
    return tasks, pending[number - 1] if number <= len(pending) else None


def complete_task(number):
    if not isinstance(number, int):
        return "Please provide a valid task number."
    tasks, task = _task_at_pending_number(number)
    if task is None:
        return f"I couldn't find task {number}."
    task["completed"] = True
    if not _save_tasks(tasks):
        return "I couldn't save that task update."
    return f"Task {number} completed: {task['task']}. ⚡"


def remove_task(number):
    if not isinstance(number, int):
        return "Please provide a valid task number."
    tasks, task = _task_at_pending_number(number)
    if task is None:
        return f"I couldn't find task {number}."
    tasks.remove(task)
    if not _save_tasks(tasks):
        return "I couldn't save that task update."
    return f"Task {number} removed. ⚡"


def clear_completed_tasks():
    tasks = _load_tasks()
    if not _save_tasks(_pending(tasks)):
        return "I couldn't clear completed tasks."
    return "Completed tasks cleared. ⚡"


def clear_all_tasks():
    if not _save_tasks([]):
        return "I couldn't clear your tasks."
    return "All tasks cleared. ⚡"
