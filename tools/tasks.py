"""Persistent, local task management for SPARK."""

import json
import os
import tempfile
from pathlib import Path

from config.paths import runtime_file


TASK_FILE = runtime_file("data", "tasks.json")
TASK_READ_ERROR = "I couldn't read tasks.json; the file was preserved. Please inspect it before changing tasks."


def _load_tasks():
    try:
        with TASK_FILE.open("r", encoding="utf-8") as file:
            tasks = json.load(file)
        if not isinstance(tasks, list) or not all(isinstance(task, dict) for task in tasks):
            raise ValueError(TASK_READ_ERROR)
        return tasks
    except FileNotFoundError:
        _save_tasks([])
        return []
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        raise ValueError(TASK_READ_ERROR) from exc


def _save_tasks(tasks):
    temporary_path = None
    try:
        TASK_FILE.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=TASK_FILE.parent,
                                         prefix=TASK_FILE.name + ".", suffix=".tmp", delete=False) as file:
            temporary_path = file.name
            json.dump(tasks, file, indent=2, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, TASK_FILE)
        return True
    except (OSError, TypeError, ValueError):
        return False
    finally:
        if temporary_path and os.path.exists(temporary_path):
            try:
                os.unlink(temporary_path)
            except OSError:
                pass


def _pending(tasks):
    return [task for task in tasks if not task.get("completed", False)]


def _display_task(text):
    text = text.strip()
    return text[:1].upper() + text[1:]


def add_task(text, priority="normal", due_at=None):
    if not text or not text.strip():
        return "Please tell me what task you want me to add."
    try:
        tasks = _load_tasks()
    except ValueError as exc:
        return str(exc)
    next_id = max((task.get("id", 0) for task in tasks), default=0) + 1
    task_text = _display_task(text)
    if priority not in {"low", "normal", "high"}:
        priority = "normal"
    tasks.append({"id": next_id, "task": task_text, "completed": False,
                  "priority": priority, "due_at": due_at})
    if not _save_tasks(tasks):
        return "I couldn't save that task."
    return f"Task added: {task_text}. ⚡"


def show_tasks():
    try:
        tasks = _pending(_load_tasks())
    except ValueError as exc:
        return str(exc)
    if not tasks:
        return "You have no pending tasks. ⚡"
    lines = ["My Tasks:", ""]
    lines.extend(f"{number}. {task['task']}" for number, task in enumerate(tasks, 1))
    return "\n".join(lines)


def _task_at_pending_number(number):
    if not isinstance(number, int) or number < 1:
        return None, None
    try:
        tasks = _load_tasks()
    except ValueError:
        return None, None
    pending = _pending(tasks)
    return tasks, pending[number - 1] if number <= len(pending) else None


def complete_task(number):
    if not isinstance(number, int):
        return "Please provide a valid task number."
    tasks, task = _task_at_pending_number(number)
    if tasks is None:
        return TASK_READ_ERROR
    if task is None:
        return f"I couldn't find task {number}."
    task["completed"] = True
    if not _save_tasks(tasks):
        return "I couldn't save that task update."
    return f"Task {number} completed: {task['task']}. ⚡"


def update_task(task_id, task_text=None, priority=None, due_at=None, completed=None):
    try:
        tasks = _load_tasks()
    except ValueError:
        return False
    task = next((item for item in tasks if item.get("id") == task_id), None)
    if task is None:
        return False
    if task_text is not None:
        task["task"] = _display_task(task_text)
    if priority is not None:
        if priority not in {"low", "normal", "high"}:
            raise ValueError("Priority must be low, normal, or high.")
        task["priority"] = priority
    if due_at is not None:
        task["due_at"] = due_at
    if completed is not None:
        task["completed"] = completed
    return _save_tasks(tasks)


def remove_task(number):
    if not isinstance(number, int):
        return "Please provide a valid task number."
    tasks, task = _task_at_pending_number(number)
    if tasks is None:
        return TASK_READ_ERROR
    if task is None:
        return f"I couldn't find task {number}."
    tasks.remove(task)
    if not _save_tasks(tasks):
        return "I couldn't save that task update."
    return f"Task {number} removed. ⚡"


def clear_completed_tasks():
    try:
        tasks = _load_tasks()
    except ValueError as exc:
        return str(exc)
    if not _save_tasks(_pending(tasks)):
        return "I couldn't clear completed tasks."
    return "Completed tasks cleared. ⚡"


def clear_all_tasks():
    if not _save_tasks([]):
        return "I couldn't clear your tasks."
    return "All tasks cleared. ⚡"
