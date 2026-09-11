import json
import os


# -------------------------------------------------
# MEMORY FILE
# -------------------------------------------------

MEMORY_FILE = os.path.join(
    os.path.dirname(__file__),
    "memory.json"
)


# -------------------------------------------------
# LOAD MEMORY
# -------------------------------------------------

def load_memory():

    if not os.path.exists(MEMORY_FILE):
        return {}

    try:

        with open(
            MEMORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        return {}


# -------------------------------------------------
# SAVE MEMORY
# -------------------------------------------------

def save_memory(memory):

    try:

        with open(
            MEMORY_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                memory,
                file,
                indent=4,
                ensure_ascii=False
            )

        return True

    except Exception:

        return False


# -------------------------------------------------
# REMEMBER
# -------------------------------------------------

def remember(key, value):

    memory = load_memory()

    key = " ".join(key.lower().split())
    value = " ".join(value.lower().split())

    if memory.get(key) == value:
        return f"Your {key} is already saved as {value}."

    memory[key] = value

    save_memory(memory)

    return (
        f"I'll remember that "
        f"{key} is {value}."
    )


# -------------------------------------------------
# RECALL
# -------------------------------------------------

def recall(key):

    memory = load_memory()

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

    memory = load_memory()

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

    save_memory({})

    return "My memory has been cleared."
