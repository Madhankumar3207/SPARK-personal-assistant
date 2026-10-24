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

## Build and Run on Windows

Requirements: Windows 10/11, Python 3.10+, Node.js/npm for the browser frontend, and a microphone for voice input. Install Python dependencies in a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

`python main.py` starts the existing terminal assistant. For the native desktop interface, run `python gui_main.py`.

For the local API and responsive browser app, use two terminals from the repository root:

```powershell
python -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite address shown in the frontend terminal (normally `http://127.0.0.1:5173`). The API listens on localhost by default. Build the frontend with `cd frontend; npm run build`; when `frontend/dist` exists, FastAPI serves it at `http://127.0.0.1:8000`.

Voice input uses `SpeechRecognition` and `PyAudio`; if unavailable, chat remains usable. Excel uses `openpyxl`.

## Natural Language, Tasks, and Reminders

SPARK uses deterministic intent parsing and a small set of English/Tanglish aliases. A supported Tanglish reminder form is `Naalaikku evening 5 manikku assignment submit panna remind pannu`. The default timezone is `Asia/Kolkata`; configure `SPARK_TIMEZONE` to change it. If a date or time is missing or ambiguous, SPARK asks for clarification. Daily and weekly recurrence are supported.

Tasks remain in the existing JSON store and retain stable IDs; optional priority and due-date fields are backward compatible. Reminders and WhatsApp review suggestions use SQLite at `data/spark.sqlite3` (or `%LOCALAPPDATA%\SPARK\data\spark.sqlite3` when packaged). A single backend scheduler claims each due reminder once and emits an in-app WebSocket event. The backend must be running for delivery; reminders are not guaranteed while it is closed, and there is no OS-level push delivery.

## Mobile Access and PWA

The frontend is responsive and includes a basic installable PWA shell. Localhost works on the same computer. LAN binding and authenticated pairing are not enabled; do not expose the API to another network or the public internet. Microphone, installation, and notification support varies by browser and generally requires HTTPS or localhost. Offline caching covers the app shell only, not API data or laptop file access.

## Android Digital Wellbeing Companion

The separate native Kotlin companion project is in `android/` (Android Studio, Android SDK 36, and JDK 17 are required). Open that folder in Android Studio, allow Gradle sync, connect an Android device with USB debugging enabled, then run the `app` configuration. The companion is local-first and works without the SPARK laptop backend or internet after installation. Automated policy tests are in `android/app/src/test`; run `gradle :app:testDebugUnitTest` from `android/` when Gradle/Android tooling is installed.

On the phone, choose distracting apps explicitly, set the per-app session usage threshold, warning grace, and session length, then grant Usage Access and notifications and start a session. Android Usage Access is special app access, not a normal permission dialog; SPARK first explains its narrow use, then opens Android's Usage Access settings. Usage events and local session history stay on-device. Only selected app IDs and usage durations are read; no message text, screenshots, keystrokes, or network upload is used. Disable the session in SPARK or revoke Usage Access at any time.

Android restricts apps from launching activities over another app. SPARK therefore does not claim it can forcibly redirect to Home: on a second violation it posts a focus notification with a user-tapped **Go to Home** action. It never kills or force-stops other apps and does not use AccessibilityService, Device Admin, root, or overlays. A visible, ongoing foreground-service notification is required while monitoring. OEM battery controls can still interrupt monitoring. Device-specific behavior has not been tested here; do not treat the companion as production-ready until tested on physical devices. Google Play may require an Android 14+ `specialUse` foreground-service declaration/review; listing compliance and Play approval are not guaranteed. This current starter implementation has manual session start/end; scheduled starts and daily limit enforcement are not implemented. The React wellbeing page explains the native setup but does not inspect phone apps or synchronize private usage history.

The implementation follows Android's [UsageStatsManager documentation](https://developer.android.com/reference/android/app/usage/UsageStatsManager), [Usage Access settings action](https://developer.android.com/reference/android/provider/Settings#ACTION_USAGE_ACCESS_SETTINGS), [background activity launch restrictions](https://developer.android.com/guide/components/activities/background-starts), [foreground-service requirements](https://developer.android.com/develop/background-work/services/fgs/service-types), and Google Play's [Accessibility API policy](https://support.google.com/googleplay/android-developer/answer/10964491). We avoid AccessibilityService because SPARK is a general assistant rather than a disability-support tool and narrower Usage Access is available.

## WhatsApp Export Analysis and Privacy

In WhatsApp, export a chat without media and select the `.txt` file in SPARK's WhatsApp Analysis page. The local API accepts text exports up to 5 MB, parses common timestamp formats, and keeps only review suggestions/evidence snippets plus a source fingerprint in local SQLite; it does not save the original export. Parsing is heuristic and may not resolve every locale or deadline. Review, edit, approve, or reject each suggestion. Suggestions without a clear deadline must be edited before reminder approval. No live WhatsApp connection, scraping, or third-party upload is implemented.

Run `python -m unittest discover -s tests` for the synthetic NLP, reminders, and WhatsApp parser checks. Existing helpers are `python test_excel.py` and `python test_voice.py` (voice requires working microphone dependencies and hardware).

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
- Memory, tasks, and learned skills are stored locally in JSON files in development and under `%LOCALAPPDATA%\SPARK` when packaged. Reminder records and limited WhatsApp review data are stored locally in SQLite. Review runtime data before sharing backups.
