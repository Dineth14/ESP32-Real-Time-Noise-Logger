Noise Pollution Logger - Prototype

This repository contains a prototype pipeline for a noise pollution logger using an ESP32 with a capacitive microphone and a Python toolkit for signal processing, feature extraction, and ML training.

Structure
- python/
  - feature_extraction.py    # DSP helpers and feature extraction
  - train_and_export.py      # Synthetic dataset, training, and model export
  - requirements.txt         # Python dependencies
- esp32/
  - esp32_noise_logger.ino   # Arduino/ESP32 sketch to sample, filter, extract features and stream them

Quick start (Python)
1. Create a virtual environment and install dependencies from `python/requirements.txt`.
2. Use `python/train_and_export.py` to generate a synthetic dataset, train a classifier, and export it.

Quick start (ESP32)
1. Open `esp32/esp32_noise_logger.ino` in Arduino IDE or PlatformIO.
2. Install required libraries: arduinoFFT (or built-in FFT replacement), and any I2S/ADC helpers as noted.
3. Upload to an ESP32 and open Serial Monitor at 115200 baud to see feature JSON lines.

Notes
- The Python toolkit is useful for offline experimentation, producing models and porting simple rule-based or tree models to the ESP32.
- For production on-device inference, convert the model to a tiny format (decision tree rules, or TensorFlow Lite Micro) and ensure memory fits the target.

See `python/` for detailed usage.
