# ESP32 Real-Time Noise Logger

**Author:** Dineth Perera

**License:** MIT License (see LICENSE file)

---
# ESP32 Noise Logger with Offline kNN Classifier

A complete system for real-time audio classification using an ESP32 microcontroller (offline k-Nearest Neighbors classifier) and a Python GUI for real-time monitoring and labeling.

---

## 🚀 Quick Start

1. Double-click `setup.bat` (first time only)
2. Double-click `run_gui.bat` (to launch GUI)
3. For full details, see [`HOW_TO_RUN.md`](HOW_TO_RUN.md)

---

## 📦 Features

### ESP32 Firmware
- High-quality audio processing (30 kHz sample rate)
- Real-time feature extraction (RMS, ZCR, Spectral Centroid, Band Energies, Spectral Flux)
- Offline kNN classifier with incremental learning
- Data persistence: saves dataset to ESP32 SPIFFS (non-volatile flash)
- Serial protocol for communication with desktop GUI

### Python GUI
- Real-time monitoring of audio features and classifications
- Interactive labeling (predefined/custom labels)
- Dataset management (save, load, clear via ESP32)
- Real-time feature visualization
- Communication log

---

## 💾 Data Logging & Storage

- **All labeled data is stored on the ESP32's internal SPIFFS flash** as `/classifier_data.bin`.
- Data is persistent: unplugging or rebooting the ESP32 does NOT erase the dataset.
- When the sample limit is reached, the oldest data is replaced by new samples.
- The Python GUI does NOT log data to your PC by default (can be added if needed).

---

## 🛠️ Hardware Requirements

- ESP32 development board (e.g., ESP32-DevKit, NodeMCU-32S)
- Capacitor (electret) microphone (e.g., MAX4466 breakout)
- USB cable for programming/serial
- (Optional) SD card module for extended storage

### Microphone Connections
```
Microphone     ESP32
VCC        ->  3.3V (or GPIO33 for controlled power)
GND        ->  GND
OUT        ->  GPIO34 (ADC1_CH6)
```
*Most electret microphones require a bias voltage (3.3V) and may have a built-in amplifier. MAX4466 is recommended.*

---

## 📋 How to Run

See [`HOW_TO_RUN.md`](HOW_TO_RUN.md) for full instructions.

---
# Run the automated setup
double-click setup.bat

# OR manually:
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the GUI
```bash
# Easy way:
double-click run_gui.bat

# OR manually:
.venv\Scripts\python.exe test_gui.py
```

### 3. ESP32 Firmware (Optional - GUI works standalone)
- Open `esp32_firmware` folder in PlatformIO
- Connect ESP32 via USB
- Upload firmware: `PlatformIO: Upload`

## Software Setup

### ESP32 Firmware

1. **Install PlatformIO**:
   - Install VS Code
   - Install PlatformIO extension

2. **Configure Hardware**:
   - The firmware is configured for capacitor/electret microphone on GPIO34
   - Optional: Enable GPIO33 for microphone power by setting `MIC_VCC_PIN`
   - Adjust `MIC_PIN` if using a different ADC pin

3. **Build and Upload**:
   ```bash
   cd esp32_firmware
   pio run -t upload
   pio device monitor
   ```

### Python GUI

1. **Install Python Dependencies**:
   ```bash
   cd python_gui
   pip install -r requirements.txt
   ```

2. **Run the GUI**:
   ```bash
   python noise_logger_gui.py
   ```

## Usage

### Initial Setup

1. **Flash ESP32**: Upload the firmware to your ESP32
2. **Connect Hardware**: Wire the capacitor microphone to GPIO34 (and optionally VCC to GPIO33)
3. **Start GUI**: Run the Python GUI application
4. **Connect**: Select the ESP32's COM port and click "Connect"

### Training the Classifier

1. **Generate Sounds**: Make or play different types of sounds
2. **Monitor Features**: Watch the real-time feature extraction in the GUI
3. **Label Sounds**: Click appropriate labels (traffic, machinery, human, background, other) or use custom labels
4. **Build Dataset**: Continue labeling various sounds to build a diverse training set
5. **Save Data**: Use "Save Dataset" to persist the training data

### Real-time Classification

Once you have labeled samples:
- The system will automatically classify incoming audio
- Classifications appear in real-time with confidence scores
- Feature plots show the evolution of audio characteristics
- All data is logged for analysis

## Serial Protocol

