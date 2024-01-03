"""
Utils for voicesynth
"""
import logging

from rich import print
from rich.logging import RichHandler
from rich.table import Table

from . import config

models = {
    "v4_ru": {"url": "https://models.silero.ai/models/tts/ru/v4_ru.pt",
              "speakers": ['aidar', 'baya', 'kseniya', 'xenia', 'eugene']},
    "v4_ua": {"url": "https://models.silero.ai/models/tts/ua/v4_ua.pt", "speakers": ["mykyta"]},
    "v3_en": {"url": "https://models.silero.ai/models/tts/en/v3_en.pt", "speakers": [f'en_{i}' for i in range(118)]},
    "v3_de": {"url": "https://models.silero.ai/models/tts/de/v3_de.pt", "speakers": ["eva_k", "karlsson"]},
    "v3_es": {"url": "https://models.silero.ai/models/tts/es/v3_es.pt", "speakers": ['es_0', 'es_1', 'es_2']},
    "v3_fr": {"url": "https://models.silero.ai/models/tts/fr/v3_fr.pt", "speakers": [f'fr_{i}' for i in range(6)]}
}


def show_available_models() -> None:
    """
    Beautifully prints out all available models
    """
    table_of_models = Table("Name", "Url", "Speakers", show_lines=True, title="Available Models",
                            title_style="bold red")
    for model, parameters in models.items():
        speakers = ""
        row_count = 0
        for speaker in parameters["speakers"]:
            row_count += 1
            speakers += f"{speaker}, "
            if row_count % 5 == 0:
                speakers += "\n"
        table_of_models.add_row(model, parameters["url"], speakers)
    print(table_of_models)


def logging_enabled(log_enable: bool):
    config.log_enable = log_enable


class VoiceSynthLogger(logging.Logger):
    """
    Logger class
    """
    def __init__(self, name: str, level=logging.NOTSET):
        super().__init__(name, level)
        self._setup()

    def _setup(self) -> None:
        """
        Setting logger parameters
        """
        handler = RichHandler()
        self.addHandler(handler)

    def out(self, text) -> None:
        """
        Helper function for logging
        :param text: log message
        """
        if config.log_enable:
            self.log(level=logging.INFO, msg=text)


# setting logger up
logger = VoiceSynthLogger("SynthLog")



