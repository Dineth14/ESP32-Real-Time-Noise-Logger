#ifndef AUDIO_PROCESSOR_H
#define AUDIO_PROCESSOR_H

#include <Arduino.h>
#include <vector>
#include <math.h>

#ifndef SAMPLE_RATE
#define SAMPLE_RATE 30000    // 30 kHz sampling rate as per VISUAL_FLOW.md
#endif
#define FRAME_SIZE 1024      // 1024 samples frame size as per VISUAL_FLOW.md
#define NUM_FEATURES 7

struct AudioFeatures {
    float rms;           // Root Mean Square
    float zcr;           // Zero Crossing Rate  
    float spectral_centroid;
    float low_energy;    // 0-2000 Hz (0-2kHz as per VISUAL_FLOW.md)
    float mid_energy;    // 2000-6000 Hz (2-6kHz as per VISUAL_FLOW.md)
    float high_energy;   // 6000-15000 Hz (6-15kHz as per VISUAL_FLOW.md)
    float spectral_flux;
};

class AudioProcessor {
private:
    std::vector<float> window;
    std::vector<float> prev_spectrum;
    std::vector<int16_t> audio_buffer;
    int buffer_index;
    
    // Digital filters as per VISUAL_FLOW.md
    float high_pass_prev_input;
    float high_pass_prev_output;
    float low_pass_prev_output;
    
    void apply_hamming_window(std::vector<float>& frame);
    void compute_fft(std::vector<float>& frame, std::vector<float>& spectrum);
    float compute_rms(const std::vector<float>& frame);
    float compute_zcr(const std::vector<float>& frame);
    float compute_spectral_centroid(const std::vector<float>& spectrum);
    void compute_band_energies(const std::vector<float>& spectrum, float& low, float& mid, float& high);
    float compute_spectral_flux(const std::vector<float>& spectrum);
    float apply_high_pass_filter(float input);  // 150Hz cutoff
    float apply_low_pass_filter(float input);   // 15kHz cutoff
public:
    AudioProcessor();
    void initialize();
    void add_sample(int16_t sample);
    bool extract_features(AudioFeatures& features);
    void reset_buffer();
};

#endif
