import re
import sys
import threading
import time

from agents.brain import understand_command
from tools.router import execute_action
from tools.tool_selector import select_tool
from voice.speech import listen


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


print("⚡ SPARK is starting...")
print("SPARK: Voice and chat are ready.")


voice_enabled = threading.Event()
chat_enabled = threading.Event()
stop_event = threading.Event()
command_lock = threading.Lock()

voice_enabled.set()
chat_enabled.set()
voice_thread = None


def normalize_command(command):

    command = command.strip()

    return re.sub(r"[.!?]+$", "", command).strip()


def process_command(command, from_voice=False):

    command = normalize_command(command)

    if not command:
        return False

    with command_lock:

        understood = understand_command(command)

        understood = select_tool(understood)

        if understood.get("action") == "MODE_CONTROL":

            mode = understood.get("mode")
            enabled = understood.get("enabled")

            if mode == "voice":

                if not enabled and not chat_enabled.is_set():
                    understood["message"] = (
                        "Chat is off, so voice must stay on."
                    )

                elif enabled:
                    voice_enabled.set()
                    start_voice_listener()
                else:
                    voice_enabled.clear()

            elif mode == "chat":

                if not enabled and not voice_enabled.is_set():
                    understood["message"] = (
                        "Voice is off, so chat must stay on."
                    )

                elif enabled:
                    chat_enabled.set()
                else:
                    chat_enabled.clear()

        result = execute_action(understood)

        print("SPARK:", result)

        if understood.get("action") == "EXIT":

            stop_event.set()
            voice_enabled.clear()
            chat_enabled.clear()

            return True

    return False


def voice_loop():

    last_command = ""
    last_command_time = 0.0

    while not stop_event.is_set():

        if not voice_enabled.is_set():
            time.sleep(0.2)
            continue

        command = listen()

        if command is None:
            print("SPARK: Voice input temporarily unavailable.")
            time.sleep(1)
            continue

        if not command:
            time.sleep(0.3)
            continue

        command = normalize_command(command)
        current_time = time.monotonic()

        if (
            command == last_command
            and current_time - last_command_time < 2
        ):
            continue

        last_command = command
        last_command_time = current_time

        if process_command(command, from_voice=True):
            break


def start_voice_listener():

    global voice_thread

    if voice_thread is None or not voice_thread.is_alive():
        voice_thread = threading.Thread(
            target=voice_loop,
            daemon=True
        )
        voice_thread.start()


start_voice_listener()


while not stop_event.is_set():

    if not chat_enabled.is_set():
        time.sleep(0.2)
        continue

    try:
        command = input("\nYou: ")

    except KeyboardInterrupt:

        if stop_event.is_set():
            break

        print()
        continue

    except EOFError:
        stop_event.set()
        break

    if process_command(command):
        break
