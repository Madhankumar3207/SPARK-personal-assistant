"""Serialize API operations through SPARK's established controller and tools."""
import re
import threading

from main import get_mode_state, process_user_command, start_voice_listener
from memory.context import clear_memory, load_memory, remember
from tools import router as spark_router
from tools import tasks as task_tools
from tools.utility_tools import network_information, system_information

from backend.services.events import events
from backend.services import reminders
from backend.services.diagnostics import classify_result


service_lock = threading.RLock()


def _voice_event(command, response):
    events.publish({"type": "voice_result", "command": command, "response": response,
                    "mode": get_mode_state()})


def start_runtime():
    start_voice_listener(_voice_event)
    reminders.start_scheduler(lambda item: events.publish({"type": "reminder", "id": item["id"], "title": item["title"], "status": "delivered"}))


def stop_runtime():
    from main import chat_enabled, stop_event, voice_enabled
    stop_event.set()
    voice_enabled.clear()
    chat_enabled.clear()
    reminders.stop_scheduler()


def mode_state():
    state = get_mode_state()
    return {"voice_enabled": state["voice"], "chat_enabled": state["chat"]}


def run_command(message: str):
    with service_lock:
        before = mode_state()
        response = process_user_command(message)
        after = mode_state()
        if before != after:
            events.publish({"type": "mode", **after})
        return response


def chat(message: str):
    events.publish({"type": "processing", "active": True})
    try:
        with service_lock:
            before = mode_state()
            response = process_user_command(message)
            after = mode_state()
            if before != after:
                events.publish({"type": "mode", **after})
            results = []
            if re.search(r"(?:^|\n)\s*\d+\.\s+", response):
                results = [
                    {"id": index, "name": path.name, "path": str(path),
                     "type": path.suffix.lower().lstrip(".")}
                    for index, path in enumerate(spark_router.last_search_results, 1)
                ]
        success, category = classify_result(response)
        return {"response": response, "type": "files" if results else "text",
                "success": success, "category": category, "results": results}
    finally:
        events.publish({"type": "processing", "active": False})


def list_tasks():
    with service_lock:
        return task_tools._load_tasks()


def add_task(task: str, priority="normal", due_at=None):
    with service_lock:
        response = task_tools.add_task(task, priority, due_at)
        return response, task_tools._load_tasks()


def complete_task(task_id: int):
    with service_lock:
        tasks = task_tools._load_tasks()
        pending = [task for task in tasks if not task.get("completed", False)]
        number = next((index for index, task in enumerate(pending, 1)
                       if task.get("id") == task_id), None)
        response = task_tools.complete_task(number) if number else f"I couldn't find task {task_id}."
        return response, task_tools._load_tasks()


def update_task(task_id, task=None, priority=None, due_at=None, completed=None):
    with service_lock:
        try:
            saved = task_tools.update_task(task_id, task, priority, due_at, completed)
        except ValueError as error:
            return str(error), task_tools._load_tasks()
        message = "Task updated." if saved else f"I couldn't find task {task_id}."
        return message, task_tools._load_tasks()


def delete_task(task_id: int):
    with service_lock:
        tasks = task_tools._load_tasks()
        pending = [task for task in tasks if not task.get("completed", False)]
        number = next((index for index, task in enumerate(pending, 1)
                       if task.get("id") == task_id), None)
        response = task_tools.remove_task(number) if number else f"I couldn't find pending task {task_id}."
        return response, task_tools._load_tasks()


def memory_state():
    with service_lock:
        return load_memory()


def add_memory(key: str, value: str):
    with service_lock:
        return remember(key, value), load_memory()


def clear_all_memory():
    with service_lock:
        return clear_memory()


def system_state():
    system = system_information()
    network = network_information()
    values = {}
    for line in system.splitlines()[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip().lower().replace(" ", "_")] = value.strip()
    network_values = {}
    for line in network.splitlines()[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            network_values[key.strip().lower().replace(" ", "_")] = value.strip()
    values["storage"] = [line.strip() for line in system.split("Storage:", 1)[-1].splitlines() if line.strip()]
    values["network_status"] = network_values.get("internet", "Not available")
    values["local_ip"] = network_values.get("local_ip", "Not available")
    values["wifi"] = network_values.get("wifi", "Not available")
    values["network"] = network_values
    return values


def search_files(query: str):
    with service_lock:
        response = process_user_command(f"find {query}")
        return response, [
            {"id": index, "name": path.name, "path": str(path),
             "type": path.suffix.lower().lstrip(".")}
            for index, path in enumerate(spark_router.last_search_results, 1)
        ]


def open_file_result(result_id: int):
    with service_lock:
        return process_user_command(f"open {result_id}")
