import numpy as np


def resample_to_16khz(audio: np.ndarray, source_sr: int) -> np.ndarray:
    """Resample int16 mono audio to 16kHz via linear interpolation."""
    if source_sr == 16000:
        return audio
    ratio = 16000 / source_sr
    new_len = int(len(audio) * ratio)
    indices = np.linspace(0, len(audio) - 1, new_len)
    return np.interp(indices, np.arange(len(audio)), audio).astype(np.int16)
