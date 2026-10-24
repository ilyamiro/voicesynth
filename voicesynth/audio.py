import os
import shutil
import subprocess
import sys

from voicesynth.exceptions import AudioPlayingError, InvalidAudioPath
from voicesynth.log import logger

_LINUX_PLAYERS = (
    ["paplay"],
    ["pw-play"],
    ["aplay", "-q"],
    ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"],
    ["mpv", "--no-video", "--really-quiet"],
    ["play", "-q"],
)


def _run(command: list) -> bool:
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, OSError):
        return False


class AudioManager:
    @staticmethod
    def play_audio(path: str) -> None:
        if not os.path.isfile(path):
            raise InvalidAudioPath(f"Specified path for playing does not exist: {path}")

        if sys.platform == "win32":
            import winsound

            try:
                winsound.PlaySound(path, winsound.SND_FILENAME)
            except RuntimeError as error:
                raise AudioPlayingError(f"Could not play {path}: {error}") from error
        elif sys.platform == "darwin":
            if not _run(["afplay", path]):
                raise AudioPlayingError("afplay failed to play the audio file")
        else:
            players = [player for player in _LINUX_PLAYERS if shutil.which(player[0])]
            if not players:
                raise AudioPlayingError(
                    "No audio player found. Install PulseAudio, PipeWire, ALSA, ffmpeg, mpv or sox"
                )
            if not any(_run(player + [path]) for player in players):
                raise AudioPlayingError(f"None of the available audio players could play {path}")

        logger.info(f"File {path} played")

    play = play_audio
