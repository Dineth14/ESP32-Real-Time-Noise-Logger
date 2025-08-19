#include <Arduino.h>
#include <FS.h>
#include <SPIFFS.h>
#include "AudioProcessor.h"
#include "KNNClassifier.h"
#include "SerialProtocol.h"

// Pin definitions
#define MIC_PIN 34         // Analog microphone pin (capacitor/electret mic)
#define MIC_VCC_PIN 33     // Optional: Power pin for microphone (3.3V)
#define MIC_BIAS_ENABLE 1  // Enable bias voltage for electret microphone

// Audio configuration
#define SAMPLE_RATE 30000      // 30 kHz sampling rate (Nyquist: 15 kHz)
#define BUFFER_LEN 1024
#define CLASSIFICATION_INTERVAL 2000  // ms between classifications

// Digital filter parameters
#define HP_CUTOFF_HZ 150       // High-pass filter cutoff (remove DC and low-freq noise)
#define LP_CUTOFF_HZ 15000     // Low-pass filter cutoff (anti-aliasing)

// Global objects
AudioProcessor audio_processor;
KNNClassifier classifier;
SerialProtocol serial_protocol;

// Global variables for communication with SerialProtocol
AudioFeatures last_features;
String last_classification = "unknown";
float last_confidence = 0.0;
bool has_new_features = false;

// Timing variables
unsigned long last_classification_time = 0;
unsigned long last_status_print = 0;

// Audio buffer
int16_t audio_buffer[BUFFER_LEN];
bool use_analog_mic = true;  // Using capacitor/electret microphone

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("ESP32 Noise Logger Starting...");
    
    // Initialize SPIFFS
    if (!SPIFFS.begin(true)) {
        Serial.println("SPIFFS initialization failed");
    }
    
    // Initialize audio processor
    audio_processor.initialize();
    Serial.println("Audio processor initialized");
    
    // Initialize classifier
    classifier.initialize();
    
    // Try to load existing data
    if (classifier.load_from_storage()) {
        Serial.print("Loaded ");
        Serial.print(classifier.get_sample_count());
        Serial.println(" samples from storage");
    } else {
        Serial.println("No existing data found, starting fresh");
    }
    
    // Initialize serial protocol
    serial_protocol.initialize();
    
    // Initialize audio input
    init_analog_microphone();
    Serial.println("Capacitor microphone initialized on GPIO34");
    Serial.print("Sampling rate: ");
    Serial.print(SAMPLE_RATE);
    Serial.println(" Hz");
    Serial.print("High-pass filter: ");
    Serial.print(HP_CUTOFF_HZ);
    Serial.println(" Hz");
    Serial.print("Low-pass filter: ");
    Serial.print(LP_CUTOFF_HZ);
    Serial.println(" Hz");
    
    Serial.println("System ready for audio processing");
    Serial.println("Available commands: GET_STATUS, GET_FEATURES, LABEL:<label>, CLEAR_DATA, SAVE_DATA, LOAD_DATA");
}

void loop() {
    // Handle serial communication
    serial_protocol.handle_input();
    
    // Read audio samples from capacitor microphone
    read_analog_samples();
    
    // Process audio and classify periodically
    unsigned long current_time = millis();
    if (current_time - last_classification_time >= CLASSIFICATION_INTERVAL) {
        process_audio_frame();
        last_classification_time = current_time;
    }
    
    // Print status periodically
    if (current_time - last_status_print >= 10000) {  // Every 10 seconds
        print_system_status();
        last_status_print = current_time;
    }
}

void init_analog_microphone() {
    // Configure ADC for capacitor microphone
    analogReadResolution(12);  // 12-bit ADC resolution (0-4095)
    analogSetAttenuation(ADC_11db);  // For 3.3V reference, allows 0-3.3V input
    
    // Optional: Enable microphone power pin
    #if MIC_VCC_PIN > 0
    pinMode(MIC_VCC_PIN, OUTPUT);
    digitalWrite(MIC_VCC_PIN, HIGH);  // Provide 3.3V to microphone
    Serial.println("Microphone power enabled on GPIO33");
    #endif
    
    // Set up ADC characteristics for better accuracy
    analogSetPinAttenuation(MIC_PIN, ADC_11db);
    
    Serial.println("Capacitor microphone configured:");
    Serial.println("- GPIO34 (ADC1_CH6) for audio input");
    Serial.println("- 12-bit resolution (0-4095)");
    Serial.println("- 11dB attenuation (0-3.3V range)");
}

void read_analog_samples() {
    static unsigned long last_sample_time = 0;
    static int16_t dc_offset = 2048;  // Track DC offset for capacitor mic
    static int sample_count = 0;
    
    unsigned long sample_interval = 1000000 / SAMPLE_RATE;  // microseconds between samples (33.33 μs for 30kHz)
    
    if (micros() - last_sample_time >= sample_interval) {
        int analog_value = analogRead(MIC_PIN);
        
        // Adaptive DC offset removal for capacitor microphone
        if (sample_count < 2000) {
            // Learn DC offset during first 2000 samples (more samples for better DC estimation at higher rate)
            dc_offset = (dc_offset * sample_count + analog_value) / (sample_count + 1);
            sample_count++;
        }
        
        // Remove DC offset and convert to signed 16-bit
        int16_t sample = (analog_value - dc_offset) * 16;  // Scale up for better resolution
        
        // Digital filtering is now handled in AudioProcessor
        audio_processor.add_sample(sample);
        last_sample_time = micros();
    }
}

void process_audio_frame() {
    AudioFeatures features;
    
    if (audio_processor.extract_features(features)) {
        // Classify the features
        float confidence;
        String classification = classifier.classify(features, confidence);
        
        // Update global variables for serial communication
        last_features = features;
        last_classification = classification;
        last_confidence = confidence;
        has_new_features = true;
        
        // Send results via serial
        serial_protocol.send_classification_result(features, classification, confidence);
        
        // Reset audio buffer for next frame
        audio_processor.reset_buffer();
    }
}

void print_system_status() {
    Serial.println("=== System Status ===");
    Serial.print("Samples in dataset: ");
    Serial.println(classifier.get_sample_count());
    Serial.print("Free heap: ");
    Serial.println(ESP.getFreeHeap());
    Serial.print("Uptime: ");
    Serial.print(millis() / 1000);
    Serial.println(" seconds");
    
    if (has_new_features) {
        Serial.print("Last classification: ");
        Serial.print(last_classification);
        Serial.print(" (confidence: ");
        Serial.print(last_confidence * 100, 1);
        Serial.println("%)");
    }
    Serial.println("==================");
}
