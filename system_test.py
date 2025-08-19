#!/usr/bin/env python3
"""
Quick system test for ESP32 Noise Logger
Tests all major components without requiring hardware.
"""

import sys

def test_imports():
    """Test if all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import tkinter  # type: ignore[unused-import]
        print("  [OK] tkinter")
    except ImportError as e:
        print(f"  [FAIL] tkinter: {e}")
        return False
    
    try:
        import matplotlib.pyplot  # type: ignore[unused-import]
        print("  [OK] matplotlib")
    except ImportError as e:
        print(f"  [FAIL] matplotlib: {e}")
        return False
    
    try:
        import serial  # type: ignore[unused-import]
        print("  [OK] pyserial")
    except ImportError as e:
        print(f"  [FAIL] pyserial: {e}")
        return False
    
    try:
        import python_gui.noise_logger_gui  # type: ignore[unused-import]
        print("  [OK] noise_logger_gui")
    except ImportError as e:
        print(f"  [FAIL] noise_logger_gui: {e}")
        return False
    
    return True

def test_gui_creation():
    """Test if GUI can be created without errors."""
    print("\nTesting GUI creation...")
    
    try:
        import tkinter as tk
        from python_gui.noise_logger_gui import ESP32NoiseLoggerGUI
        root = tk.Tk()
        root.withdraw()  # Hide the window
        ESP32NoiseLoggerGUI(root)
        print("  [OK] GUI object created successfully")
        root.destroy()
        return True
    except Exception as e:
        print(f"  [FAIL] GUI creation failed: {e}")
        return False

def main():
    print("ESP32 Noise Logger - System Test")
    print("=" * 40)
    
    # Test imports
    if not test_imports():
        print("\n[RESULT] FAILED - Missing dependencies")
        print("Run: pip install -r requirements.txt")
        return 1
    
    # Test GUI creation
    if not test_gui_creation():
        print("\n[RESULT] FAILED - GUI creation error")
        return 1
    
    print("\n[RESULT] SUCCESS - All tests passed!")
    print("\nSystem is ready to use:")
    print("- Run GUI: python test_gui.py")
    print("- Or use: run_gui.bat")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
