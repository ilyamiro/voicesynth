import os
from dataclasses import dataclass
from typing import List

from voicesynth import integrity
from voicesynth.download import download_file
from voicesynth.exceptions import IncorrectModel, ModelIntegrityError
from voicesynth.log import logger
from voicesynth.models import get_model_info, models


@dataclass
class CachedModel:
    name: str
    path: str
    size: int
    known: bool


def cache_dir() -> str:
    override = os.environ.get("VOICESYNTH_HOME")
    if override:
        return os.path.expanduser(override)
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    return os.path.join(base, "voicesynth")


def default_model_path(model: str) -> str:
    return os.path.join(cache_dir(), f"{model}.pt")


def _artifacts(path: str) -> List[str]:
    return [path, integrity.checksum_path(path), path + ".part"]


def fetch_model(url: str, path: str, show_progress: bool = True) -> None:
    download_file(url, path, show_progress)
    try:
        integrity.verify_model(path)
    except ModelIntegrityError:
        for artifact in _artifacts(path):
            if os.path.exists(artifact):
                os.remove(artifact)
        raise


def ensure_model(name: str, path: str, show_progress: bool = True) -> str:
    url = get_model_info(name)["url"]
    if os.path.isfile(path):
        try:
            integrity.verify_model(path)
            logger.info("Setting up existing model")
            return path
        except ModelIntegrityError as error:
            logger.warning(f"{error}. Downloading the model again")
            for artifact in _artifacts(path):
                if os.path.exists(artifact):
                    os.remove(artifact)
    logger.info("Downloading synthesis model")
    fetch_model(url, path, show_progress)
    return path


def download(name: str, show_progress: bool = True) -> str:
    return ensure_model(name, default_model_path(name), show_progress)


def cached_models() -> List[CachedModel]:
    directory = cache_dir()
    if not os.path.isdir(directory):
        return []
    found = []
    for entry in sorted(os.listdir(directory)):
        if not entry.endswith(".pt"):
            continue
        path = os.path.join(directory, entry)
        name = entry[:-3]
        found.append(CachedModel(name, path, os.path.getsize(path), name in models))
    return found


def verify(name: str) -> str:
    path = default_model_path(name)
    return integrity.verify_model(path)


def remove(name: str) -> bool:
    if name not in models and not os.path.isfile(default_model_path(name)):
        raise IncorrectModel(f"Unknown model '{name}'")
    removed = False
    for artifact in _artifacts(default_model_path(name)):
        if os.path.exists(artifact):
            os.remove(artifact)
            removed = True
    return removed


def clear() -> int:
    count = 0
    for cached in cached_models():
        if remove(cached.name):
            count += 1
    directory = cache_dir()
    if os.path.isdir(directory):
        for entry in os.listdir(directory):
            if entry.endswith(".part"):
                os.remove(os.path.join(directory, entry))
    return count