The ESP32 communicates via a simple text-based protocol:

### Commands (GUI → ESP32)
- `GET_STATUS` - Request system status
- `GET_FEATURES` - Request current features
- `LABEL:<label>` - Label current sound
- `CLEAR_DATA` - Clear all training data
- `SAVE_DATA` - Save data to storage
- `LOAD_DATA` - Load data from storage
- `GET_DATASET` - Get dataset information

### Responses (ESP32 → GUI)
- `FEATURES:rms,zcr,centroid,low,mid,high,flux,classification,confidence`
- `STATUS:samples,uptime,memory`
- `LABELED:label,total_samples`
- `DATASET:total,traffic,machinery,human,background,other`
- `OK:message` - Success confirmation
- `ERROR:message` - Error notification

## Configuration

### Audio Parameters
```cpp
#define SAMPLE_RATE 8000        // Sampling frequency
#define FRAME_SIZE 512          // Analysis frame size
#define OVERLAP_SIZE 256        // Frame overlap
#define CLASSIFICATION_INTERVAL 2000  // ms between classifications
```

### Classifier Parameters
```cpp
#define MAX_SAMPLES 500         // Maximum training samples
#define K_VALUE 5               // Number of nearest neighbors
```

## Features Extracted

1. **RMS (Root Mean Square)**: Overall energy/volume level
2. **ZCR (Zero Crossing Rate)**: Measure of frequency content
3. **Spectral Centroid**: "Center of mass" of the spectrum
4. **Band Energies**: Energy in low (0-1kHz), mid (1-2kHz), high (2-4kHz) frequency bands
5. **Spectral Flux**: Rate of change in spectral content

## File Structure

```
esp32_noise_logger/
├── esp32_firmware/
│   ├── src/
│   │   └── main.cpp                 # Main ESP32 application
│   ├── lib/
│   │   ├── AudioProcessor/          # Audio feature extraction
│   │   ├── KNNClassifier/           # Machine learning classifier
│   │   └── SerialProtocol/          # Communication handling
│   └── platformio.ini               # PlatformIO configuration
├── python_gui/
│   ├── noise_logger_gui.py          # Main GUI application
│   └── requirements.txt             # Python dependencies
└── README.md                        # This file
```

## Extending the System

### Adding New Features
1. Modify `AudioProcessor.h` to define new features
2. Implement extraction in `AudioProcessor.cpp`
3. Update `NUM_FEATURES` and feature comparison in `KNNClassifier.cpp`

### New Classification Labels
- Simply use them in the GUI - the system dynamically handles new labels
- Predefined labels can be modified in the GUI code

### Advanced ML Models
- Replace `KNNClassifier` with more sophisticated algorithms
- Consider neural networks for complex pattern recognition
- Implement feature selection and dimensionality reduction

### Data Analysis
- Export training data for offline analysis
- Implement confusion matrices and performance metrics
- Add spectrogram visualization for detailed analysis

## Troubleshooting

### Common Issues

1. **No Audio Input**:
   - Check microphone connections (VCC to 3.3V, GND to GND, OUT to GPIO34)
   - Verify the electret microphone has proper bias voltage
   - Test with oscilloscope or multimeter on GPIO34
   - Ensure microphone is not damaged

2. **Poor Classification**:
   - Ensure diverse training data
   - Check feature extraction quality
   - Adjust classifier parameters

3. **Serial Communication Issues**:
   - Verify correct COM port
   - Check baud rate (115200)
   - Ensure ESP32 is not in bootloader mode

4. **Memory Issues**:
   - Reduce `MAX_SAMPLES` if needed
   - Monitor heap usage
   - Consider using SD card for large datasets

### Debug Output

Enable debug output by modifying `platformio.ini`:
```ini
build_flags = 
    -DCORE_DEBUG_LEVEL=3
```

## Performance Notes

- **Sampling Rate**: 8kHz provides good balance of quality and processing speed
- **Frame Size**: 512 samples (~64ms) for real-time response
- **Memory Usage**: ~50KB for classifier data with 500 samples
- **Processing Time**: ~10ms per frame on ESP32 @ 240MHz

## License

This project is open source. Feel free to modify and extend for your needs.

## Contributing

Contributions welcome! Areas for improvement:
- Advanced feature extraction (MFCC, spectral roll-off)
- Better ML algorithms (SVM, neural networks)
- Enhanced GUI with spectrograms
- Mobile app interface
- IoT cloud integration
