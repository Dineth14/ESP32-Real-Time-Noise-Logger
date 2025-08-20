#include "SerialProtocol.h"

// External references (to be defined in main.cpp)
extern KNNClassifier classifier;
extern AudioFeatures last_features;
extern String last_classification;
extern float last_confidence;
extern bool has_new_features;

SerialProtocol::SerialProtocol() {
    input_buffer = "";
}

void SerialProtocol::initialize() {
    Serial.begin(115200);
    input_buffer.reserve(100);
    
    // Send initialization message
    Serial.println("ESP32_NOISE_LOGGER_READY");
    delay(100);
}

void SerialProtocol::handle_input() {
    while (Serial.available()) {
        char c = Serial.read();
        
        if (c == '\n' || c == '\r') {
            if (input_buffer.length() > 0) {
                process_command(input_buffer);
                input_buffer = "";
            }
        } else {
            input_buffer += c;
        }
    }
}

void SerialProtocol::process_command(String& command) {
    command.trim();
    
    if (command == "GET_STATUS") {
        send_status();
    }
    else if (command == "GET_FEATURES") {
        if (has_new_features) {
            send_features(last_features, last_classification, last_confidence);
        } else {
            send_error("No features available");
        }
    }
    else if (command.startsWith("LABEL:")) {
        String label = command.substring(6);
        if (label.length() > 0 && has_new_features) {
            if (classifier.add_sample(last_features, label.c_str())) {
                send_label_confirmation(label.c_str());
                // Send updated dataset info after successful labeling
                send_dataset_info();
            } else {
                send_error("Failed to add sample");
            }
        } else {
            send_error("Invalid label or no features available");
        }
    }
    else if (command == "CLEAR_DATA") {
        classifier.clear_data();
        Serial.println("OK:DATA_CLEARED");
    }
    else if (command == "SAVE_DATA") {
        if (classifier.save_to_storage()) {
            Serial.println("OK:DATA_SAVED");
        } else {
            send_error("Failed to save data");
        }
    }
    else if (command == "LOAD_DATA") {
        if (classifier.load_from_storage()) {
            Serial.println("OK:DATA_LOADED");
        } else {
            send_error("Failed to load data");
        }
    }
    else if (command == "GET_DATASET") {
        send_dataset_info();
    }
    else {
        send_error("Unknown command: " + command);
    }
}

void SerialProtocol::send_features(const AudioFeatures& features, const String& classification, float confidence) {
    Serial.print("FEATURES:");
    Serial.print(features.rms, 4);
    Serial.print(",");
    Serial.print(features.zcr, 4);
    Serial.print(",");
    Serial.print(features.spectral_centroid, 2);
    Serial.print(",");
    Serial.print(features.low_energy, 4);
    Serial.print(",");
    Serial.print(features.mid_energy, 4);
    Serial.print(",");
    Serial.print(features.high_energy, 4);
    Serial.print(",");
    Serial.print(features.spectral_flux, 4);
    Serial.print(",");
    Serial.print(classification);
    Serial.print(",");
    Serial.println(confidence, 3);
}

void SerialProtocol::send_status() {
    Serial.print("STATUS:");
    Serial.print(classifier.get_sample_count());
    Serial.print(",");
    Serial.print(millis());
    Serial.print(",");
    Serial.println(ESP.getFreeHeap());
}

void SerialProtocol::send_dataset_info() {
    Serial.print("DATASET:");
    Serial.print(classifier.get_sample_count());
    Serial.print(",");
    
    // Count samples by label
    const char* labels[] = {"traffic", "machinery", "human", "background", "other"};
    for (int i = 0; i < 5; i++) {
        Serial.print(classifier.get_label_count(labels[i]));
        if (i < 4) Serial.print(",");
    }
    Serial.println();
}

void SerialProtocol::send_classification_result(const AudioFeatures& features, const String& classification, float confidence) {
    send_features(features, classification, confidence);
}

void SerialProtocol::send_label_confirmation(const char* label) {
    Serial.print("LABELED:");
    Serial.print(label);
    Serial.print(",");
    Serial.println(classifier.get_sample_count());
}

void SerialProtocol::send_error(const String& error) {
    Serial.print("ERROR:");
    Serial.println(error);
}
