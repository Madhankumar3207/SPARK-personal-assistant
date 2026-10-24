
# ⚡ SPARK — Smart Personal AI Assistant

**An adaptive, local-first personal assistant for Windows, with a Python backend, web interface, voice interaction, task management, and an Android Digital Wellbeing companion.**

SPARK is a personal assistant project designed to bring everyday computer tasks, natural-language commands, local memory, file search, productivity tools, and controlled self-learning into one application.

The project includes a Python command-line assistant, a native desktop UI, a FastAPI backend, a React/Vite frontend, and a separate Android companion for digital wellbeing.

> **Project status:** Active development. Features, integrations, and platform behaviour should be tested in the target environment before production use.

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Technology Stack](#-technology-stack)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [System Requirements](#-system-requirements)
- [Installation](#-installation)
- [Running SPARK](#-running-spark)
- [Natural Language Processing](#-natural-language-processing)
- [Tasks and Reminders](#-tasks-and-reminders)
- [WhatsApp Export Analysis](#-whatsapp-export-analysis)
- [Mobile Support](#-mobile-support)
- [Android Digital Wellbeing](#-android-digital-wellbeing)
- [Testing](#-testing)
- [Configuration and Data Storage](#-configuration-and-data-storage)
- [Security and Privacy](#-security-and-privacy)
- [Troubleshooting](#-troubleshooting)
- [Roadmap](#-roadmap)

---

## 🚀 Overview

SPARK aims to provide a unified personal-assistant experience across desktop and mobile interfaces.

Instead of relying exclusively on exact command strings, SPARK uses command interpretation, supported language patterns, application tools, memory, and task services to handle common requests.

Its design focuses on four principles:

- **Understand:** Interpret supported natural-language requests and command variations.
- **Assist:** Use existing tools for files, applications, calculations, memory, and productivity.
- **Remember:** Retain supported information and task data locally.
- **Improve safely:** Diagnose failures and support controlled learning without unrestricted code execution.

SPARK is primarily designed to run locally on a Windows computer. The browser frontend communicates with the Python backend, while the Android wellbeing companion operates separately on the phone.

## ✨ Features

### 🧠 Natural Language and Conversation

- Basic conversational responses and greetings.
- Recognition of supported command variations and spelling errors.
- English and selected English/Tanglish command patterns.
- Personal memory retrieval and updates.
- Command routing to existing SPARK tools.
- Controlled fallback behaviour for unsupported requests.

Language understanding is based on the patterns and capabilities implemented in the project. It is not guaranteed to understand every sentence, language, typo, or ambiguous instruction.

### 📁 File Search and Application Control

- Search local files, including supported PDFs, images, videos, audio files, and documents.
- Display numbered file-search results.
- Open a selected result through the existing backend.
- Filter supported searches by date or time where available.
- Find the largest file in supported folders.
- Launch supported Windows applications such as Chrome, Calculator, Notepad, VS Code, File Explorer, and Excel.
- Support configured Chrome profiles and web-search helpers where available.

File access depends on the Windows account's permissions and the paths supported by the implementation.

### 💾 Personal Memory

- Save supported personal information.
- Retrieve stored information using recognised requests.
- Display or clear memory through supported operations.
- Persist memory locally.

Example:

```text
my name is Madhankumar
what is my name
show memory
```

Only information actually stored in memory should be presented as remembered information.

### 📊 Excel Assistant

The existing Excel functionality supports operations such as:

- Retrieve a student's mark.
- Increase or update marks.
- Add students.
- Display supported workbook records.

Example:

```text
what is Kavin mark
increase Kavin mark by 5
change Kavin mark to 95
```

Excel operations depend on a valid workbook and the expected column structure.

### 🔢 Calculations and Pattern Analysis

- Perform supported mathematical calculations.
- Analyse numerical sequences.
- Identify supported number patterns.
- Calculate likely next values for recognised sequences.
- Display basic statistics where implemented.

Example:

```text
calculate 25 * 4
analyze 1 4 9 16
```

Results depend on the expression parser and the patterns supported by the current implementation.

### ✅ Tasks and Reminders

- Create and list tasks.
- Track task completion.
- Preserve task data using the existing storage mechanism.
- Support due dates, reminder scheduling, and recurrence where implemented.
- Display reminder and task information through supported interfaces.

Reminder delivery depends on the backend scheduler and the configured notification mechanism. Background delivery is not guaranteed while the required application or backend is closed.

### 🔍 Controlled Self-Learning

SPARK includes a controlled learning/fallback mechanism for selected safe capabilities.

The intended approach is to identify unsupported requests, inspect relevant failures, reuse existing tools, and validate safe improvements.

Online research availability depends on the configured provider and network connectivity.

Untrusted online instructions must never override security restrictions. Source-code changes, new permissions, and sensitive capabilities should require appropriate review and approval.

### 🖥️ System and Network Information

Supported system utilities can report information such as:

- Operating-system details.
- CPU and RAM information.
- Storage capacity and usage.
- Network connectivity.
- Local IP address and related network information.

Available details depend on the operating system and the libraries used.

### 🎤 Voice and Chat

- Text-based command input.
- Optional microphone input.
- Voice/chat mode controls.
- Background voice processing where supported.
- Graceful handling of unavailable microphone dependencies.

Voice functionality requires suitable hardware, permissions, and dependencies. Chat should remain available when voice input is unavailable.

### 🪟 Desktop Interfaces

SPARK provides separate entry points for its existing terminal assistant and native desktop interface.

The project also includes a responsive React frontend for browser-based interaction through a local API.

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Core application | Python |
| Command understanding | Python intent and routing services |
| API backend | FastAPI |
| API validation | Pydantic |
| Browser frontend | React |
| Frontend development server | Vite |
| Frontend language | JavaScript, JSX and CSS |
| Android companion | Kotlin and Android SDK |
| Excel operations | openpyxl |
| Voice recognition | SpeechRecognition and PyAudio |
| Persistence | JSON and SQLite, depending on the feature |
| Testing | Python unittest and Android unit tests |
| Packaging | PyInstaller configuration/script, where supported |

---

## 🏗️ Architecture

```text
                       SPARK
                         |
          +--------------+--------------+
          |              |              |
       CLI App        Desktop UI     React Frontend
      main.py         gui_main.py      Vite / React
          |              |              |
          +--------------+--------------+
                         |
                   FastAPI Backend
                         |
              Shared SPARK Core Services
                         |
          +--------------+--------------+
          |              |              |
         NLP          Tasks/Memory     Tool Router
          |              |              |
      WhatsApp       Reminders        File/Excel/
      Analysis       Scheduler        System Tools
                         |
                 Local Persistent Data

          Separate Android Wellbeing App
                Kotlin / Android
```

The React interface does not directly access Windows files or applications. Such operations must go through the local Python backend and its validated tools.

The Android wellbeing companion has its own native implementation and local usage-monitoring logic.

## 📂 Project Structure

The following is a simplified overview of the repository. Some modules contain additional files.

```text
SPARK/
│
├── main.py
├── gui_main.py
├── build_windows.bat
├── requirements.txt
├── README.md
├── QA_AUDIT_REPORT.md
│
├── agents/
│   └── brain.py
│
├── analysis/
│   └── pattern_analyzer.py
│
├── backend/
│   ├── api/
│   │   ├── main.py
│   │   └── schemas.py
│   └── services/
│       ├── diagnostics.py
│       ├── events.py
│       ├── nlp.py
│       ├── reminders.py
│       ├── spark_service.py
│       └── whatsapp.py
│
├── config/
│   └── paths.py
│
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   ├── index.html
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       └── styles/
│
├── android/
│   ├── app/
│   │   └── src/
│   │       ├── main/
│   │       └── test/
│   ├── build.gradle.kts
│   └── settings.gradle.kts
│
├── memory/
├── data/
├── skills/
├── tools/
├── voice/
├── ui/
└── tests/
```

---

## 💻 System Requirements

### Windows application

- Windows 10 or Windows 11.
- Python 3.10 or later, compatible with the project's dependencies.
- Internet connection for online-research features that require a configured provider.
- Microphone and supported dependencies for voice input.
- Microsoft Excel or another compatible workbook editor is useful for Excel-related tasks.

### Web frontend

- Node.js and npm.
- A modern browser.
- The Python backend running locally.

### Android companion

- Android Studio.
- Android SDK 36 as configured by the project.
- JDK 17.
- An Android device or emulator compatible with the project's configuration.
- Additional user-granted access for application-usage monitoring and notifications.

---

## ⚙️ Installation

### 1. Clone the repository

```powershell
git clone https://github.com/Madhankumar3207/SPARK-personal-assistant.git
cd SPARK-personal-assistant
```

### 2. Create a Python virtual environment

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

```bat
.venv\Scripts\activate.bat
```

### 3. Install Python dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If voice dependencies cannot be installed on your particular environment, resolve their installation separately. Core text-based functionality should remain usable where voice is optional.

### 4. Install frontend dependencies

Open a second terminal in the repository root:

```powershell
cd frontend
npm install
```

Return to the repository root after installing if you intend to run backend commands from there.

---

## ▶️ Running SPARK

### Option 1: Terminal assistant

From the repository root with the Python environment activated:

```powershell
python main.py
```

This launches the existing terminal-based assistant.

### Option 2: Native desktop interface

From the repository root:

```powershell
python gui_main.py
```

The desktop interface requires its configured GUI dependencies.

### Option 3: FastAPI backend

Open a terminal in the repository root:

```powershell
python -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

The API is bound to localhost by default.

Do not change the host to `0.0.0.0` or expose the backend publicly without implementing and verifying proper authentication, authorization, network protections, and secure pairing.

### Option 4: React frontend

Open a separate terminal in the repository root:

```powershell
cd frontend
npm run dev
```

Open the local address displayed by Vite, normally:

```text
http://127.0.0.1:5173
```

The frontend needs the backend to be running for API-backed features.

### Build the frontend

From the frontend directory:

```powershell
npm run build
```

The production build is normally generated in `frontend/dist`.

The current FastAPI setup is intended to serve that built frontend at:

```text
http://127.0.0.1:8000
```

when the required production-serving configuration is present.

### Windows executable

The repository includes `build_windows.bat` for the Windows packaging workflow.

Review the build script, install its required dependencies, and run it from the project root. Treat packaging as successful only when the build exits successfully and the expected executable exists.

---

## 🗣️ Natural Language Processing

SPARK uses command interpretation, input normalization, and supported English/Tanglish aliases.

Example commands:

```text
hello spark
hi bro
my name is Madhankumar
what is my name
find my resume
open calculator
show my tasks
```

A supported Tanglish reminder form is:

```text
Naalaikku evening 5 manikku assignment submit panna remind pannu
```

The default reminder timezone is:

```text
Asia/Kolkata
```

To configure a different timezone, set the `SPARK_TIMEZONE` environment variable to an appropriate timezone identifier supported by the application.

Language understanding is not unlimited. Misspellings, ambiguous entities, unsupported phrases, and complex multi-action requests may require clarification or additional implementation.

SPARK should report failures honestly rather than inventing an answer or claiming an action succeeded when it did not.

---

## ✅ Tasks and Reminders

Task records use the existing local task store and stable IDs. Optional priority and due-date fields are supported by the current service where available.

Reminder records and WhatsApp review suggestions use SQLite:

```text
data/spark.sqlite3
```

When packaged, the configured application-data location may instead use:

```text
%LOCALAPPDATA%\SPARK
```

The backend scheduler processes due reminders and can emit in-app events through WebSocket.

**Important limitations:**

- The backend must be running for scheduled reminder delivery.
- Reminders are not guaranteed while the backend is closed.
- OS-level push notifications are not implemented by the current reminder architecture.
- Recurrence is limited to the patterns actually implemented and tested.

---

## 💬 WhatsApp Export Analysis

SPARK's initial WhatsApp feature analyses a chat export selected by the user. It does not provide unrestricted live access to personal WhatsApp conversations.

### How to use it

1. Open WhatsApp.
2. Export the required chat, preferably without media.
3. Select the exported `.txt` file in SPARK's WhatsApp Analysis page.
4. Review the extracted tasks and potential deadlines.
5. Edit, approve, or reject each suggestion.
6. Approved suggestions can be saved through the task/reminder service.

The local API supports text exports up to 5 MB and attempts to parse common timestamps and multiline messages.

The parser uses heuristics and may not correctly interpret every locale, timestamp format, abbreviation, or ambiguous deadline.

Suggestions without a clear deadline must be edited before reminder approval.

The implementation stores review suggestions, evidence snippets, and a source fingerprint in local SQLite; it does not intentionally retain the original export file.

No live WhatsApp connection, unofficial scraping, or default third-party upload is implemented.

Avoid importing chats containing information you do not have permission to process. Review local data-storage and backup practices before sharing application data.

---

## 📱 Mobile Support

The React frontend includes a responsive interface and a basic installable Progressive Web App (PWA) shell.

It can be opened in a supported mobile browser, subject to the browser's installation and permission capabilities.

Current limitations:

- Localhost refers to the device on which the service is running.
- Authenticated LAN pairing has not been enabled in the current configuration.
- Do not expose the local API to another network or the public internet.
- Microphone access, PWA installation, and browser notifications depend on browser support and secure-context requirements.
- Offline caching covers the application shell, not live API data or laptop files.
- The frontend cannot independently control applications or read files on the laptop without the backend.

A secure remote-access configuration must be implemented before using SPARK's computer-control features across networks.

---

## 📵 Android Digital Wellbeing Companion

The separate native Android project is located in:

```text
android/
```

Open this directory in Android Studio, allow Gradle sync, connect a compatible device or emulator, and run the application configuration.

The companion is designed to work locally after installation and does not require the laptop backend for its core usage-monitoring functionality.

### Setup

1. Open the `android` directory in Android Studio.
2. Allow Gradle sync to finish.
3. Run the app on a compatible Android device.
4. Select the apps you want to treat as distractions.
5. Configure per-app session usage thresholds, warning grace periods, and session length.
6. Grant Usage Access in Android Settings.
7. Grant notification permission where required.
8. Start a focus session.

Usage Access is special app access, not an ordinary runtime permission.

### Warning and intervention behaviour

The intended focus workflow is:

1. Monitor selected apps during an active focus session.
2. Warn the user after the configured usage threshold.
3. If a second violation occurs, post a focus notification with a **Go to Home** action.

Android restricts applications from automatically opening activities over other apps. Therefore, SPARK does not claim that it can forcibly redirect the user or force-stop another app.

The companion does not use root access, Device Admin, AccessibilityService, screenshots, keystroke capture, or message-content monitoring.

Usage events and focus-session history remain on the device.

### Limitations

- Monitoring requires the appropriate access and foreground-service behaviour.
- Device-specific battery controls may interrupt monitoring.
- Scheduled session starts and daily limit enforcement are not implemented by the current starter implementation.
- Real-device testing is required before treating the companion as production-ready.
- Google Play compliance and distribution approval are not guaranteed.

Technical references:

- [Android UsageStatsManager](https://developer.android.com/reference/android/app/usage/UsageStatsManager)
- [Usage Access settings](https://developer.android.com/reference/android/provider/Settings#ACTION_USAGE_ACCESS_SETTINGS)
- [Background activity launch restrictions](https://developer.android.com/guide/components/activities/background-starts)
- [Foreground services](https://developer.android.com/develop/background-work/services/fgs/service-types)

---

## 🧪 Testing

Run the Python test suite from the repository root:

```powershell
python -m unittest discover -s tests
```

The tests cover selected NLP, reminder, WhatsApp parsing, privacy, and core regression behaviour, depending on the implementation and available dependencies.

### Excel helper

```powershell
python test_excel.py
```

Use an appropriate test workbook. Avoid running test operations against important personal records.

### Voice helper

```powershell
python test_voice.py
```

This requires supported microphone hardware and installed voice-recognition dependencies.

### Android unit tests

If the required Android SDK, JDK, and Gradle installation are available:

```powershell
cd android
gradle :app:testDebugUnitTest
```

Review the test output rather than assuming a successful build means every feature works.

The repository contains `QA_AUDIT_REPORT.md` for recorded findings, fixes, and test status. Check that report for the latest verified results.

---

## 🗂️ Configuration and Data Storage

SPARK uses local configuration and persistence for supported features.

| Data | Storage |
|---|---|
| Personal memory | Existing JSON memory store |
| Tasks | Existing JSON task store |
| Learned skills | Existing local skill registry |
| Reminder records | SQLite |
| WhatsApp review suggestions | SQLite |
| Android focus state/history | Local Android storage |

The exact path can vary between development and packaged execution.

### Excel configuration

The existing Excel marks functionality expects a workbook at:

```text
~/OneDrive/Documents/test.xlsx
```

with the expected columns:

```text
Name
Mark
```

Adjust the workbook or configure the supported path mechanism before using Excel-related commands.

### Timezone configuration

The default timezone is:

```text
Asia/Kolkata
```

Configure `SPARK_TIMEZONE` if a different timezone is required.

Do not commit personal data files, secret configuration, API tokens, private chat exports, or local environment files.

---

## 🔒 Security and Privacy

SPARK is designed to operate through validated tools and explicit permission boundaries.

### Existing safety restrictions

The following computer power operations are intentionally disabled:

- Shutdown.
- Restart.
- Lock.
- Sleep.
- Hibernate.
- Sign out.

Their required response is:

```text
I don't have computer power controls enabled.
```

SPARK should not provide unrestricted shell, PowerShell, CMD, or arbitrary Python execution.

Additional safeguards include:

- Use validated file-opening operations instead of trusting arbitrary file paths.
- Treat retrieved online content as untrusted.
- Validate user input and API payloads.
- Keep credentials out of source control.
- Avoid unnecessary collection of private data.
- Require approval for source-code modifications and sensitive capabilities.
- Use synthetic data when testing operations that could modify personal files.

Do not expose the local API to untrusted networks. The current local API setup does not provide authenticated LAN pairing.

---

## 🧰 Troubleshooting

### Python cannot find `main.py`

Make sure the terminal is in the actual project directory:

```powershell
cd "C:\Users\asus\OneDrive\Desktop\SPARK_project_structure\spark"
python main.py
```

If you cloned the repository into another location, use that directory instead.

### Python module is missing

Activate the virtual environment and install the project's requirements:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Voice input does not work

Check microphone availability, operating-system permissions, and the installed SpeechRecognition/PyAudio dependencies.

The text-based assistant should remain usable where voice is optional.

### Frontend cannot connect to the backend

Make sure the API is running:

```powershell
python -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

Then check the API and frontend configuration for the correct local address and port.

### Reminders do not arrive

Check that:
- The backend is running.
- The reminder exists in persistent storage.
- Its scheduled date, time, and timezone are correct.
- The application has not reported a scheduler or notification error.

Scheduled delivery is not guaranteed while the backend is stopped.

### Git opens an unexpected pager

Use `--no-pager` for commands that display lengthy diffs:

```powershell
git --no-pager status --short
git --no-pager diff --cached --name-status
```

### Build reports success but no executable exists

Verify that the build ran from the project root, that the required entry point exists, and that PyInstaller actually completed successfully. A success message alone does not verify that the executable was created.

---

## 🗺️ Roadmap

Potential future improvements include:

- More robust English/Tanglish intent understanding.
- Better typo tolerance and contextual follow-ups.
- Expanded automated regression tests.
- Improved diagnostics and safe self-learning.
- More reliable reminder delivery and notification handling.
- Secure authenticated mobile-to-PC pairing.
- Improved frontend usability and accessibility.
- Better packaging, installation, and update workflows.
- Additional Android device testing and reliability improvements.

Items in this roadmap are potential enhancements, not claims that they are already implemented.

---

## 🤝 Contributing

SPARK is an evolving personal-assistant project.

When proposing changes:

1. Inspect the existing implementation.
2. Keep changes focused and maintainable.
3. Preserve existing features and user data.
4. Add regression tests for defects.
5. Validate security-sensitive changes carefully.
6. Document environmental requirements and limitations.
7. Report actual test results.

## 📄 License

No license has been specified yet. Unless a license is added to the repository, do not assume that others have permission to redistribute or reuse the project's code.

## 👨‍💻 Author

**Madhankumar**

GitHub: [@Madhankumar3207](https://github.com/Madhankumar3207)

Project: [SPARK — Smart Personal Assistant](https://github.com/Madhankumar3207/SPARK-personal-assistant)

---

**SPARK — Understand. Assist. Remember. Improve Safely. ⚡**
