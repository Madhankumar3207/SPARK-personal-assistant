"""Native PySide6 SPARK interface, backed by the existing command pipeline."""
import html
import re

from PySide6.QtCore import QEvent, Qt, QThreadPool, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QPushButton, QTextBrowser, QTextEdit,
    QVBoxLayout, QWidget,
)

from main import get_mode_state, start_voice_listener
from ui.styles import APP_STYLE
from ui.worker import CommandWorker
from backend.services.reminders import start_scheduler, stop_scheduler


class MainWindow(QMainWindow):
    voice_result = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SPARK — Desktop Assistant")
        self.resize(1120, 760)
        self.setMinimumSize(780, 560)
        self.setStyleSheet(APP_STYLE)
        self.pool = QThreadPool.globalInstance()
        self.pool.setMaxThreadCount(2)
        self.voice_result.connect(self._append_exchange)
        self._build_ui()
        self._append_message("SPARK", "Hello bro! ⚡ I’m ready to help.")
        self._update_status()
        start_voice_listener(self._voice_command)
        start_scheduler(lambda item: self.voice_result.emit("", f"Reminder: {item['title']}"))

    def _build_ui(self):
        root = QWidget()
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        header = QHBoxLayout()
        brand = QLabel("SPARK ⚡")
        brand.setObjectName("brand")
        self.status = QLabel("● Online")
        self.status.setObjectName("muted")
        header.addWidget(brand)
        header.addStretch(1)
        header.addWidget(self.status)
        outer.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(12)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(175)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(12, 16, 12, 16)
        for label in ("New Chat", "Home", "Files", "Tasks", "Memory", "System", "Settings"):
            button = QPushButton(label)
            button.clicked.connect(lambda checked=False, page=label: self._show_page(page))
            side.addWidget(button)
        side.addStretch(1)
        self.mode_label = QLabel()
        self.mode_label.setWordWrap(True)
        self.mode_label.setObjectName("muted")
        side.addWidget(self.mode_label)
        self.voice_toggle = QPushButton("🎤  Voice")
        self.voice_toggle.setCheckable(True)
        self.voice_toggle.clicked.connect(self._toggle_voice)
        self.chat_toggle = QPushButton("Chat mode")
        self.chat_toggle.setCheckable(True)
        self.chat_toggle.clicked.connect(self._toggle_chat)
        side.addWidget(self.voice_toggle)
        side.addWidget(self.chat_toggle)
        body.addWidget(sidebar)

        content = QVBoxLayout()
        self.page_title = QLabel("Home")
        self.page_title.setStyleSheet("font-size: 14pt; font-weight: 600; padding: 6px;")
        content.addWidget(self.page_title)
        self.chat = QTextBrowser()
        self.chat.setOpenExternalLinks(False)
        content.addWidget(self.chat, 1)
        self.results = QListWidget()
        self.results.setMaximumHeight(135)
        self.results.hide()
        self.results.itemClicked.connect(self._open_selected_result)
        content.addWidget(self.results)
        entry = QHBoxLayout()
        self.mic = QPushButton("🎤")
        self.mic.setToolTip("Toggle voice input")
        self.mic.clicked.connect(self._toggle_voice)
        entry.addWidget(self.mic)
        self.input = QTextEdit()
        self.input.setPlaceholderText("Type a message…  Enter to send · Shift+Enter for a new line")
        self.input.setFixedHeight(72)
        self.input.installEventFilter(self)
        entry.addWidget(self.input, 1)
        send = QPushButton("Send")
        send.setObjectName("send")
        send.clicked.connect(self._send)
        entry.addWidget(send)
        content.addLayout(entry)
        body.addLayout(content, 1)
        outer.addLayout(body, 1)
        self.setCentralWidget(root)

    def eventFilter(self, watched, event):
        if watched is self.input and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not event.modifiers() & Qt.ShiftModifier:
                self._send()
                return True
        return super().eventFilter(watched, event)

    def _append_message(self, who, message):
        color = "#55cdb4" if who == "SPARK" else "#82b6ff"
        self.chat.append(f'<p style="margin:10px 0 4px;color:{color};font-weight:700">{html.escape(who)}</p>'
                         f'<p style="margin:0 0 10px;white-space:pre-wrap">{html.escape(message)}</p>')
        bar = self.chat.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _send(self):
        command = self.input.toPlainText().strip()
        if not command:
            return
        self.input.clear()
        self._dispatch(command)

    def _dispatch(self, command):
        worker = CommandWorker(command)
        worker.signals.finished.connect(self._command_done)
        self.pool.start(worker)

    def _command_done(self, command, response):
        self._append_exchange(command, response)
        self._populate_results(response)
        self._update_status()

    def _populate_results(self, response):
        if re.search(r"\n\s*\d+\.\s+", response):
            self.results.clear()
            for number, name in re.findall(r"(?:^|\n)\s*(\d+)\.\s+([^\n]+)", response):
                item = QListWidgetItem(f"{number}. {name.strip()}")
                item.setData(Qt.UserRole, number)
                self.results.addItem(item)
            self.results.setVisible(self.results.count() > 0)

    def _append_exchange(self, command, response):
        if command:
            self._append_message("You", command)
        if response:
            self._append_message("SPARK", response)
            self._populate_results(response)
        self._update_status()

    def _voice_command(self, command, response):
        self.voice_result.emit(command, response)

    def _open_selected_result(self, item):
        number = item.data(Qt.UserRole)
        if number:
            self._dispatch(f"open {number}")

    def _toggle_voice(self):
        target = "voice off" if get_mode_state()["voice"] else "voice on"
        self._dispatch(target)

    def _toggle_chat(self):
        target = "chat off" if get_mode_state()["chat"] else "chat on"
        self._dispatch(target)

    def _update_status(self):
        state = get_mode_state()
        self.mode_label.setText(f"VOICE {'ON' if state['voice'] else 'OFF'}\nCHAT {'ON' if state['chat'] else 'OFF'}")
        self.voice_toggle.setChecked(state["voice"])
        self.chat_toggle.setChecked(state["chat"])
        self.mic.setText("🎙 Listening" if state["voice"] else "🎤")
        self.status.setText("● Online")

    def _show_page(self, page):
        self.page_title.setText(page)
        actions = {
            "New Chat": None,
            "Home": "hello spark",
            "Files": "show my documents",
            "Tasks": "show my tasks",
            "Memory": "show my memory",
            "System": "what is my system",
            "Settings": None,
        }
        if page == "New Chat":
            self.chat.clear()
            self.results.clear()
            self.results.hide()
            self._append_message("SPARK", "New conversation started. What can I help with?")
        elif actions.get(page):
            self._dispatch(actions[page])
            if page == "System":
                self._dispatch("what is my ip")
        elif page == "Settings":
            self._append_message("SPARK", "Use the Voice and Chat controls to switch input modes. SPARK desktop assistant.")

    def closeEvent(self, event):
        stop_scheduler()
        super().closeEvent(event)
