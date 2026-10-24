@echo off
setlocal
cd /d "%~dp0"

if not exist "main.py" (
    echo ERROR: main.py was not found in %CD%.
    exit /b 1
)
if not exist "gui_main.py" (
    echo ERROR: gui_main.py was not found in %CD%.
    exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: .venv\Scripts\python.exe was not found. Create the project virtual environment first.
    exit /b 1
)

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Dependency installation failed.
    exit /b 1
)

if exist "build" rmdir /s /q "build"
if errorlevel 1 (
    echo ERROR: Could not clean build directory.
    exit /b 1
)
if exist "dist" rmdir /s /q "dist"
if errorlevel 1 (
    echo ERROR: Could not clean dist directory.
    exit /b 1
)

".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name SPARK --paths "%CD%" --hidden-import speech_recognition --hidden-import openpyxl gui_main.py
if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    exit /b 1
)
if not exist "dist\SPARK.exe" (
    echo ERROR: PyInstaller returned success but dist\SPARK.exe is missing.
    exit /b 1
)

echo SUCCESS: %CD%\dist\SPARK.exe
exit /b 0
