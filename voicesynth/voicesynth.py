import os
import tempfile
from typing import List, Optional
from xml.sax.saxutils import escape

from voicesynth.audio import AudioManager
from voicesynth.download import download_file
from voicesynth.exceptions import (
    IncorrectModelPath,
    IncorrectSpeaker,
    InvalidAudioFormat,
    PackageError,
    SynthesisError,
)
from voicesynth.log import disable_logging, enable_logging, logger
from voicesynth.models import DEFAULT_MODEL, SAMPLE_RATES, get_model_info, models, show_available_models

__all__ = [
    "Model",
    "Synthesizer",
    "AudioManager",
    "models",
    "show_available_models",
    "disable_logging",
    "enable_logging",
    "default_model_path",
]


def _torch():
    try:
        import torch
    except ModuleNotFoundError:
        raise PackageError(
            "PyTorch is not installed. For a lightweight CPU-only installation, use: "
            "pip install torch --index-url https://download.pytorch.org/whl/cpu"
        ) from None
    return torch


def default_model_path(model: str) -> str:
    cache = os.environ.get("VOICESYNTH_HOME") or os.path.join(
        os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache"), "voicesynth"
    )
    return os.path.join(cache, f"{model}.pt")


class Model:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        model_path: Optional[str] = None,
        show_download: bool = True,
        speaker: Optional[str] = None,
    ):
        info = get_model_info(model)
        self.model = model
        self.url = info["url"]
        self.language = info["language"]
        self.speakers: List[str] = list(info["speakers"])
        self.exhaustive: bool = info["exhaustive"]
        self.model_path = os.path.expanduser(model_path) if model_path else default_model_path(model)

        if not self.model_path.endswith(".pt"):
            raise IncorrectModelPath("Model file path should end with .pt!")

        self.set_speaker(speaker or self.speakers[0])
        logger.info("Model configured")
        self.download_model(self.url, self.model_path, show_download)

    def set_speaker(self, name: str) -> None:
        if name not in self.speakers and self.exhaustive:
            raise IncorrectSpeaker(f"Speaker invalid! Ensure it's one of {', '.join(self.speakers)}")
        self.speaker = name
        logger.info(f"Speaker {name} set")

    def download_model(self, url: str, model_path: str, show_progress: bool = True) -> None:
        self.model_path = model_path
        if os.path.isfile(model_path):
            logger.info("Setting up existing model")
            return
        logger.info("Downloading synthesis model")
        download_file(url, model_path, show_progress)


class Synthesizer:
    def __init__(
        self,
        model: Optional[Model] = None,
        device: str = "cpu",
        threads: Optional[int] = None,
        sample_rate: int = 48000,
    ) -> None:
        self._check_sample_rate(sample_rate)
        torch = _torch()

        self.model = model if model is not None else Model()
        self.audio = AudioManager()
        self.sample_rate = sample_rate

        if threads:
            torch.set_num_threads(threads)

        self.device = torch.device(device)
        try:
            self._tts = torch.package.PackageImporter(self.model.model_path).load_pickle("tts_models", "model")
        except Exception as error:
            raise IncorrectModelPath(
                f"Could not load {self.model.model_path}. Delete the file to download it again: {error}"
            ) from error
        self._tts.to(self.device)

        loaded_speakers = list(getattr(self._tts, "speakers", None) or [])
        if loaded_speakers:
            self.model.speakers = loaded_speakers
            self.model.exhaustive = True
            self.model.set_speaker(self.model.speaker)

        logger.info(f"Synthesizer configured: {self.model.model}, device {device}")

    @staticmethod
    def _check_sample_rate(sample_rate: int) -> None:
        if sample_rate not in SAMPLE_RATES:
            raise InvalidAudioFormat(f"Sample rate must be one of {', '.join(map(str, SAMPLE_RATES))}")

    @property
    def speakers(self) -> List[str]:
        return self.model.speakers

    def set_speaker(self, name: str) -> None:
        self.model.set_speaker(name)

    def synthesize(
        self,
        text: str,
        path: str = "audio.wav",
        prosody_rate: int = 100,
        speaker: Optional[str] = None,
        sample_rate: Optional[int] = None,
        ssml: bool = False,
    ) -> str:
        if not path.lower().endswith(".wav"):
            raise InvalidAudioFormat("Incorrect audio format! Ensure that path leads to a .wav file")
        if not text or not text.strip():
            raise SynthesisError("There is no text to synthesize")

        speaker = speaker or self.model.speaker
        if speaker not in self.model.speakers:
            raise IncorrectSpeaker(f"Speaker invalid! Ensure it's one of {', '.join(self.model.speakers)}")

        rate = sample_rate or self.sample_rate
        self._check_sample_rate(rate)

        arguments = {"speaker": speaker, "sample_rate": rate, "audio_path": path}
        if ssml:
            arguments["ssml_text"] = text
        elif prosody_rate != 100:
            arguments["ssml_text"] = f"<speak><prosody rate='{prosody_rate}%'>{escape(text)}</prosody></speak>"
        else:
            arguments["text"] = text

        directory = os.path.dirname(os.path.abspath(path))
        os.makedirs(directory, exist_ok=True)

        try:
            self._tts.save_wav(**arguments)
        except Exception as error:
            raise SynthesisError(f"There was an error synthesizing this text: {text}. {error}") from error

        logger.info("Audio synthesized")
        return path

    def say(
        self,
        text: str,
        path: Optional[str] = None,
        prosody_rate: int = 100,
        speaker: Optional[str] = None,
        sample_rate: Optional[int] = None,
        ssml: bool = False,
    ) -> Optional[str]:
        if path is not None:
            self.synthesize(text, path, prosody_rate, speaker, sample_rate, ssml)
            self.audio.play_audio(path)
            return path

        handle, temporary = tempfile.mkstemp(suffix=".wav", prefix="voicesynth_")
        os.close(handle)
        try:
            self.synthesize(text, temporary, prosody_rate, speaker, sample_rate, ssml)
            self.audio.play_audio(temporary)
        finally:
            if os.path.exists(temporary):
                os.remove(temporary)
        return None
