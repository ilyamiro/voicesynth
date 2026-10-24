import asyncio
import functools
import importlib
import os
import tempfile
from typing import Any, BinaryIO, Callable, Dict, List, Optional, Union
from xml.sax.saxutils import escape

import numpy as np

from voicesynth import cache
from voicesynth.audio import AudioManager, Playback
from voicesynth.cache import default_model_path
from voicesynth.exceptions import (
    IncorrectModelPath,
    IncorrectSpeaker,
    InvalidAudioFormat,
    PackageError,
    SynthesisError,
)
from voicesynth.log import disable_logging, enable_logging, logger
from voicesynth.models import DEFAULT_MODEL, SAMPLE_RATES, get_model_info, models, show_available_models
from voicesynth.text import foreign_words, split_text
from voicesynth.wav import wav_bytes, write_wav

__all__ = [
    "Model",
    "Synthesizer",
    "AudioManager",
    "Playback",
    "models",
    "show_available_models",
    "disable_logging",
    "enable_logging",
    "default_model_path",
]

PathLike = Union[str, "os.PathLike[str]"]


def _load_engine(path: str, device: str, threads: Optional[int]) -> Any:
    try:
        import torch
    except ModuleNotFoundError:
        raise PackageError(
            "PyTorch is not installed. For a lightweight CPU-only installation, use: "
            "pip install torch --index-url https://download.pytorch.org/whl/cpu"
        ) from None

    if threads:
        torch.set_num_threads(threads)
    try:
        engine = importlib.import_module("torch.package").PackageImporter(path).load_pickle("tts_models", "model")
    except Exception as error:
        raise IncorrectModelPath(
            f"Could not load {path}. Delete the file to download it again: {error}"
        ) from error
    engine.to(torch.device(device))
    return engine


def _to_array(audio: Any) -> np.ndarray:
    if hasattr(audio, "detach"):
        audio = audio.detach().cpu().numpy()
    return np.asarray(audio, dtype=np.float32).reshape(-1)


class Model:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        model_path: Optional[PathLike] = None,
        show_download: bool = True,
        speaker: Optional[str] = None,
    ) -> None:
        info = get_model_info(model)
        self.model = model
        self.url = info["url"]
        self.language = info["language"]
        self.script = info["script"]
        self.speakers: List[str] = list(info["speakers"])
        self.exhaustive = info["exhaustive"]
        self.model_path = os.path.expanduser(os.fspath(model_path)) if model_path else default_model_path(model)

        if not self.model_path.endswith(".pt"):
            raise IncorrectModelPath("Model file path should end with .pt!")

        self.speaker = self.speakers[0]
        self.speaker_chosen = False
        self.set_speaker(speaker or self.speakers[0])
        self.speaker_chosen = speaker is not None
        logger.info("Model configured")
        self.download_model(self.url, self.model_path, show_download)

    def set_speaker(self, name: str) -> None:
        if name not in self.speakers and self.exhaustive:
            raise IncorrectSpeaker(f"Speaker invalid! Ensure it's one of {', '.join(self.speakers)}")
        self.speaker = name
        self.speaker_chosen = True
        logger.info(f"Speaker {name} set")

    def download_model(self, url: str, model_path: str, show_progress: bool = True) -> None:
        self.model_path = model_path
        cache.ensure_model(self.model, model_path, show_progress)

    def fetch_speakers(self, device: str = "cpu") -> List[str]:
        engine = _load_engine(self.model_path, device, None)
        self._adopt_speakers(engine)
        return self.speakers

    def _adopt_speakers(self, engine: Any) -> None:
        loaded = list(getattr(engine, "speakers", None) or [])
        if loaded:
            self.speakers = loaded
            self.exhaustive = True
            if self.speaker not in loaded:
                if self.speaker_chosen:
                    raise IncorrectSpeaker(f"Speaker invalid! Ensure it's one of {', '.join(loaded)}")
                logger.warning(f"Default speaker {self.speaker} is not in the model, using {loaded[0]}")
                self.speaker = loaded[0]


