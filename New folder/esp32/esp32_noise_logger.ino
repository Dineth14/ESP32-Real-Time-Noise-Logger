/*
ESP32 Noise Logger - prototype
Samples ADC, applies simple IIR filters, computes time-domain features and sends JSON lines over Serial.
Note: This sketch is a starting point. For higher-quality audio use I2S microphone or ADC oversampling and calibration.
*/

#include <Arduino.h>
#include <driver/adc.h>
#include <ArduinoJson.h>
#include "tree_classifier.h"
#include "tree_classifier_ondevice.h"

const int SAMPLE_PIN = 34; // ADC1 channel
const int SAMPLE_RATE = 8000; // Hz
const int FRAME_SIZE = 256;

float buffer[FRAME_SIZE];
int idx = 0;

// Simple notch filter coefficients (placeholder) - recommend designing offline and hardcoding
float notch_b[3] = {1.0, -1.618, 1.0};
float notch_a[3] = {1.0, -1.618, 0.99};
float hp_b[2] = {0.995, -0.995};
float hp_a[2] = {1.0, -0.99};

void setup() {
  Serial.begin(115200);
  analogSetPinAttenuation(SAMPLE_PIN, ADC_11db);
  esp_timer_config_t cfg;
}

float apply_simple_hp(float x) {
  static float x1=0, y1=0;
  float y = hp_b[0]*x + hp_b[1]*x1 - hp_a[1]*y1;
  x1 = x;
  y1 = y;
  return y;
}

float apply_simple_notch(float x) {
  static float x1=0, x2=0, y1=0, y2=0;
  float y = notch_b[0]*x + notch_b[1]*x1 + notch_b[2]*x2 - notch_a[1]*y1 - notch_a[2]*y2;
  x2 = x1; x1 = x;
  y2 = y1; y1 = y;
  return y;
}

void process_frame() {
  // compute simple RMS and ZCR
  float sumsq=0; int zc=0;
  for (int i=0;i<FRAME_SIZE;i++) {
    sumsq += buffer[i]*buffer[i];
    if (i>0 && buffer[i-1]*buffer[i]<0) zc++;
  }
  float rms = sqrt(sumsq/FRAME_SIZE);
  float zcr = (float)zc/(FRAME_SIZE-1);

  // NOTE: centroid and band energies are approximated here by simple placeholders.
  // For better matching with the Python feature order, compute FFT and real band energies
  // (left as TODO for accuracy). We'll provide the same feature vector ordering:
  // [rms,zcr,centroid,band_energy_low,band_energy_mid,band_energy_high,snr]
  float centroid = 0.0;
  float be_low = 0.0;
  float be_mid = 0.0;
  float be_high = 0.0;
  float est_snr = 0.0;

  // pack features in same order expected by tree
  float features[7];
  features[0] = rms;
  features[1] = zcr;
  features[2] = centroid;
  features[3] = be_low;
  features[4] = be_mid;
  features[5] = be_high;
  features[6] = est_snr;

  // prefer on-device classifier built with on-device-features
  const char* cls = tree_classify_ondevice(features);

  // prepare JSON with classification
  StaticJsonDocument<256> doc;
  doc["rms"] = rms;
  doc["zcr"] = zcr;
  doc["class"] = cls;
  char out[256];
  size_t n = serializeJson(doc, out);
  Serial.println(out);
}

void loop() {
  // sample at SAMPLE_RATE roughly
  int raw = analogRead(SAMPLE_PIN);
  float v = ((float)raw)/4095.0 - 0.5; // center
  v = apply_simple_hp(v);
  v = apply_simple_notch(v);
  buffer[idx++] = v;
  if (idx>=FRAME_SIZE) { idx=0; process_frame(); }
  delayMicroseconds(1000000/SAMPLE_RATE);
}
