"""
Train a simple classifier on synthetic audio data and export model.
This script generates synthetic signals for classes (traffic, machinery, voices, background), extracts features using feature_extraction, trains a RandomForest, and exports with joblib.
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn import tree as sktree
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

from feature_extraction import extract_features


def synth_signal(class_name, duration, fs):
    t = np.linspace(0, duration, int(fs*duration), endpoint=False)
    if class_name == 'traffic':
        # broadband noise + low-frequency rumble
        sig = 0.3 * np.random.randn(len(t)) + 0.2 * np.sin(2*np.pi*100*t)
    elif class_name == 'machinery':
        sig = 0.2 * np.random.randn(len(t)) + 0.4 * np.sin(2*np.pi*300*t)
    elif class_name == 'voice':
        # quasi-periodic with formant-like bands
        sig = 0.1 * np.random.randn(len(t)) + 0.3 * np.sin(2*np.pi*200*t)
        sig += 0.15 * np.sin(2*np.pi*800*t)
    else:
        sig = 0.05 * np.random.randn(len(t))
    # add 50Hz hum
    sig += 0.02 * np.sin(2*np.pi*50*t)
    return sig


def make_dataset(fs=16000, n_per_class=50):
    classes = ['traffic', 'machinery', 'voice', 'background']
    X = []
    y = []
    for cls in classes:
        for i in range(n_per_class):
            sig = synth_signal(cls, 2.0, fs)
            frames, feats = extract_features(sig, fs)
            # summarise per-file by averaging frame features
            keys = list(feats[0].keys())
            arr = np.array([[f[k] for k in keys] for f in feats])
            mean = arr.mean(axis=0)
            X.append(mean)
            y.append(cls)
    keys = keys
    return np.array(X), np.array(y), keys


def make_ondevice_dataset(fs=16000, n_per_class=50):
    # Use only on-device features: rms, zcr, band_energy_low, band_energy_mid, band_energy_high
    X = []
    y = []
    classes = ['traffic', 'machinery', 'voice', 'background']
    for cls in classes:
        for i in range(n_per_class):
            sig = synth_signal(cls, 2.0, fs)
            frames, feats = extract_features(sig, fs)
            # pick per-file mean for only selected keys
            arr = np.array([[f[k] for k in ['rms', 'zcr', 'band_energy_low', 'band_energy_mid', 'band_energy_high']] for f in feats])
            mean = arr.mean(axis=0)
            X.append(mean)
            y.append(cls)
    return np.array(X), np.array(y), ['rms', 'zcr', 'band_energy_low', 'band_energy_mid', 'band_energy_high']


def main():
    X, y, keys = make_dataset()
    X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, test_size=0.2, random_state=42)
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)
    print(classification_report(y_test, preds))
    joblib.dump({'model': clf, 'features': keys}, 'noise_classifier.joblib')
    print('Exported noise_classifier.joblib')

    # Train a compact decision tree for on-device rules
    dt = DecisionTreeClassifier(max_depth=4, min_samples_leaf=5, random_state=42)
    dt.fit(X_train, y_train)
    dt_preds = dt.predict(X_test)
    print('DecisionTree performance:')
    print(classification_report(y_test, dt_preds))
    joblib.dump({'model': dt, 'features': keys}, 'noise_tree.joblib')
    print('Exported noise_tree.joblib')

    # Export the decision tree as a C header with nested if/else.
    def node_to_c(tree, feature_names, class_names, node=0, depth=0):
        indent = '  ' * depth
        left = tree.children_left[node]
        right = tree.children_right[node]
        if left == -1 and right == -1:
            # leaf
            # pick majority class
            vals = tree.value[node][0]
            cls = class_names[np.argmax(vals)]
            return indent + f'return "{cls}";\n'
        feat = feature_names[tree.feature[node]]
        thresh = float(tree.threshold[node])
        s = indent + f'if (f[{feature_names.index(feat)}] <= {thresh:.6f}) {{\n'
        s += node_to_c(tree, feature_names, class_names, left, depth+1)
        s += indent + '} else {\n'
        s += node_to_c(tree, feature_names, class_names, right, depth+1)
        s += indent + '}\n'
        return s

    def export_tree_to_header(dt_clf, feature_names, class_names, path):
        T = dt_clf.tree_
        with open(path, 'w') as fh:
            fh.write('#ifndef TREE_CLASSIFIER_H\n')
            fh.write('#define TREE_CLASSIFIER_H\n\n')
            fh.write('// Auto-generated decision tree classifier header\n')
            fh.write('// Feature order: ' + ','.join(feature_names) + '\n\n')
            fh.write('static const char* tree_classify(const float *f) {\n')
            fh.write(node_to_c(T, feature_names, class_names, 0, 1))
            fh.write('}\n\n')
            fh.write('#endif // TREE_CLASSIFIER_H\n')

    class_names = list(np.unique(y_train))
    feature_names = list(keys)
    export_tree_to_header(dt, feature_names, class_names, '../esp32/tree_classifier.h')
    print('Exported esp32/tree_classifier.h')

    # Train a compact tree for on-device-only features
    X_on, y_on, feat_on = make_ondevice_dataset()
    Xon_train, Xon_test, yon_train, yon_test = train_test_split(X_on, y_on, stratify=y_on, test_size=0.2, random_state=42)
    dt_on = DecisionTreeClassifier(max_depth=4, min_samples_leaf=5, random_state=42)
    dt_on.fit(Xon_train, yon_train)
    print('On-device DecisionTree performance:')
    print(classification_report(yon_test, dt_on.predict(Xon_test)))
    joblib.dump({'model': dt_on, 'features': feat_on}, 'noise_tree_ondevice.joblib')
    export_tree_to_header(dt_on, feat_on, list(np.unique(yon_train)), '../esp32/tree_classifier_ondevice.h')
    print('Exported esp32/tree_classifier_ondevice.h')

if __name__ == '__main__':
    main()
