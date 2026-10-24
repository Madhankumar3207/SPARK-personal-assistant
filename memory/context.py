import json
import os
import tempfile

from config.paths import runtime_file


# -------------------------------------------------
# MEMORY FILE
# -------------------------------------------------

MEMORY_FILE = runtime_file("memory", "memory.json")
MEMORY_READ_ERROR = "I couldn't read memory.json; the file was preserved. Please inspect it before writing new memory."


# -------------------------------------------------
# LOAD MEMORY
# -------------------------------------------------

def load_memory():

    if not MEMORY_FILE.exists():
        save_memory({})
        return {}

    try:

        with open(
            MEMORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            memory = json.load(file)
            if not isinstance(memory, dict):
                raise ValueError("Memory data must be a JSON object.")
            return memory

    except (json.JSONDecodeError, OSError, ValueError) as exc:
        raise ValueError(MEMORY_READ_ERROR) from exc


# -------------------------------------------------
# SAVE MEMORY
# -------------------------------------------------

def save_memory(memory):
    temporary_path = None
    try:
        MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=MEMORY_FILE.parent,
                                         prefix=MEMORY_FILE.name + ".", suffix=".tmp", delete=False) as file:
            temporary_path = file.name
            json.dump(memory, file, indent=4, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, MEMORY_FILE)
        return True
    except (OSError, TypeError, ValueError):
        return False
    finally:
        if temporary_path and os.path.exists(temporary_path):
            try:
                os.unlink(temporary_path)
            except OSError:
                pass


# -------------------------------------------------
# REMEMBER
# -------------------------------------------------

def remember(key, value):

    if not isinstance(key, str) or not key.strip() or not isinstance(value, str) or not value.strip():
        return "Please provide a non-empty memory key and value."

    try:
        memory = load_memory()
    except ValueError as exc:
        return str(exc)

    key = " ".join(key.lower().split())
    value = " ".join(value.split())

    if memory.get(key) == value:
        return f"Your {key} is already saved as {value}."

    memory[key] = value

    if not save_memory(memory):
        return "I couldn't save that memory. Please check the storage location and try again."

    return (
        f"I'll remember that "
        f"{key} is {value}."
    )


# -------------------------------------------------
# RECALL
# -------------------------------------------------

def recall(key):

    if not isinstance(key, str) or not key.strip():
        return "Please tell me what you want me to recall."

    try:
        memory = load_memory()
    except ValueError as exc:
        return str(exc)

    key = key.lower().strip()

    if key in memory:

        return (
            f"{key} is "
            f"{memory[key]}."
        )

    return (
        f"I don't remember anything "
        f"about {key}."
    )


# -------------------------------------------------
# SHOW MEMORY
# -------------------------------------------------

def show_memory():

    try:
        memory = load_memory()
    except ValueError as exc:
        return str(exc)

    if not memory:

        return "My memory is empty."

    result = []

    for key, value in memory.items():

        result.append(
            f"{key}: {value}"
        )

    return "\n".join(result)


# -------------------------------------------------
# CLEAR MEMORY
# -------------------------------------------------

def clear_memory():

    if not save_memory({}):
        return "I couldn't clear memory. Please check the storage location and try again."

    return "My memory has been cleared."
