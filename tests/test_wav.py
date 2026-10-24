import io
import wave

import numpy as np

from voicesynth.wav import to_pcm16, wav_bytes, write_wav


def test_pcm_conversion_clips():
    pcm = np.frombuffer(to_pcm16(np.array([0.0, 1.0, -1.0, 5.0, -5.0])), dtype="<i2")
    assert pcm.tolist() == [0, 32767, -32767, 32767, -32767]


def test_write_wav_to_path(tmp_path):
    path = tmp_path / "a.wav"
    write_wav(str(path), np.zeros(480, dtype=np.float32), 24000)
    with wave.open(str(path)) as reader:
        assert reader.getframerate() == 24000
        assert reader.getnframes() == 480
        assert reader.getnchannels() == 1
        assert reader.getsampwidth() == 2


def test_wav_bytes_roundtrip():
    data = wav_bytes(np.linspace(-1, 1, 100, dtype=np.float32), 8000)
    with wave.open(io.BytesIO(data)) as reader:
        assert reader.getnframes() == 100
        assert reader.getframerate() == 8000
