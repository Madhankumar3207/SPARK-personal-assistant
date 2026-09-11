# SPARK – Smart Personal Assistant

SPARK is a Windows-based Python desktop assistant that accepts both chat and voice commands. It provides practical local-assistant features—such as file search, application control, memory, Excel marks, task management, and system information—through one shared command pipeline.

## Features

- Chat input and optional voice input
- Voice ON/OFF and chat ON/OFF controls
- Persistent local memory: remember, recall, show, and clear memory
- Natural memory commands, for example: `my name is Madhankumar`
- Local file search for PDFs, images/photos, videos, audio, documents, and other matching files
- Date and time filters for supported file searches
- Numbered search results and single-result opening: `open 1`, `open first`, `open last`, or a matching filename
- Find the largest file in a supported Windows user folder
- Open Chrome, Calculator, Notepad, VS Code, File Explorer, and Excel
- Chrome profile and web-search helpers
- Excel marks management: add students, update/increase marks, get one mark, and show all marks
- Basic conversation, calculator, pattern analysis, task management, and system/network information
- Controlled, allowlisted self-learning for selected safe capabilities
- Safe handling for unsupported requests
- Computer power controls are intentionally disabled

## Technologies used

- Python
- Windows OS integration (`os.startfile`, `subprocess`, `ctypes`, and standard library utilities)
- `SpeechRecognition` for optional microphone input
- `openpyxl` for Excel workbook handling
- Threading for simultaneous chat and voice input
- JSON local storage for memory, tasks, and learned skill definitions
- Filesystem handling with `pathlib`, `os`, and `shutil`

## Project structure

```text
SPARK/
├── main.py                       # Application entry point; chat and voice loops
├── agents/
│   └── brain.py                  # Command understanding and action selection
├── analysis/
│   └── pattern_analyzer.py       # Number and text pattern analysis
├── config/
│   └── chrome_profiles.py        # Optional Chrome profile configuration
├── data/
│   └── tasks.json                # Persistent task data
├── memory/
│   ├── context.py                # Memory operations
│   └── memory.json               # Persistent memory data
├── skills/
│   └── learned_skills.json       # Safe learned capability definitions
├── tools/
│   ├── app_tools.py              # Application, file-opening, and web helpers
│   ├── excel_tools.py            # Excel marks operations
│   ├── file_tools.py             # File search and safe file-management helpers
│   ├── learner.py                # Controlled self-learning fallback
│   ├── router.py                 # Action execution router
│   ├── tasks.py                  # Task-management operations
│   ├── tool_selector.py          # Existing-capability selector
│   └── utility_tools.py          # Calculator, system, and network helpers
├── voice/
│   └── speech.py                 # Optional speech-recognition input
├── test_excel.py                 # Excel test helper
└── test_voice.py                 # Voice test helper
```

## Setup

SPARK is designed for Windows. Install the imported third-party libraries:

```powershell
py -m pip install openpyxl SpeechRecognition PyAudio
```

`SpeechRecognition` and `PyAudio` are required only for microphone input. Chat mode remains available if voice dependencies are not installed.

## Run

```powershell
py main.py
```

## Example commands

```text
hello spark
my name is Madhankumar
what is my name
show my photos
find my resume
open 1
find the largest file in Downloads
open chrome
what is Kavin mark
show my tasks
what is my system
```

## Safety

SPARK does not provide unrestricted shell, PowerShell, CMD, or Python execution. Destructive file actions require confirmation, and computer power controls—including shutdown, restart, lock, sleep, hibernate, and sign-out—are intentionally disabled.

## Notes

- Excel marks commands expect a workbook at `~/OneDrive/Documents/test.xlsx` with `Name` and `Mark` columns.
- Memory, tasks, and learned skills are stored locally in JSON files. Review those files before publishing a repository if they contain personal data.
