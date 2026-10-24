import importlib
import os
import shutil
import subprocess
import sys
import threading
from typing import Callable, List, Optional

from voicesynth.exceptions import AudioPlayingError, InvalidAudioPath, VoiceSynthError
from voicesynth.log import logger

_LINUX_PLAYERS = (
    ["paplay"],
    ["pw-play"],
    ["aplay", "-q"],
    ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"],
    ["mpv", "--no-video", "--really-quiet"],
    ["play", "-q"],
)

_DARWIN_PLAYERS = (["afplay"],)


def _available_players() -> List[List[str]]:
    candidates = _DARWIN_PLAYERS if sys.platform == "darwin" else _LINUX_PLAYERS
    return [list(player) for player in candidates if shutil.which(player[0])]


class Playback:
    def __init__(self, path: str, cleanup: Optional[Callable[[], None]] = None) -> None:
        self.path = path
        self._cleanup = cleanup
        self._process: Optional["subprocess.Popen[bytes]"] = None
        self._error: Optional[VoiceSynthError] = None
        self._stopped = threading.Event()
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._run, name="voicesynth-playback", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        try:
            if sys.platform == "win32":
                self._play_windows()
            else:
                self._play_process()
            if not self._stopped.is_set():
                logger.info(f"File {self.path} played")
        except VoiceSynthError as error:
            self._error = error
        finally:
            if self._cleanup is not None:
                try:
                    self._cleanup()
                except OSError:
                    pass

    def _play_windows(self) -> None:
        winsound = importlib.import_module("winsound")
        try:
            winsound.PlaySound(self.path, winsound.SND_FILENAME)
        except RuntimeError as error:
            raise AudioPlayingError(f"Could not play {self.path}: {error}") from error

    def _play_process(self) -> None:
        players = _available_players()
        if not players:
            raise AudioPlayingError(
                "No audio player found. Install PulseAudio, PipeWire, ALSA, ffmpeg, mpv or sox"
            )
        for player in players:
            with self._lock:
                if self._stopped.is_set():
                    return
                try:
                    self._process = subprocess.Popen(
                        player + [self.path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                except OSError:
                    continue
                process = self._process
            code = process.wait()
            if self._stopped.is_set() or code == 0:
                return
        raise AudioPlayingError(f"None of the available audio players could play {self.path}")

    @property
    def is_playing(self) -> bool:
        return self._thread.is_alive()

    def wait(self, timeout: Optional[float] = None) -> bool:
        self._thread.join(timeout)
        if self._thread.is_alive():
            return False
        if self._error is not None and not self._stopped.is_set():
            raise self._error
        return True

    def stop(self) -> None:
        with self._lock:
            self._stopped.set()
            process = self._process
        if sys.platform == "win32":
            winsound = importlib.import_module("winsound")
            winsound.PlaySound(None, winsound.SND_PURGE)
        elif process is not None and process.poll() is None:
            process.terminate()
        self._thread.join()

    async def wait_async(self) -> bool:
        import asyncio

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.wait)


class AudioManager:
    @staticmethod
    def play_audio(
        path: str, blocking: bool = True, cleanup: Optional[Callable[[], None]] = None
    ) -> Playback:
        path = os.fspath(path)
        if not os.path.isfile(path):
            raise InvalidAudioPath(f"Specified path for playing does not exist: {path}")
        playback = Playback(path, cleanup)
        if blocking:
            playback.wait()
        return playback

    play = play_audio
