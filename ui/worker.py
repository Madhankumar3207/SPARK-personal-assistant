"""Bounded command workers and a single persistent voice-listener thread."""
from PySide6.QtCore import QObject, QRunnable, QThread, Signal, Slot

from main import listen, process_user_command, voice_enabled


class CommandSignals(QObject):
    finished = Signal(str, str)


class CommandWorker(QRunnable):
    def __init__(self, command):
        super().__init__()
        self.command = command
        self.signals = CommandSignals()

    @Slot()
    def run(self):
        try:
            response = process_user_command(self.command)
        except Exception:
            response = "I couldn't complete that command. Please try again."
        self.signals.finished.emit(self.command, response)


class VoiceListener(QThread):
    recognized = Signal(str, str)

    def run(self):
        previous = ""
        while not self.isInterruptionRequested():
            if not voice_enabled.is_set():
                self.msleep(150)
                continue
            try:
                command = listen()
            except Exception:
                command = None
            if command is None:
                self.recognized.emit("", "Voice input is temporarily unavailable.")
                self.msleep(1000)
            elif command:
                command = command.strip()
                if command and command.lower() != previous.lower():
                    previous = command
                    try:
                        self.recognized.emit(command, process_user_command(command))
                    except Exception:
                        self.recognized.emit(command, "I couldn't process that voice command.")
