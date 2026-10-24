import io
import wave
from typing import BinaryIO, Union

import numpy as np


def to_pcm16(audio: np.ndarray) -> bytes:
    clipped = np.clip(np.asarray(audio, dtype=np.float32), -1.0, 1.0)
    return (clipped * 32767.0).astype("<i2").tobytes()


def write_wav(target: Union[str, BinaryIO], audio: np.ndarray, sample_rate: int) -> None:
    with wave.open(target, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(sample_rate)
        writer.writeframes(to_pcm16(audio))


def wav_bytes(audio: np.ndarray, sample_rate: int) -> bytes:
    buffer = io.BytesIO()
    write_wav(buffer, audio, sample_rate)
    return buffer.getvalue()
