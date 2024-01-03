"""
Voice Synthesizing package
Author: ilyamiro

Available on pip:
pip install voicesynth

This package was created for realistic voice-synthesis
"""
import datetime
import os
import time
import json
import threading

from playsound import playsound
import torch

from .utils import (
    logger,
    models,
    show_available_models,
    VoiceSynthError,
)
from .utils.exceptions import *


class Model:
    """
    TTS Model class for Synthesizer
    """

    def __init__(self, model: str, model_path: str):
        self.model = model  # name of the model
        self.speaker = None  # speaker changes model's synthesized voice
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

        logger.out("Model initialized")

        if not self.model_path.endswith(".pt"):
            raise IncorrectModelPath("Model file path should end with .pt!")

        self.download_model(self.url, self.model_path)

    def set_speaker(self, name):
        if name in models[self.model]["speakers"]:
            self.speaker = name
            logger.out(f"Speaker {name} set")
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
            logger.out("Downloading synthesis model")
            torch.hub.download_url_to_file(url, f"{self.model_path}",
                                           progress=show_progress)
        else:
            logger.out("Setting existing model...")


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
        self.speaker = None
        self.audio_path = None

        logger.out("Synthesizer configured")

        # setting torch configuration
        device = torch.device("cpu")
        torch.set_num_threads(16)

        # initialize sample rate
        self.sample_rate = 48000

        # creating model
        self.model_download = torch.package.PackageImporter(
            f"{self.model.model_path}").load_pickle("tts_models", "model")
        self.model_download.to(device)

        logger.out("Model imported to torch tts")

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

        # playing audio from file using playsound.
        try:
            self.play(self.audio_path)
        except Exception:
            raise AudioPlayingError("There was an error playing synthesized audio")

    def synthesize(self, text: str, path: str = "audio.wav", prosody_rate: int = 100) -> None:
        try:
            self.audio_path = path
            self.model_download.save_wav(ssml_text=f"<speak><prosody rate='{prosody_rate}%'>{text}</prosody></speak>",
                                         speaker=self.model.speaker,
                                         sample_rate=self.sample_rate,
                                         audio_path=path)
            logger.out("Audio synthesyzed")
        except Exception:
            raise SynthesisError(
                "There was en error synthesizing text. Ensure all parameters are inputed correctly")

    def set_speaker(self, speaker: str):
        """
        Function for changing voice model's speaker
        :param speaker: speaker name
        """
        if speaker in self.model.speakers:
            self.speaker = speaker
            logger.out(f"Speaker {speaker} set")

    @staticmethod
    def play(path):
        if os.path.exists(path):
            playsound(path)
            logger.out(f"Audio {path} played")
        else:
            raise InvalidAudioPath("Specified audio file path does not exist")
