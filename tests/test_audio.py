import os
import threading

import pytest

import voicesynth.audio as audio
from voicesynth.exceptions import AudioPlayingError, InvalidAudioPath


class FakeProcess:
    def __init__(self, code=0, hold=None):
        self.code = code
        self.hold = hold
        self.terminated = False
        self.released = threading.Event()

    def wait(self):
        if self.hold:
            self.released.wait(5)
        return self.code

    def poll(self):
        return None if self.hold and not self.released.is_set() else self.code

    def terminate(self):
        self.terminated = True
        self.released.set()


@pytest.fixture
def wav(tmp_path):
    path = tmp_path / "a.wav"
    path.write_bytes(b"RIFF")
    return str(path)


@pytest.fixture(autouse=True)
def linux(monkeypatch):
    monkeypatch.setattr(audio.sys, "platform", "linux")
    monkeypatch.setattr(audio.shutil, "which", lambda name: f"/usr/bin/{name}" if name in ("paplay", "aplay") else None)


def test_missing_file(tmp_path):
    with pytest.raises(InvalidAudioPath):
        audio.AudioManager.play_audio(str(tmp_path / "none.wav"))


def test_blocking_play_runs_first_player(monkeypatch, wav):
    started = []
    monkeypatch.setattr(audio.subprocess, "Popen", lambda command, **_: started.append(command) or FakeProcess())
    playback = audio.AudioManager.play_audio(wav)
    assert started == [["paplay", wav]]
    assert not playback.is_playing


def test_falls_back_when_player_fails(monkeypatch, wav):
    started = []

    def popen(command, **_):
        started.append(command[0])
        return FakeProcess(code=1 if command[0] == "paplay" else 0)

    monkeypatch.setattr(audio.subprocess, "Popen", popen)
    audio.AudioManager.play_audio(wav)
    assert started == ["paplay", "aplay"]


def test_falls_back_when_player_cannot_start(monkeypatch, wav):
    started = []

    def popen(command, **_):
        started.append(command[0])
        if command[0] == "paplay":
            raise FileNotFoundError
        return FakeProcess()

    monkeypatch.setattr(audio.subprocess, "Popen", popen)
    audio.AudioManager.play_audio(wav)
    assert started == ["paplay", "aplay"]


def test_all_players_failing_raises(monkeypatch, wav):
    monkeypatch.setattr(audio.subprocess, "Popen", lambda command, **_: FakeProcess(code=1))
    with pytest.raises(AudioPlayingError):
        audio.AudioManager.play_audio(wav)


def test_no_player_installed(monkeypatch, wav):
    monkeypatch.setattr(audio.shutil, "which", lambda name: None)
    with pytest.raises(AudioPlayingError, match="No audio player"):
        audio.AudioManager.play_audio(wav)


def test_non_blocking_playback_can_be_waited(monkeypatch, wav):
    process = FakeProcess(hold=True)
    monkeypatch.setattr(audio.subprocess, "Popen", lambda command, **_: process)
    playback = audio.AudioManager.play_audio(wav, blocking=False)
    assert playback.is_playing
    assert playback.wait(timeout=0.05) is False
    process.released.set()
    assert playback.wait(timeout=5) is True
    assert not playback.is_playing


def test_stop_terminates_process(monkeypatch, wav):
    process = FakeProcess(hold=True)
    monkeypatch.setattr(audio.subprocess, "Popen", lambda command, **_: process)
    playback = audio.AudioManager.play_audio(wav, blocking=False)
    while playback._process is None:
        pass
    playback.stop()
    assert process.terminated
    assert not playback.is_playing
    assert playback.wait() is True


def test_cleanup_runs_after_playback(monkeypatch, wav):
    monkeypatch.setattr(audio.subprocess, "Popen", lambda command, **_: FakeProcess())
    audio.AudioManager.play_audio(wav, cleanup=lambda: os.remove(wav))
    assert not os.path.exists(wav)


def test_cleanup_runs_even_on_error(monkeypatch, wav):
    monkeypatch.setattr(audio.shutil, "which", lambda name: None)
    done = []
    playback = audio.AudioManager.play_audio(wav, blocking=False, cleanup=lambda: done.append(1))
    with pytest.raises(AudioPlayingError):
        playback.wait()
    assert done == [1]


def test_macos_uses_afplay(monkeypatch, wav):
    started = []
    monkeypatch.setattr(audio.sys, "platform", "darwin")
    monkeypatch.setattr(audio.shutil, "which", lambda name: "/usr/bin/afplay")
    monkeypatch.setattr(audio.subprocess, "Popen", lambda command, **_: started.append(command) or FakeProcess())
    audio.AudioManager.play_audio(wav)
    assert started == [["afplay", wav]]


def test_wait_async(monkeypatch, wav):
    import asyncio

    monkeypatch.setattr(audio.subprocess, "Popen", lambda command, **_: FakeProcess())
    playback = audio.AudioManager.play_audio(wav, blocking=False)
    assert asyncio.run(playback.wait_async()) is True
