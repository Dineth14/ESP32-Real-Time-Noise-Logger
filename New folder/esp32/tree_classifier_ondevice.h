// Auto-generated on-device decision tree classifier header
// Guard and function name are unique to avoid collisions with other generated headers
#ifndef TREE_CLASSIFIER_ONDEVICE_H
#define TREE_CLASSIFIER_ONDEVICE_H

// Feature order expected by this classifier: rms, zcr, band_energy_low, band_energy_mid, band_energy_high
static const char* tree_classify_ondevice(const float *f) {
  if (f[3] <= 0.049394) {
    if (f[1] <= 0.295739) {
      return "voice";
    } else {
      return "background";
    }
  } else {
    if (f[2] <= 0.033234) {
      return "machinery";
    } else {
      return "traffic";
    }
  }
}

#endif // TREE_CLASSIFIER_ONDEVICE_H
