import asyncio
import io
import wave

import numpy as np
import pytest

import voicesynth.voicesynth as core
from voicesynth import audio
from voicesynth.exceptions import (
    IncorrectModelPath,
    IncorrectSpeaker,
    InvalidAudioFormat,
    PackageError,
    SynthesisError,
)

from conftest import FakeEngine


def test_model_downloads_into_cache(fake_model, cache_home):
    model = core.Model(fake_model, show_download=False)
    assert model.model_path == str(cache_home / f"{fake_model}.pt")
    assert model.speaker == "es_0"


def test_model_rejects_unknown_model():
    with pytest.raises(Exception, match="Unknown model"):
        core.Model("nope")


def test_model_requires_pt_extension(tmp_path):
    with pytest.raises(IncorrectModelPath):
        core.Model("v3_es", str(tmp_path / "model.bin"))


def test_model_validates_speaker(fake_model):
    with pytest.raises(IncorrectSpeaker):
        core.Model(fake_model, speaker="nobody", show_download=False)
    model = core.Model(fake_model, speaker="es_2", show_download=False)
    assert model.speaker == "es_2"
    model.set_speaker("es_1")
    assert model.speaker == "es_1"
    with pytest.raises(IncorrectSpeaker):
        model.set_speaker("es_9")


def test_non_exhaustive_model_accepts_unknown_speaker(cache_home, server, package, monkeypatch):
    from voicesynth.models import models

    server.files["/d.pt"] = package
    monkeypatch.setitem(models["v3_de"], "url", server.url("/d.pt"))
    model = core.Model("v3_de", speaker="friedrich", show_download=False)
    assert model.speaker == "friedrich"


def test_loaded_speakers_replace_catalog(synthesizer, engine):
    assert synthesizer.speakers == engine.speakers
    assert synthesizer.model.exhaustive


def test_loaded_engine_rejects_invalid_chosen_speaker(fake_model, monkeypatch):
    monkeypatch.setattr(core, "_load_engine", lambda *a: FakeEngine(["only"]))
    with pytest.raises(IncorrectSpeaker):
        core.Synthesizer(core.Model(fake_model, speaker="es_1", show_download=False))


def test_loaded_engine_replaces_missing_default_speaker(fake_model, monkeypatch):
    monkeypatch.setattr(core, "_load_engine", lambda *a: FakeEngine(["only", "other"]))
    synthesizer = core.Synthesizer(core.Model(fake_model, show_download=False))
    assert synthesizer.model.speaker == "only"


def test_fetch_speakers(fake_model, monkeypatch):
    monkeypatch.setattr(core, "_load_engine", lambda *a: FakeEngine(["x", "y"]))
    model = core.Model(fake_model, speaker="es_0", show_download=False)
    with pytest.raises(IncorrectSpeaker):
        model.fetch_speakers()
    monkeypatch.setattr(core, "_load_engine", lambda *a: FakeEngine(["es_0", "extra"]))
    assert model.fetch_speakers() == ["es_0", "extra"]


def test_missing_torch(monkeypatch):
    import builtins

    real = builtins.__import__

    def fake(name, *args, **kwargs):
        if name == "torch":
            raise ModuleNotFoundError(name)
        return real(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake)
    with pytest.raises(PackageError, match="PyTorch"):
        core._load_engine("x.pt", "cpu", None)


def test_synthesize_writes_wav(synthesizer, tmp_path):
    path = tmp_path / "nested" / "out.wav"
    assert synthesizer.synthesize("hello", str(path)) == str(path)
    with wave.open(str(path)) as reader:
        assert reader.getframerate() == 8000
        assert reader.getnframes() == 50


def test_synthesize_accepts_pathlike_and_buffer(synthesizer, tmp_path):
    synthesizer.synthesize("hi", tmp_path / "a.wav")
    assert (tmp_path / "a.wav").exists()
    buffer = io.BytesIO()
    synthesizer.synthesize("hi", buffer)
    assert buffer.getvalue().startswith(b"RIFF")


def test_synthesize_rejects_non_wav(synthesizer, tmp_path):
    with pytest.raises(InvalidAudioFormat):
        synthesizer.synthesize("hi", str(tmp_path / "a.mp3"))


def test_empty_text_rejected(synthesizer):
    with pytest.raises(SynthesisError):
        synthesizer.generate("   ")


def test_invalid_speaker_and_sample_rate(synthesizer):
    with pytest.raises(IncorrectSpeaker):
        synthesizer.generate("hi", speaker="nobody")
    with pytest.raises(InvalidAudioFormat):
        synthesizer.generate("hi", sample_rate=44100)


def test_invalid_constructor_arguments(fake_model, monkeypatch):
    monkeypatch.setattr(core, "_load_engine", lambda *a: FakeEngine())
    model = core.Model(fake_model, show_download=False)
    with pytest.raises(InvalidAudioFormat):
        core.Synthesizer(model, sample_rate=1)
    with pytest.raises(ValueError):
        core.Synthesizer(model, max_chars=0)


def test_plain_text_is_sent_as_text(synthesizer, engine):
    synthesizer.generate("hello", speaker="baya")
    assert engine.calls == [{"speaker": "baya", "sample_rate": 8000, "text": "hello"}]


