ESP32 Integration - Final instructions

Files of interest:
- `esp32_noise_logger.ino` - main sketch (prints JSON lines with features and class)
- `tree_classifier.h` - auto-generated from Python (full-featured tree)
- `tree_classifier_ondevice.h` - auto-generated compact tree using only on-device features

Steps to use
1. Build & flash
   - Open `esp32_noise_logger.ino` in Arduino IDE or PlatformIO.
   - Ensure `ArduinoJson` is installed. Optionally install `arduinoFFT` if you implement FFT.
   - Select your ESP32 board and upload.

2. Start local server
   - In `python/` run `python server.py` to start the Flask ingest server on port 5000.

3. Run serial bridge
   - Identify your COM port (Windows Device Manager).
   - Run: `python serial_bridge.py --port COM3 --baud 115200` (replace COM3).

4. View stats
   - Open http://localhost:5000/stats to see recent classes and counts.

Notes
- The on-device classifier expects features in order: rms, zcr, band_energy_low, band_energy_mid, band_energy_high
- The sketch currently computes only rms and zcr; compute spectral features on-device with `arduinoFFT` or IIR banks for proper inference.
