#ifndef SERIAL_PROTOCOL_H
#define SERIAL_PROTOCOL_H

#include <Arduino.h>
#include "AudioProcessor.h"
#include "KNNClassifier.h"

class SerialProtocol {
private:
    String input_buffer;
    void process_command(String& command);
    void send_features(const AudioFeatures& features, const String& classification, float confidence);
    void send_dataset_info();
    
public:
    SerialProtocol();
    void initialize();
    void handle_input();
    void send_status();
    void send_classification_result(const AudioFeatures& features, const String& classification, float confidence);
    void send_label_confirmation(const char* label);
    void send_error(const String& error);
};

// Commands:
// GET_STATUS - Get system status
// GET_FEATURES - Request current features
// LABEL:<label> - Label current sound
// CLEAR_DATA - Clear all training data
// SAVE_DATA - Save data to storage
// LOAD_DATA - Load data from storage
// GET_DATASET - Get dataset information

#endif
