@echo off
echo Installing Python GUI dependencies...
cd python_gui
pip install -r requirements.txt
echo.
echo Dependencies installed!
echo Run: python noise_logger_gui.py
pause
