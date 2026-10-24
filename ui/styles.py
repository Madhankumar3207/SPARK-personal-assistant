"""Compact dark theme for the native SPARK window."""

APP_STYLE = """
QWidget { background: #10151d; color: #e8edf5; font-family: 'Segoe UI'; font-size: 10pt; }
QFrame#sidebar { background: #151c26; border-right: 1px solid #26313f; }
QLabel#brand { color: #f4f7fb; font-size: 19pt; font-weight: 700; }
QLabel#muted { color: #8e9bad; }
QPushButton { background: #202a37; border: 1px solid #2c3949; border-radius: 9px; padding: 9px 13px; }
QPushButton:hover { background: #2a3849; border-color: #3c566f; }
QPushButton:checked { background: #133b3a; border-color: #21a88b; color: #81edce; }
QPushButton#send { background: #167d79; border: 0; font-weight: 700; padding: 10px 20px; }
QTextBrowser, QTextEdit, QLineEdit, QListWidget { background: #171f2a; border: 1px solid #2b3746; border-radius: 11px; padding: 10px; selection-background-color: #176e79; }
QTextBrowser { padding: 16px; }
QScrollBar:vertical { background: #10151d; width: 9px; margin: 0; }
QScrollBar::handle:vertical { background: #354252; border-radius: 4px; min-height: 25px; }
"""
