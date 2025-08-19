# ESP32 Real-Time Noise Logger - Visual Flow

**Author:** Dineth Perera

**License:** MIT License (see LICENSE file)

# ESP32 Noise Logger - Visual System Flow

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ESP32 NOISE LOGGER SYSTEM                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  HARDWARE   │ ── │   SIGNAL     │ ── │  MACHINE    │ ── │   OUTPUT    │  │
│  │   LAYER     │    │  PROCESSING  │    │  LEARNING   │    │    LAYER    │  │
│  └─────────────┘    └──────────────┘    └─────────────┘    └─────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Detailed System Flow Diagram

### 1. Audio Capture Chain
```
🎤 Sound Wave
    │
    ▼
┌─────────────────┐
│ Capacitor Mic   │ ◄── 3.3V Bias Voltage
│ (Electret)      │
└─────────┬───────┘
          │ AC Signal (0.1-3.0V)
          ▼
┌─────────────────┐
│   ESP32 ADC     │ ◄── 12-bit Resolution
│   GPIO34        │      0-4095 counts
└─────────┬───────┘      30kHz sampling
          │ Digital Values
          ▼
┌─────────────────┐
│ Sample Rate     │ ◄── 33.33μs intervals
│ Controller      │      Interrupt driven
└─────────┬───────┘
          │
          ▼
```

### 2. Digital Signal Processing Pipeline
```
Raw ADC Sample (12-bit)
          │
          ▼
┌─────────────────┐
│  DC Offset      │ ◄── Learn DC bias first 2000 samples
│  Removal        │     Center signal around zero
└─────────┬───────┘
          │ Centered Signal
          ▼
┌─────────────────┐
│  High-Pass      │ ◄── 150Hz cutoff
│  Filter         │     Remove low-freq noise
└─────────┬───────┘     y[n] = α(y[n-1] + x[n] - x[n-1])
          │ Filtered Signal
          ▼
┌─────────────────┐
│  Low-Pass       │ ◄── 15kHz cutoff
│  Filter         │     Anti-aliasing
└─────────┬───────┘     y[n] = αx[n] + (1-α)y[n-1]
          │ Clean Signal
          ▼
┌─────────────────┐
│ Circular Buffer │ ◄── 1024 samples (34ms)
│ Storage         │     Overwrite oldest
└─────────┬───────┘
          │ Frame Ready (1024 samples)
          ▼
```

### 3. Feature Extraction Process
```
Complete Audio Frame (1024 samples)
          │
          ▼
┌─────────────────┐
│ Hamming Window  │ ◄── Reduce spectral leakage
│ Application     │     w[n] = 0.54 - 0.46*cos(2πn/N)
└─────────┬───────┘
          │ Windowed Frame
          ├─────────────────────┬─────────────────────┐
          ▼                     ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   TIME DOMAIN   │   │ FREQUENCY DOMAIN│   │   SPECTRAL      │
│   FEATURES      │   │   PROCESSING    │   │   FEATURES      │
└─────────┬───────┘   └─────────┬───────┘   └─────────┬───────┘
          │                     │                     │
          ▼                     ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ 1. RMS Energy   │   │ Fast Fourier    │   │ 4. Spectral     │
│    √(Σx²/N)     │   │ Transform (FFT) │   │    Centroid     │
│                 │   │ 1024→512 bins   │   │ Σ(f*E)/Σ(E)    │
│ 2. Zero Cross   │   │ 0-15kHz range   │   │                 │
│    Rate (ZCR)   │   │                 │   │ 5-7. Band       │
│    Σ(sign Δ)    │   │                 │   │     Energies    │
└─────────────────┘   └─────────┬───────┘   │ Low: 0-2kHz     │
                                │           │ Mid: 2-6kHz     │
                                ▼           │ High: 6-15kHz   │
                      ┌─────────────────┐   │                 │
                      │ Magnitude       │   │ 8. Spectral     │
                      │ Spectrum        │   │    Flux         │
                      │ 512 bins        │   │ Σ(positive Δ)   │
                      └─────────────────┘   └─────────────────┘
                                │
                                ▼
                      ┌─────────────────────────────────────┐
                      │        FEATURE VECTOR               │
                      │ [RMS, ZCR, Centroid, Low, Mid,     │
                      │  High, Flux] = 7 dimensions        │
                      └─────────────────┬───────────────────┘
                                        │
                                        ▼
```

