#ifndef TREE_CLASSIFIER_H
#define TREE_CLASSIFIER_H

// Auto-generated decision tree classifier header
// Feature order: rms,zcr,centroid,band_energy_low,band_energy_mid,band_energy_high,snr

static const char* tree_classify(const float *f) {
  if (f[6] <= 27.885633) {
    if (f[5] <= 0.086534) {
      return "background";
    } else {
      return "traffic";
    }
  } else {
    if (f[5] <= 0.047245) {
      return "voice";
    } else {
      return "machinery";
    }
  }
}

#endif // TREE_CLASSIFIER_H
