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

import importlib
import os
import logging
import subprocess
import sys

# disabling playsound module logging
logging.getLogger("playsound").setLevel(logging.ERROR)

import playsound
import torch

from typing import Literal, List

from .utils import (
    install, installed
)
from .utils.exceptions import *

from .models import (
    models, show_available_models
)


def disable_logging():
    logging.disable(logging.ERROR)


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

        logging.info("Model initialized")

        # Ensuring that model is a PyTorch one
        if not self.model_path.endswith(".pt"):
            raise IncorrectModelPath("Model file path should end with .pt!")

        self.download_model(self.url, self.model_path, show_download)

    def set_speaker(self, name):
        if name in models[self.model]["speakers"]:
            # noinspection PyAttributeOutsideInit
            self.speaker = name
            logging.info(f"Speaker {name} set")
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
            logging.info("Downloading synthesis model")
            torch.hub.download_url_to_file(url, f"{self.model_path}",
                                           progress=show_progress)
        else:
            logging.info("Setting existing model...")


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

        logging.info("Synthesizer configured")

        # setting torch configuration
        device = torch.device("cpu")
        torch.set_num_threads(16)

        # initialize sample rate
        self.sample_rate = 48000

        # creating model
        self.model_download = torch.package.PackageImporter(
            f"{self.model.model_path}").load_pickle("tts_models", "model")
        self.model_download.to(device)

        logging.info("Model imported to torch tts")

    def say(self, text: str, path: str = "audio.wav", prosody_rate: int = 100, delete_file: bool = False,
            module: Literal["playsound", "pygame", "pydub"] = "playsound") -> None:
        """
        Function for saying something
        :param prosody_rate: relative speed for saying
        :param path: path for audio to be saved in. Should be a .wav file
        :param text: text for saying
        :param delete_file: if set True, file is being deleted after playing
        :param module: module to use for audio playing
        """
        if not path.endswith(".wav"):
            raise InvalidAudioFormat("Incorrect audio format! Ensure that path leads to a .wav file")

        self.synthesize(text, path, prosody_rate)

        getattr(self.audio, f"play_{module}")(path, delete_file)

    def synthesize(self, text: str, path: str = "audio.wav", prosody_rate: int = 100) -> None:
        try:
            self.model_download.save_wav(ssml_text=f"<speak><prosody rate='{prosody_rate}%'>{text}</prosody></speak>",
                                         speaker=self.model.speaker,
                                         sample_rate=self.sample_rate,
                                         audio_path=path)
            logging.info("Audio synthesyzed")
        except Exception:
            raise SynthesisError(
                "There was en error synthesizing text. Ensure all parameters are inputed correctly")


def _player(path: str, remove_after: bool = True):
    def decorator(func):
        def wrapper():
            if os.path.exists(path):
                func()
                logging.info("Audio played")
                if remove_after:
                    os.remove(path)
            else:
                raise InvalidAudioPath("Specified path for playing does not exist")

        return wrapper

    return decorator


def _install_audio_package(name: str):
    if not installed(name):
        logging.info(f"{name} is not installed, voicesynth will attempt to install it for you...")
        try:
            package = install(name, output=False)
            if not package:
                logging.info(
                    f"{name} installation failed. Try installing it manually using '{sys.executable} -m 'pip install {name}'.")
                return
            else:
                globals()[name] = package
        except Exception:
            raise PackageInstallatioError(f"Unexpected exception raised while trying to install {name}")
    else:
        globals()[name] = importlib.import_module(name)


class AudioManager:
    @staticmethod
    def play_playsound(path: str, remove_after: bool = False):
        _install_audio_package("playsound")

        @_player(path, remove_after)
        def play():
            playsound.playsound(path)

        play()

    @staticmethod
    def play_pygame(path: str, remove_after: bool = False):

        from os import environ
        environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

        _install_audio_package("pygame")

        pygame.init()
        pygame.mixer.init()

        @_player(path, remove_after)
        def play():
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

        play()

    @staticmethod
    def play_pydub(path: str, remove_after: bool = False):
        _install_audio_package("pydub")

        from pydub.playback import play as pdbplay

        if sys.platform == "linux":
            subprocess.run(["jack_control", "start"])

        @_player(path, remove_after)
        def play():
            pdbplay(pydub.AudioSegment.from_wav(path))

        play()
