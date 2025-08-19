"""
Feature extraction utilities for Noise Pollution Logger.
Provides filtering, framing, time-domain and frequency-domain features.
"""
import numpy as np
from scipy.signal import butter, filtfilt, iirnotch, welch

# Simple filters

def butter_highpass(cutoff, fs, order=4):
    """Design a highpass Butterworth filter (cutoff in Hz).

    Cutoff is clamped to (0, nyquist-eps) to avoid invalid designs.
    Returns (b, a).
    """
    nyq = 0.5 * fs
    eps = 1e-6
    cutoff = max(min(cutoff, nyq - eps), eps)
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    return b, a


def butter_lowpass(cutoff, fs, order=4):
    """Design a lowpass Butterworth filter (cutoff in Hz).

    Cutoff is clamped to (0, nyquist-eps) to avoid invalid designs.
    Returns (b, a).
    """
    nyq = 0.5 * fs
    eps = 1e-6
    cutoff = max(min(cutoff, nyq - eps), eps)
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a


def apply_filter(data, b, a, zero_phase=True):
    """Apply IIR filter. By default use zero-phase filtering (filtfilt) to avoid phase distortion.
    Falls back to lfilter-like behaviour if filtfilt is inappropriate for very short signals.
    """
    if zero_phase and len(data) > (max(len(a), len(b)) * 3):
        return filtfilt(b, a, data)
    # fallback
    from scipy.signal import lfilter
    return lfilter(b, a, data)


def notch(fs, freq=50.0, Q=30.0):
    """Design a notch (band-stop) filter around `freq` (Hz).

    Uses scipy.signal.iirnotch with the `fs` argument when available; falls back to normalized w0 if needed.
    """
    try:
        # newer scipy: iirnotch(w0, Q, fs=fs)
        b, a = iirnotch(freq, Q, fs=fs)
    except TypeError:
        # older interface expects normalized frequency (0..1 where 1 is Nyquist)
        w0 = freq / (fs / 2)
        b, a = iirnotch(w0, Q)
    return b, a

# Framing

def frame_signal(x, frame_size, hop_size):
    """Frame `x` into overlapping frames. Pads the end with zeros if necessary.

    Returns an array shape (num_frames, frame_size).
    """
    if len(x) < frame_size:
        x = np.pad(x, (0, frame_size - len(x)))
    num_frames = 1 + (len(x) - frame_size) // hop_size
    frames = np.stack([x[i*hop_size:i*hop_size+frame_size] for i in range(num_frames)])
    return frames

# Time-domain features

def rms(x):
    return np.sqrt(np.mean(np.square(x)))


def zero_crossing_rate(x):
    return ((x[:-1] * x[1:]) < 0).sum() / float(len(x)-1)

# Frequency-domain features

def compute_fft(x, fs):
    N = len(x)
    win = np.hanning(N)
    X = np.fft.rfft(x * win)
    freqs = np.fft.rfftfreq(N, 1/fs)
    mags = np.abs(X) / (win.sum()/2)
    return freqs, mags


def spectral_centroid(freqs, mags):
    if mags.sum() == 0:
        return 0.0
    return (freqs * mags).sum() / mags.sum()


def band_energy(freqs, mags, f_low, f_high):
    mask = (freqs >= f_low) & (freqs <= f_high)
    return np.sum(mags[mask]**2)


def snr(mags):
    """Estimate SNR (dB) from the magnitude spectrum.

    Uses 10*log10(signal_power / noise_power) where signal_power is the power around the spectral peak
    and noise_power is the median power across bins.
    """
    power = mags**2
    if power.sum() == 0:
        return 0.0
    peak_idx = np.argmax(power)
    # signal energy in a small neighborhood around the peak
    lo = max(0, peak_idx-2)
    hi = min(len(power)-1, peak_idx+2)
    signal_power = power[lo:hi+1].sum()
    noise_power = np.median(power)
    if noise_power <= 0:
        return 120.0
    return 10 * np.log10(signal_power / noise_power)

# High-level pipeline

def extract_features(signal, fs, frame_size=1024, hop_size=512):
    """High-level extraction pipeline:

    - Notch at mains (50Hz) to remove hum.
    - High-pass at 20 Hz to remove DC and very low drift.
    - Low-pass to Nyquist-allowable frequency (clamped).
    - Frame, then compute per-frame features.

    Returns (frames, list_of_feature_dicts).
    """
    # design filters
    b_notch, a_notch = notch(fs, 50.0, Q=30.0)
    b_hp, a_hp = butter_highpass(20.0, fs, order=2)
    # lowpass slightly below Nyquist
    b_lp, a_lp = butter_lowpass(min(0.45*fs, fs/2 - 1.0), fs, order=4)

    # apply filters with zero-phase where possible
    sig = apply_filter(signal, b_notch, a_notch, zero_phase=True)
    sig = apply_filter(sig, b_hp, a_hp, zero_phase=True)
    sig = apply_filter(sig, b_lp, a_lp, zero_phase=True)

    frames = frame_signal(sig, frame_size, hop_size)
    feats = []
    for f in frames:
        fr = {}
        fr['rms'] = rms(f)
        fr['zcr'] = zero_crossing_rate(f)
        freqs, mags = compute_fft(f, fs)
        fr['centroid'] = spectral_centroid(freqs, mags)
        fr['band_energy_low'] = band_energy(freqs, mags, 20, 250)
        fr['band_energy_mid'] = band_energy(freqs, mags, 250, 2000)
        fr['band_energy_high'] = band_energy(freqs, mags, 2000, fs/2)
        fr['snr'] = snr(mags)
        feats.append(fr)
    return frames, feats

if __name__ == '__main__':
    # tiny smoke test
    fs = 16000
    t = np.linspace(0, 1, fs, endpoint=False)
    sig = 0.1 * np.sin(2*np.pi*440*t) + 0.02 * np.sin(2*np.pi*50*t)
    frames, feats = extract_features(sig, fs)
    print('Extracted', len(feats), 'frames, sample feature:', feats[0])