### 4. Machine Learning Classification
```
Feature Vector [7D]
          │
          ▼
┌─────────────────┐
│   Training      │ ◄── Stored in SPIFFS flash
│   Database      │     Labeled feature vectors
└─────────┬───────┘     JSON format
          │ Compare with all stored samples
          ▼
┌─────────────────┐
│   Distance      │ ◄── Euclidean distance
│  Calculation    │     d = √Σ(fi - ti)²
└─────────┬───────┘     i = 1 to 7 features
          │ Distance array
          ▼
┌─────────────────┐
│   K-Nearest     │ ◄── K=3 (configurable)
│   Neighbors     │     Sort by distance
└─────────┬───────┘     Take closest K samples
          │ K closest samples
          ▼
┌─────────────────┐
│   Majority      │ ◄── Count votes per label
│    Voting       │     Winner = most votes
└─────────┬───────┘     Confidence = votes/K
          │ Classification + Confidence
          ▼
┌─────────────────┐
│   Result        │ ◄── Label string + score
│   Output        │     e.g., "traffic" 85%
└─────────┬───────┘
          │
          ▼
```

### 5. Communication and Output
```
Classification Result
          │
          ▼
┌─────────────────┐
│   Serial        │ ◄── Format: "FEATURES:1.2,0.3,..."
│   Protocol      │     115200 baud UART
└─────────┬───────┘     ASCII text protocol
          │ Serial data stream
          ▼
┌─────────────────┐
│   USB Cable     │ ◄── ESP32 ↔ Computer
│   Connection    │     Virtual COM port
└─────────┬───────┘
          │ USB Serial
          ▼
┌─────────────────┐
│   Python GUI    │ ◄── Real-time display
│   Application   │     Matplotlib graphs
└─────────┬───────┘     User interaction
          │
          ▼
┌─────────────────┐
│   User          │ ◄── Label sounds for training
│   Interface     │     View classifications
└─────────────────┘     Monitor system status
```

## Timing Diagram

### Real-time Processing Timeline
```
Time (ms):  0    10    20    30    34    35    36    ∞
            │     │     │     │     │     │     │     │
Sampling:   ████████████████████████▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
            │◄──── Collect 1024 samples ──►│
                                           │
Processing:                                 ███▓▓▓▓▓▓▓▓
                                           │◄─►│
                                           FFT  Features
                                                │
Classification:                                 ██▓▓▓▓▓▓
                                                │◄►│
                                                k-NN
                                                   │
Serial Out:                                       █▓▓▓▓▓
                                                  │◄►│
                                                  TX

Legend: ████ Active Processing    ▓▓▓▓ Idle Time
```

### Processing Load Distribution
```
┌─────────────────────────────────────────────────────────────┐
│                    ESP32 CPU UTILIZATION                   │
├─────────────────────────────────────────────────────────────┤
│ Sampling (30kHz):     ██████████████████ 60%              │
│ Digital Filtering:    ████████ 25%                        │
│ Feature Extraction:   ██████ 20%                          │
│ Classification:       ████ 12%                            │
│ Serial Communication: ██ 8%                               │
│ System Overhead:      ██ 5%                               │
├─────────────────────────────────────────────────────────────┤
│ TOTAL CPU USAGE:      ████████████████████████████ 70%    │
│ REMAINING CAPACITY:   ████████████ 30%                    │
└─────────────────────────────────────────────────────────────┘
```

## Memory Layout Diagram

