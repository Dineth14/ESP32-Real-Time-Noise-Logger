@echo off
echo ==========================================
echo ESP32 Noise Logger - Setup Script
echo ==========================================
echo.

echo Creating Python virtual environment...
python -m venv .venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment. Make sure Python is installed.
    pause
    exit /b 1
)

echo.
echo Installing required packages...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip uninstall numpy matplotlib -y
".venv\Scripts\python.exe" -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo [ERROR] Failed to install packages.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Setup complete!
echo.
echo To run the GUI:
echo   - Double-click run_gui.bat
echo   - OR run: .venv\Scripts\python.exe test_gui.py
echo.
pause
