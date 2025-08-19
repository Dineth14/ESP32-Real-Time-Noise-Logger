#!/usr/bin/env python3
"""
Test script to verify the ESP32 Noise Logger GUI works correctly.
This script will launch the GUI without requiring an ESP32 connection.
"""

import sys
import os

# Add the python_gui directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python_gui'))

try:
    # Import the GUI module from the python_gui directory
    import python_gui.noise_logger_gui as gui
    print("[SUCCESS] GUI module imported successfully!")
    print("[LAUNCH] Starting GUI...")
    gui.main()
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    print("Please make sure all required packages are installed:")
    print("pip install matplotlib pyserial")
    print("Run: pip install -r requirements.txt")
except Exception as e:
    print(f"[ERROR] Error launching GUI: {e}")