def test_prosody_rate_builds_escaped_ssml(synthesizer, engine):
    synthesizer.generate("Tom & Jerry <3", prosody_rate=90)
    assert engine.calls[0]["ssml_text"] == "<speak><prosody rate='90%'>Tom &amp; Jerry &lt;3</prosody></speak>"
    assert "text" not in engine.calls[0]


def test_raw_ssml_is_passed_through(synthesizer, engine):
    synthesizer.generate("<speak>hi</speak>", ssml=True)
    assert engine.calls[0]["ssml_text"] == "<speak>hi</speak>"


def test_long_text_is_chunked_with_pauses(synthesizer, engine):
    synthesizer.max_chars = 30
    text = "First sentence here. Second sentence here. Third sentence here."
    audio_data = synthesizer.generate(text)
    assert len(engine.calls) == 3
    silence = int(0.1 * 8000)
    expected = sum(len(call["text"]) * 10 for call in engine.calls) + 2 * silence
    assert len(audio_data) == expected
    assert np.count_nonzero(audio_data == 0) == 2 * silence


def test_ssml_is_not_chunked(synthesizer, engine):
    synthesizer.max_chars = 5
    synthesizer.generate("<speak>" + "word " * 20 + "</speak>", ssml=True)
    assert len(engine.calls) == 1


def test_engine_errors_are_wrapped(synthesizer):
    def broken(**kwargs):
        raise RuntimeError("boom")

    synthesizer._tts.apply_tts = broken
    with pytest.raises(SynthesisError, match="boom"):
        synthesizer.generate("hello")


def test_tensor_like_output_is_converted(synthesizer):
    class Tensor:
        def detach(self):
            return self

        def cpu(self):
            return self

        def numpy(self):
            return np.ones((1, 4), dtype=np.float64)

    synthesizer._tts.apply_tts = lambda **kwargs: Tensor()
    result = synthesizer.generate("hello")
    assert result.dtype == np.float32 and result.shape == (4,)


def test_synthesize_bytes(synthesizer):
    data = synthesizer.synthesize_bytes("hello", sample_rate=24000)
    with wave.open(io.BytesIO(data)) as reader:
        assert reader.getframerate() == 24000
        assert reader.getnframes() == 50


def test_mixed_language_warning(fake_model, monkeypatch, caplog):
    from voicesynth.log import logger
    from voicesynth.models import models

    monkeypatch.setitem(models[fake_model], "script", "cyrillic")
    monkeypatch.setattr(core, "_load_engine", lambda *a: FakeEngine())
    synthesizer = core.Synthesizer(core.Model(fake_model, show_download=False), sample_rate=8000)
    logger.disabled = False
    logger.addHandler(caplog.handler)
    try:
        synthesizer.generate("Привет hello мир")
        synthesizer.warn_mixed_language = False
        synthesizer.generate("Привет hello мир")
    finally:
        logger.removeHandler(caplog.handler)
    warnings = [record for record in caplog.records if "Latin" in record.getMessage()]
    assert len(warnings) == 1
    assert "Latin" in warnings[0].getMessage() and "hello" in warnings[0].getMessage()


def test_no_warning_for_pure_text(synthesizer, caplog):
    synthesizer.generate("hello world")
    assert not caplog.records


class Recorder:
    def __init__(self):
        self.played = []

    def play_audio(self, path, blocking=True, cleanup=None):
        self.played.append(path)
        playback = audio.Playback.__new__(audio.Playback)
        playback.path = path
        playback._cleanup = cleanup
        import threading

        playback._process = None
        playback._error = None
        playback._stopped = threading.Event()
        playback._lock = threading.Lock()
        playback._thread = threading.Thread(target=lambda: cleanup and cleanup())
        playback._thread.start()
        return playback


def test_say_without_path_uses_and_removes_temp_file(synthesizer):
    recorder = Recorder()
    synthesizer.audio = recorder
    playback = synthesizer.say("hello")
    assert len(recorder.played) == 1
    assert recorder.played[0].endswith(".wav")
    playback.wait()
    import os

    assert not os.path.exists(recorder.played[0])


def test_say_with_path_keeps_file(synthesizer, tmp_path):
    recorder = Recorder()
    synthesizer.audio = recorder
    path = tmp_path / "keep.wav"
    synthesizer.say("hello", str(path), blocking=False)
    assert path.exists()


def test_say_cleans_up_when_synthesis_fails(synthesizer, tmp_path, monkeypatch):
    import glob
    import tempfile

    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    synthesizer.audio = Recorder()
    with pytest.raises(SynthesisError):
        synthesizer.say("   ")
    assert glob.glob(str(tmp_path / "voicesynth_*")) == []


def test_async_methods(synthesizer, tmp_path):
    synthesizer.audio = Recorder()

    async def scenario():
        path = await synthesizer.synthesize_async("hello", str(tmp_path / "x.wav"))
        playback = await synthesizer.say_async("hello", str(tmp_path / "y.wav"))
        return path, playback

    path, playback = asyncio.run(scenario())
    assert (tmp_path / "x.wav").exists() and (tmp_path / "y.wav").exists()
    assert not playback.is_playing
