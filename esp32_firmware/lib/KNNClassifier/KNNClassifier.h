#ifndef KNN_CLASSIFIER_H
#define KNN_CLASSIFIER_H

#include <Arduino.h>
#include <vector>
#include <string>
#include "AudioProcessor.h"

#define MAX_SAMPLES 500
#define K_VALUE 5
#define MAX_LABEL_LENGTH 20

struct LabeledSample {
    AudioFeatures features;
    char label[MAX_LABEL_LENGTH];
    unsigned long timestamp;
};

class KNNClassifier {
private:
    std::vector<LabeledSample> training_data;
    int num_samples;
    
    float compute_distance(const AudioFeatures& a, const AudioFeatures& b);
    void normalize_features(AudioFeatures& features);
    
public:
    KNNClassifier();
    void initialize();
    bool add_sample(const AudioFeatures& features, const char* label);
    String classify(const AudioFeatures& features, float& confidence);
    int get_sample_count() const { return num_samples; }
    int get_label_count(const char* label);
    void clear_data();
    
    // Persistence functions
    bool save_to_storage();
    bool load_from_storage();
    
    // Data access for serialization
    const std::vector<LabeledSample>& get_training_data() const { return training_data; }
};

#endif
