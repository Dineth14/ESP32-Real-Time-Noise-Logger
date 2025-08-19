#include "KNNClassifier.h"
#include <FS.h>
#include <SPIFFS.h>
#include <algorithm>
#include <map>

KNNClassifier::KNNClassifier() : num_samples(0) {
    training_data.reserve(MAX_SAMPLES);
}

void KNNClassifier::initialize() {
    num_samples = 0;
    training_data.clear();
    
    // Initialize SPIFFS if not already done
    if (!SPIFFS.begin(true)) {
        Serial.println("SPIFFS initialization failed");
    }
}

bool KNNClassifier::add_sample(const AudioFeatures& features, const char* label) {
    if (num_samples >= MAX_SAMPLES) {
        // Remove oldest sample to make room
        training_data.erase(training_data.begin());
        num_samples--;
    }
    
    LabeledSample sample;
    sample.features = features;
    strncpy(sample.label, label, MAX_LABEL_LENGTH - 1);
    sample.label[MAX_LABEL_LENGTH - 1] = '\0';
    sample.timestamp = millis();
    
    training_data.push_back(sample);
    num_samples++;
    
    return true;
}

String KNNClassifier::classify(const AudioFeatures& features, float& confidence) {
    if (num_samples == 0) {
        confidence = 0.0;
        return "unknown";
    }
    
    // Calculate distances to all training samples
    std::vector<std::pair<float, int>> distances;
    
    for (int i = 0; i < num_samples; i++) {
        float dist = compute_distance(features, training_data[i].features);
        distances.push_back({dist, i});
    }
    
    // Sort by distance
    std::sort(distances.begin(), distances.end());
    
    // Count votes from k nearest neighbors
    std::map<String, int> votes;
    int k = std::min(K_VALUE, num_samples);
    
    for (int i = 0; i < k; i++) {
        String label = String(training_data[distances[i].second].label);
        votes[label]++;
    }
    
    // Find most voted label
    String best_label = "unknown";
    int max_votes = 0;
    for (auto& pair : votes) {
        if (pair.second > max_votes) {
            max_votes = pair.second;
            best_label = pair.first;
        }
    }
    
    confidence = (float)max_votes / k;
    return best_label;
}

float KNNClassifier::compute_distance(const AudioFeatures& a, const AudioFeatures& b) {
    // Euclidean distance with feature normalization
    float dist = 0;
    
    dist += pow(a.rms - b.rms, 2);
    dist += pow(a.zcr - b.zcr, 2);
    dist += pow((a.spectral_centroid - b.spectral_centroid) / 1000.0, 2); // Normalize by 1000
    dist += pow(a.low_energy - b.low_energy, 2);
    dist += pow(a.mid_energy - b.mid_energy, 2);
    dist += pow(a.high_energy - b.high_energy, 2);
    dist += pow(a.spectral_flux - b.spectral_flux, 2);
    
    return sqrt(dist);
}

int KNNClassifier::get_label_count(const char* label) {
    int count = 0;
    for (int i = 0; i < num_samples; i++) {
        if (strcmp(training_data[i].label, label) == 0) {
            count++;
        }
    }
    return count;
}

void KNNClassifier::clear_data() {
    training_data.clear();
    num_samples = 0;
}

bool KNNClassifier::save_to_storage() {
    File file = SPIFFS.open("/classifier_data.bin", "w");
    if (!file) {
        return false;
    }
    
    // Write number of samples
    file.write((uint8_t*)&num_samples, sizeof(num_samples));
    
    // Write all samples
    for (int i = 0; i < num_samples; i++) {
        file.write((uint8_t*)&training_data[i], sizeof(LabeledSample));
    }
    
    file.close();
    return true;
}

bool KNNClassifier::load_from_storage() {
    File file = SPIFFS.open("/classifier_data.bin", "r");
    if (!file) {
        return false;
    }
    
    // Read number of samples
    file.read((uint8_t*)&num_samples, sizeof(num_samples));
    
    // Validate and limit number of samples
    if (num_samples > MAX_SAMPLES) {
        num_samples = MAX_SAMPLES;
    }
    
    // Read samples
    training_data.clear();
    training_data.resize(num_samples);
    
    for (int i = 0; i < num_samples; i++) {
        file.read((uint8_t*)&training_data[i], sizeof(LabeledSample));
    }
    
    file.close();
    return true;
}
