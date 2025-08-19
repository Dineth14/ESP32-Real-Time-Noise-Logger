#ifndef AUDIO_PROCESSOR_H
#define AUDIO_PROCESSOR_H

#include <Arduino.h>
#include <vector>
#include <math.h>

#ifndef SAMPLE_RATE
#define SAMPLE_RATE 30000     // 30 kHz sampling rate
#endif
#define FRAME_SIZE 1024       // Increased frame size for better frequency resolution
#define OVERLAP_SIZE 512
#define NUM_FEATURES 7

// Digital filter parameters
#define HP_CUTOFF_HZ 150      // High-pass filter cutoff
#define LP_CUTOFF_HZ 15000    // Low-pass filter cutoff

struct AudioFeatures {
    float rms;           // Root Mean Square
    float zcr;           // Zero Crossing Rate  
    float spectral_centroid;
    float low_energy;    // 0-1000 Hz
    float mid_energy;    // 1000-2000 Hz
    float high_energy;   // 2000-4000 Hz
    float spectral_flux;
};

class AudioProcessor {
private:
    std::vector<float> window;
    std::vector<float> prev_spectrum;
    std::vector<int16_t> audio_buffer;
    int buffer_index;
    
    // Digital filter state variables
    float hp_prev_input, hp_prev_output;   // High-pass filter
    float lp_prev_input, lp_prev_output;   // Low-pass filter
    float hp_alpha, lp_alpha;              // Filter coefficients
    
    void apply_hamming_window(std::vector<float>& frame);
    void compute_fft(std::vector<float>& frame, std::vector<float>& spectrum);
    float compute_rms(const std::vector<float>& frame);
    float compute_zcr(const std::vector<float>& frame);
    float compute_spectral_centroid(const std::vector<float>& spectrum);
    void compute_band_energies(const std::vector<float>& spectrum, float& low, float& mid, float& high);
    float compute_spectral_flux(const std::vector<float>& spectrum);
    
    // Digital filtering functions
    float apply_high_pass_filter(float input);
    float apply_low_pass_filter(float input);
    
public:
    AudioProcessor();
    void initialize();
    void add_sample(int16_t sample);
    bool extract_features(AudioFeatures& features);
    void reset_buffer();
};

#endif
