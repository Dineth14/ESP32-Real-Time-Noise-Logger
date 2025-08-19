# ESP32 Real-Time Noise Logger - How to Run

**Author:** Dineth Perera

**License:** MIT License (see LICENSE file)

# ESP32 Noise Logger - How to Run

## 🚀 Quick Start (Easiest Method)

### Option 1: Using Batch Files (Windows)
1. **First Time Setup**: Double-click `setup.bat`
2. **Run the GUI**: Double-click `run_gui.bat`

### Option 2: Manual Commands
```bash
# First time setup
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Run the GUI
.venv\Scripts\python.exe test_gui.py
```

## 📋 Detailed Instructions

### Step 1: First Time Setup
**Option A: Automatic Setup**
- Double-click `setup.bat` file
- Wait for it to complete (creates virtual environment and installs packages)

**Option B: Manual Setup**
1. Open PowerShell or Command Prompt
2. Navigate to project folder:
   ```
   cd "d:\Projects files\New folder"
   ```
3. Create virtual environment:
   ```
   python -m venv .venv
   ```
4. Install packages:
   ```
   .venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

### Step 2: Run the Application
**Option A: Using Batch File**
- Double-click `run_gui.bat`

**Option B: Manual Command**
```
.venv\Scripts\python.exe test_gui.py
```

**Option C: Alternative Method**
```
.venv\Scripts\python.exe python_gui/noise_logger_gui.py
```

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
