"""
Voice Synthesizing package
Author: ilyamiro

Available on pip:
pip install voicesynth

This package was created for realistic voice-synthesis

Copyright [2024] [Ilya Miro]

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import logging


def _disable_loggers():
    """
    Disables all logs produced by imported modules

    DEPRECATED
    """
    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    for logg in loggers:
        logg.setLevel(logging.ERROR)


import os
import subprocess
import sys

from importlib.util import find_spec

from typing import Literal, List, Union

if sys.platform == "win32":
    import playsound

from voicesynth.exceptions import *

from voicesynth.models import (
    models, show_available_models
)

try:
    import torch
except ModuleNotFoundError:
    raise PackageError(
        "PyTorch is not installed. For a lightweight CPU-only installation, use: "
        "pip install torch --index-url https://download.pytorch.org/whl/cpu"
    )

class CustomLogger(logging.Logger):
    def __init__(self):
        super().__init__("Voicesynth", level=logging.NOTSET)
        self._setup()

    def _setup(self):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(fmt="Voicesynth - %(asctime)s - %(message)s", datefmt="%Y-%b-%d %H:%M:%S"))
        self.addHandler(handler)


logger = CustomLogger()


def disable_logging():
    """
    Disables voicesynth logging
    """
    logger.disabled = True


def installed(name: str) -> bool:
    """
    A function for checking if the specified package is installed in venv
    :param name: name of the package
    :return: True if package is installed False otherwise
    """
    return False if not find_spec(name) else True


class Model:
    """
    TTS Model class for Synthesizer
    """

    def __init__(self, model: str, model_path: str, show_download: bool = True):
        self.model = model  # name of the model
        self.model_path = model_path  # path to the model for downloading
        try:
            self.url = models[model]["url"]
            self.speakers = models[model]["speakers"]
            self.set_speaker(self.speakers[0])
        except KeyError:
            error_msg = "Model invalid. Ensure it's one of "
            for key in models.keys():
                error_msg += f"{key}, "
            raise IncorrectModel(error_msg)

        logger.info("Model configured")

        # Ensuring that model is a PyTorch one
        if not self.model_path.endswith(".pt"):
            raise IncorrectModelPath("Model file path should end with .pt!")

        self.download_model(self.url, self.model_path, show_download)

    def set_speaker(self, name):
        if name in models[self.model]["speakers"]:
            # noinspection PyAttributeOutsideInit
            self.speaker = name
            logger.info(f"Speaker {name} set")
        else:
            error_msg = "Speaker invalid! Ensure it's one of "
            for speaker in models[self.model]["speakers"]:
                error_msg += f"{speaker}, "
            raise IncorrectSpeaker(error_msg)

    def download_model(self, url: str, model_path: str, show_progress: bool = True) -> None:
        """
        Function for downloading voice model
        :param url: url for model downloading
        :param show_progress: if to show model's downloading process
        :param model_path: path for model saving
        """
        self.model_path = model_path
        # downloading model from source
        if not os.path.exists(f"{self.model_path}"):
            logger.info("Downloading synthesis model")
            torch.hub.download_url_to_file(url, f"{self.model_path}",
                                           progress=show_progress)
        else:
            logger.info("Setting up existing model")


class Synthesizer:
    """
    Class for synthesizing text
    Based on silero-tts models from https://github.com/snakers4/silero-models
    """

    def __init__(self, model: Model) -> None:
        """
        Synthesizer initializing
        """

        # Parameters for synthesis
        self.model = model
        self.audio = AudioManager()

        logger.info("Synthesizer configured")

        # setting torch configuration
        device = torch.device("cpu")
        torch.set_num_threads(16)

        logger.info("PyTorch device configured: Cpu, 16 threads")
        # initialize sample rate
        self.sample_rate = 48000

        # creating model
        self.model_download = torch.package.PackageImporter(
            f"{self.model.model_path}").load_pickle("tts_models", "model")
        self.model_download.to(device)

        logger.info("Model imported to torch tts")

    def say(self, text: str, path: str = "audio.wav", prosody_rate: int = 100) -> None:
        """
        Function for saying something
        :param prosody_rate: relative speed for saying
        :param path: path for audio to be saved in. Should be a .wav file
        :param text: text for saying
        """
        if not path.endswith(".wav"):
            raise InvalidAudioFormat("Incorrect audio format! Ensure that path leads to a .wav file")

        self.synthesize(text, path, prosody_rate)

        self.audio.play_audio(path)

    def synthesize(self, text: str, path: str = "audio.wav", prosody_rate: int = 100) -> None:
        try:
            self.model_download.save_wav(ssml_text=f"<speak><prosody rate='{prosody_rate}%'>{text}</prosody></speak>",
                                         speaker=self.model.speaker,
                                         sample_rate=self.sample_rate,
                                         audio_path=path)

            logger.info("Audio synthesized")
        except Exception:
            raise SynthesisError(
                f"There was en error synthesizing this text: {text}. Ensure all parameters are inputted correctly")


def _player(path: str):
    """
    Player decorator for checking specified path before playing.
    """
    def decorator(func):
        def wrapper():
            # checking if the path exists
            if os.path.exists(path):
                func()
                logger.info(f"File {path} played")
            else:
                raise InvalidAudioPath("Specified path for playing does not exist")
        return wrapper
    return decorator


class AudioManager:
    @staticmethod
    def play_audio(path: str):
        @_player(path)
        def play():
            if sys.platform == "win32":
                playsound.playsound(path)
            elif sys.platform == "linux":
                linux_players = ["paplay", "pw-play", "aplay"]
                played = False
                
                for player in linux_players:
                    try:
                        subprocess.run(
                            [player, path], 
                            check=True, 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL
                        )
                        played = True
                        break  # Stop trying if successful
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
                
                if not played:
                    logger.error("No suitable audio player found on Linux. Ensure PulseAudio, PipeWire, or ALSA is installed.")
            elif sys.platform == "darwin":
                # Fallback for macOS users just in case
                try:
                    subprocess.run(["afplay", path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    playsound.playsound(path)
            else:
                playsound.playsound(path)

        play()
