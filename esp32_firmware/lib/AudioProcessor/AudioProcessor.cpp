#include "AudioProcessor.h"
#include <algorithm>

AudioProcessor::AudioProcessor() : buffer_index(0), 
    high_pass_prev_input(0), high_pass_prev_output(0), low_pass_prev_output(0) {
    audio_buffer.resize(FRAME_SIZE);
    window.resize(FRAME_SIZE);
    prev_spectrum.resize(FRAME_SIZE / 2);
}

void AudioProcessor::initialize() {
    // Initialize Hamming window
    for (int i = 0; i < FRAME_SIZE; i++) {
        window[i] = 0.54 - 0.46 * cos(2.0 * PI * i / (FRAME_SIZE - 1));
    }
    
    // Initialize previous spectrum for flux calculation
    std::fill(prev_spectrum.begin(), prev_spectrum.end(), 0.0);
    buffer_index = 0;
}

void AudioProcessor::add_sample(int16_t sample) {
    // Apply digital filters as per VISUAL_FLOW.md
    float filtered_sample = apply_high_pass_filter((float)sample);
    filtered_sample = apply_low_pass_filter(filtered_sample);
    
    audio_buffer[buffer_index] = (int16_t)filtered_sample;
    buffer_index = (buffer_index + 1) % FRAME_SIZE;
}

bool AudioProcessor::extract_features(AudioFeatures& features) {
    if (buffer_index != 0) {
        return false; // Wait for complete frame
    }
    
    // Convert to float and normalize
    std::vector<float> frame(FRAME_SIZE);
    for (int i = 0; i < FRAME_SIZE; i++) {
        frame[i] = audio_buffer[i] / 32768.0;
    }
    
    // Apply window
    apply_hamming_window(frame);
    
    // Compute time-domain features
    features.rms = compute_rms(frame);
    features.zcr = compute_zcr(frame);
    
    // Compute frequency-domain features
    std::vector<float> spectrum(FRAME_SIZE / 2);
    compute_fft(frame, spectrum);
    
    features.spectral_centroid = compute_spectral_centroid(spectrum);
    compute_band_energies(spectrum, features.low_energy, features.mid_energy, features.high_energy);
    features.spectral_flux = compute_spectral_flux(spectrum);
    
    // Store current spectrum for next flux calculation
    prev_spectrum = spectrum;
    
    return true;
}

void AudioProcessor::apply_hamming_window(std::vector<float>& frame) {
    for (int i = 0; i < FRAME_SIZE; i++) {
        frame[i] *= window[i];
    }
}

void AudioProcessor::compute_fft(std::vector<float>& frame, std::vector<float>& spectrum) {
    // Simple magnitude spectrum computation (simplified FFT)
    // For a full implementation, you would use a proper FFT library
    for (int k = 0; k < FRAME_SIZE / 2; k++) {
        float real = 0, imag = 0;
        for (int n = 0; n < FRAME_SIZE; n++) {
            float angle = -2.0 * PI * k * n / FRAME_SIZE;
            real += frame[n] * cos(angle);
            imag += frame[n] * sin(angle);
        }
        spectrum[k] = sqrt(real * real + imag * imag);
    }
}

float AudioProcessor::compute_rms(const std::vector<float>& frame) {
    float sum = 0;
    for (float sample : frame) {
        sum += sample * sample;
    }
    return sqrt(sum / frame.size());
}

float AudioProcessor::compute_zcr(const std::vector<float>& frame) {
    int crossings = 0;
    for (int i = 1; i < frame.size(); i++) {
        if ((frame[i-1] >= 0) != (frame[i] >= 0)) {
            crossings++;
        }
    }
    return (float)crossings / (frame.size() - 1);
}

float AudioProcessor::compute_spectral_centroid(const std::vector<float>& spectrum) {
    float weighted_sum = 0, magnitude_sum = 0;
    
    for (int i = 0; i < spectrum.size(); i++) {
        float freq = (float)i * SAMPLE_RATE / (2 * spectrum.size());
        weighted_sum += freq * spectrum[i];
        magnitude_sum += spectrum[i];
    }
    
    return magnitude_sum > 0 ? weighted_sum / magnitude_sum : 0;
}

void AudioProcessor::compute_band_energies(const std::vector<float>& spectrum, float& low, float& mid, float& high) {
    // Frequency bands as per VISUAL_FLOW.md for 30 kHz sampling (15 kHz Nyquist)
    int low_end = (2000 * spectrum.size()) / (SAMPLE_RATE / 2);    // 0-2 kHz
    int mid_end = (6000 * spectrum.size()) / (SAMPLE_RATE / 2);    // 2-6 kHz
    // high: 6-15 kHz (rest of spectrum)
    
    low = mid = high = 0;
    
    for (int i = 0; i < spectrum.size(); i++) {
        float energy = spectrum[i] * spectrum[i];
        if (i < low_end) {
            low += energy;
        } else if (i < mid_end) {
            mid += energy;
        } else {
            high += energy;
        }
    }
}

float AudioProcessor::compute_spectral_flux(const std::vector<float>& spectrum) {
    float flux = 0;
    for (int i = 0; i < spectrum.size(); i++) {
        float diff = spectrum[i] - prev_spectrum[i];
        if (diff > 0) {
            flux += diff;
        }
    }
    return flux;
}

void AudioProcessor::reset_buffer() {
    buffer_index = 0;
    std::fill(audio_buffer.begin(), audio_buffer.end(), 0);
    
    // Reset filter states
    high_pass_prev_input = 0;
    high_pass_prev_output = 0;
    low_pass_prev_output = 0;
}

// Digital filters as per VISUAL_FLOW.md
float AudioProcessor::apply_high_pass_filter(float input) {
    // 150Hz high-pass filter: y[n] = α(y[n-1] + x[n] - x[n-1])
    // α = RC / (RC + dt), where RC = 1/(2*π*150) and dt = 1/30000
    const float alpha = 0.9691f;  // Calculated for 150Hz at 30kHz
    
    float output = alpha * (high_pass_prev_output + input - high_pass_prev_input);
    high_pass_prev_input = input;
    high_pass_prev_output = output;
    
    return output;
}

float AudioProcessor::apply_low_pass_filter(float input) {
    // 15kHz low-pass filter: y[n] = αx[n] + (1-α)y[n-1]
    // α = dt / (RC + dt), where RC = 1/(2*π*15000) and dt = 1/30000
    const float alpha = 0.7596f;  // Calculated for 15kHz at 30kHz
    
    float output = alpha * input + (1.0f - alpha) * low_pass_prev_output;
    low_pass_prev_output = output;
    
    return output;
}
