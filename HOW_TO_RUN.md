# ESP32 Real-Time Noise Logger - How to Run

**Author:** Dineth Perera

**License:** MIT License (see LICENSE file)


# ESP32 Noise Logger - How to Run

---

## 🚀 Quick Start

### 1. Python GUI (Windows)
1. Double-click `setup.bat` (first time only)
2. Double-click `run_gui.bat` to launch the GUI

### 2. Python GUI (Manual/Other OS)
```powershell
# First time setup
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
# Run the GUI
.venv\Scripts\python.exe test_gui.py
```

---

## �️ Uploading ESP32 Firmware

1. Open the `esp32_firmware` folder in VS Code with PlatformIO extension installed.
2. Connect your ESP32 board via USB.
3. Click the "Upload" button in PlatformIO (checkmark icon) to build and upload the firmware.
4. Open the PlatformIO Serial Monitor (baud: 115200) to view ESP32 output.

---

## 💾 Data Logging & Storage

- All labeled data is stored on the ESP32's SPIFFS flash as `/classifier_data.bin`.
- Data is persistent across power cycles and unplugging.
- When the sample limit is reached, oldest data is replaced by new samples.
- The Python GUI does not log data to your PC by default.

---

## ❓ FAQ

**Q: How do I close the GUI?**
A: Click the X (close) button on the GUI window.

**Q: Do I need Arduino IDE?**
A: No, use PlatformIO in VS Code for firmware upload.

**Q: Where is my data stored?**
A: On the ESP32's internal flash (SPIFFS), not on your PC.

**Q: Will my data be lost if I unplug the ESP32?**
A: No, data is persistent unless you clear it or re-flash/erase the ESP32.

---

## 🔧 Troubleshooting

### Problem: "Python is not recognized"
**Solution**: Install Python from [python.org](https://python.org) and add to PATH

### Problem: NumPy compatibility errors
**Solution**: Already fixed in requirements.txt (uses numpy<2.0)

### Problem: Virtual environment issues
**Solution**: Delete `.venv` folder and run `setup.bat` again

### Problem: Import errors
**Solution**: 
1. Run `setup.bat` to reinstall packages
2. Make sure you're using `.venv\Scripts\python.exe`

## 📁 Project Structure
```
ESP32 Noise Logger/
├── setup.bat              # First-time setup script
├── run_gui.bat            # GUI launcher script
├── test_gui.py           # GUI test launcher
├── system_test.py        # System compatibility test
├── requirements.txt      # Python dependencies
├── .venv/               # Python virtual environment
├── python_gui/          # GUI source code
└── esp32_firmware/      # ESP32 code (optional)
```

## 🎯 What Each File Does

- **`setup.bat`**: Creates Python environment and installs all required packages
- **`run_gui.bat`**: Launches the GUI application
- **`test_gui.py`**: Python script that starts the GUI
- **`system_test.py`**: Tests if all components are working
- **`requirements.txt`**: List of Python packages needed

## 📱 Using the GUI

1. **Connection Tab**: Select COM port and connect to ESP32 (optional)
2. **Features Tab**: View real-time audio features
3. **Classification Tab**: See sound classifications
4. **Labeling**: Click buttons to label sounds for training
5. **Dataset**: Save/load training data
6. **Visualization**: Real-time plots of audio features

## 🔗 ESP32 Setup (Optional)

The GUI works standalone for testing. To use with ESP32:

1. Open `esp32_firmware` folder in PlatformIO
2. Connect ESP32 via USB
3. Upload firmware: `PlatformIO: Upload`
4. Connect microphone to GPIO34
5. Use GUI to connect via serial port

## ✅ Verification

Run this command to test everything works:
```
.venv\Scripts\python.exe system_test.py
```

You should see:
```
[RESULT] SUCCESS - All tests passed!
```

## 🆘 Need Help?

1. **First**: Try running `setup.bat`
2. **Third**: Run `system_test.py` to diagnose issues
3. **Last**: Check `NUMPY_FIX.md` for compatibility issues

## 🎉 Success!

When working correctly, you'll see:
```
[SUCCESS] GUI module imported successfully!
[LAUNCH] Starting GUI...
```

And a window with the ESP32 Noise Logger interface will appear!
