import logging

logger = logging.getLogger("voicesynth")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(
        logging.Formatter(fmt="Voicesynth - %(asctime)s - %(message)s", datefmt="%Y-%b-%d %H:%M:%S")
    )
    logger.addHandler(_handler)


def disable_logging() -> None:
    logger.disabled = True


def enable_logging() -> None:
    logger.disabled = False