### ESP32 Memory Map
```
┌─────────────────────────────────────────────────────────────┐
│                    ESP32 MEMORY USAGE                      │
├─────────────────────────────────────────────────────────────┤
│ FLASH MEMORY (4MB):                                        │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Bootloader:        ████ 32KB                           │ │
│ │ Partition Table:   █ 4KB                               │ │
│ │ Application Code:  ████████████████████████ 100KB      │ │
│ │ SPIFFS Storage:    ████████████████████████████ 128KB  │ │
│ │ Free Flash:        ████████████████████████████████... │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ RAM MEMORY (320KB):                                        │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ System/WiFi:       ████████████ 48KB                   │ │
│ │ Application Stack: ████████ 32KB                       │ │
│ │ Audio Buffers:     ████ 16KB                           │ │
│ │ Training Data:     ████ 16KB                           │ │
│ │ Free RAM:          ████████████████████████████████.... │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Data Structure Flow

### Audio Data Journey
```
Raw Sound → ADC Values → Filtered Samples → Audio Frame → Features → Classification

uint16_t     int16_t      float           vector<float>   struct      string
[0-4095]     [-32768,     [-1.0, +1.0]   [1024 samples]  {7 floats}  "traffic"
12-bit       +32767]      normalized      34ms window     features    + confidence
```

### Feature Vector Structure
```
AudioFeatures {
    float rms;              // Energy: 0.0 - 1.0
    float zcr;              // Rate: 0.0 - 1.0  
    float spectral_centroid; // Hz: 0 - 15000
    float low_energy;       // Energy: 0.0 - 1.0
    float mid_energy;       // Energy: 0.0 - 1.0
    float high_energy;      // Energy: 0.0 - 1.0
    float spectral_flux;    // Change: 0.0 - 1.0
}
```

## State Machine Diagram

### System States
```
         ┌─────────────┐
         │   STARTUP   │
         └──────┬──────┘
                │ Initialize hardware
                ▼
         ┌─────────────┐
         │    INIT     │ ◄── Load training data
         └──────┬──────┘     Setup filters
                │ Ready
                ▼
    ┌─────────────────────┐
    │      SAMPLING       │ ◄─┐
    │   (Continuous)      │   │
    └──────┬──────────────┘   │
           │ Frame complete   │
           ▼                  │
    ┌─────────────────────┐   │
    │    PROCESSING       │   │
    │  (Feature Extract)  │   │
    └──────┬──────────────┘   │
           │ Features ready   │
           ▼                  │
    ┌─────────────────────┐   │
    │  CLASSIFICATION     │   │
    │    (k-NN Predict)   │   │
    └──────┬──────────────┘   │
           │ Result ready     │
           ▼                  │
    ┌─────────────────────┐   │
    │      OUTPUT         │   │
    │   (Serial Send)     │   │
    └──────┬──────────────┘   │
           │ Continue         │
           └──────────────────┘

States can be interrupted by:
- Serial commands (LABEL, SAVE, etc.)
- Error conditions
- System reset
```

## Interactive GUI Flow

### Python GUI Data Flow
```
ESP32 Serial → Python Thread → Queue → GUI Update → User Display

┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ Serial Port │──▶│ Reader      │──▶│ Data Queue  │──▶│ GUI Thread  │
│ (115200)    │   │ Thread      │   │ (Thread     │   │ (tkinter)   │
│             │   │ (Background)│   │  Safe)      │   │             │
└─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
                                                               │
                                                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        GUI COMPONENTS                              │
├─────────────────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│ │ Feature     │ │ Real-time   │ │ Classification│ │ Control     │   │
│ │ Display     │ │ Plots       │ │ History     │ │ Buttons     │   │
│ │ (Labels)    │ │ (matplotlib)│ │ (Listbox)   │ │ (Commands)  │   │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                   │
User Actions:                      ▼
- Label sounds ──────────▶ Send "LABEL:traffic"
- Save data ─────────────▶ Send "SAVE_DATA"  
- Clear data ────────────▶ Send "CLEAR_DATA"
                          │
                          ▼
                   ESP32 Serial Input
```

This comprehensive visual flow shows exactly how every component of the ESP32 Noise Logger system works together, from sound waves to final classification output!