class Synthesizer:
    def __init__(
        self,
        model: Optional[Model] = None,
        device: str = "cpu",
        threads: Optional[int] = None,
        sample_rate: int = 48000,
        max_chars: int = 500,
        pause: float = 0.25,
        warn_mixed_language: bool = True,
    ) -> None:
        self._check_sample_rate(sample_rate)
        if max_chars < 1:
            raise ValueError("max_chars must be positive")

        self.model = model if model is not None else Model()
        self.audio = AudioManager()
        self.sample_rate = sample_rate
        self.max_chars = max_chars
        self.pause = max(0.0, pause)
        self.warn_mixed_language = warn_mixed_language
        self.device = device

        self._tts = _load_engine(self.model.model_path, device, threads)
        self.model._adopt_speakers(self._tts)
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

    def _warn_mixed(self, text: str, ssml: bool) -> None:
        script = self.model.script
        if not self.warn_mixed_language or script is None:
            return
        words = foreign_words(text, script)
        if not words:
            return
        other = "Latin" if script == "cyrillic" else "Cyrillic"
        expected = script.capitalize()
        examples = ", ".join(dict.fromkeys(words[:5]))
        logger.warning(
            f"Model {self.model.model} is a {expected} model but the text contains {other} words "
            f"({examples}). They will likely be skipped or mispronounced"
        )

    def _request(self, chunk: str, speaker: str, rate: int, prosody_rate: int, ssml: bool) -> Dict[str, Any]:
        arguments: Dict[str, Any] = {"speaker": speaker, "sample_rate": rate}
        if ssml:
            arguments["ssml_text"] = chunk
        elif prosody_rate != 100:
            arguments["ssml_text"] = f"<speak><prosody rate='{prosody_rate}%'>{escape(chunk)}</prosody></speak>"
        else:
            arguments["text"] = chunk
        return arguments

    def generate(
        self,
        text: str,
        prosody_rate: int = 100,
        speaker: Optional[str] = None,
        sample_rate: Optional[int] = None,
        ssml: bool = False,
    ) -> np.ndarray:
        if not text or not text.strip():
            raise SynthesisError("There is no text to synthesize")

        speaker = speaker or self.model.speaker
        if speaker not in self.model.speakers:
            raise IncorrectSpeaker(f"Speaker invalid! Ensure it's one of {', '.join(self.model.speakers)}")

        rate = sample_rate or self.sample_rate
        self._check_sample_rate(rate)
        self._warn_mixed(text, ssml)

        chunks = [text] if ssml else split_text(text, self.max_chars)
        silence = np.zeros(int(self.pause * rate), dtype=np.float32)
        parts: List[np.ndarray] = []
        for index, chunk in enumerate(chunks):
            try:
                audio = self._tts.apply_tts(**self._request(chunk, speaker, rate, prosody_rate, ssml))
            except Exception as error:
                raise SynthesisError(f"There was an error synthesizing this text: {chunk}. {error}") from error
            if index and silence.size:
                parts.append(silence)
            parts.append(_to_array(audio))

        logger.info(f"Audio synthesized ({len(chunks)} chunk{'s' if len(chunks) != 1 else ''})")
        return np.concatenate(parts)

    def synthesize(
        self,
        text: str,
        path: Union[PathLike, BinaryIO] = "audio.wav",
        prosody_rate: int = 100,
        speaker: Optional[str] = None,
        sample_rate: Optional[int] = None,
        ssml: bool = False,
    ) -> Any:
        target: Any = path
        if isinstance(path, (str, os.PathLike)):
            target = os.fspath(path)
            if not target.lower().endswith(".wav"):
                raise InvalidAudioFormat("Incorrect audio format! Ensure that path leads to a .wav file")

        rate = sample_rate or self.sample_rate
        audio = self.generate(text, prosody_rate, speaker, rate, ssml)

        if isinstance(target, str):
            os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
        write_wav(target, audio, rate)
        return path

    def synthesize_bytes(
        self,
        text: str,
        prosody_rate: int = 100,
        speaker: Optional[str] = None,
        sample_rate: Optional[int] = None,
        ssml: bool = False,
    ) -> bytes:
        rate = sample_rate or self.sample_rate
        return wav_bytes(self.generate(text, prosody_rate, speaker, rate, ssml), rate)

    def say(
        self,
        text: str,
        path: Optional[PathLike] = None,
        prosody_rate: int = 100,
        speaker: Optional[str] = None,
        sample_rate: Optional[int] = None,
        ssml: bool = False,
        blocking: bool = True,
    ) -> Playback:
        cleanup: Optional[Callable[[], None]] = None
        if path is None:
            handle, temporary = tempfile.mkstemp(suffix=".wav", prefix="voicesynth_")
            os.close(handle)
            target = temporary

            def remove_temporary() -> None:
                if os.path.exists(temporary):
                    os.remove(temporary)

            cleanup = remove_temporary
        else:
            target = os.fspath(path)

        try:
            self.synthesize(text, target, prosody_rate, speaker, sample_rate, ssml)
            playback = self.audio.play_audio(target, blocking=False, cleanup=cleanup)
        except BaseException:
            if cleanup is not None:
                cleanup()
            raise

        if blocking:
            playback.wait()
        return playback

    async def synthesize_async(self, *args: Any, **kwargs: Any) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, functools.partial(self.synthesize, *args, **kwargs))

    async def say_async(self, *args: Any, **kwargs: Any) -> Playback:
        loop = asyncio.get_running_loop()
        kwargs["blocking"] = False
        playback = await loop.run_in_executor(None, functools.partial(self.say, *args, **kwargs))
        await playback.wait_async()
        return playback
