import hashlib
import os
import zipfile

from voicesynth.exceptions import ModelIntegrityError

CHECKSUM_SUFFIX = ".sha256"


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checksum_path(path: str) -> str:
    return path + CHECKSUM_SUFFIX


def record_checksum(path: str) -> str:
    digest = sha256_file(path)
    with open(checksum_path(path), "w", encoding="ascii") as target:
        target.write(digest + "\n")
    return digest


def verify_model(path: str) -> str:
    if not os.path.isfile(path):
        raise ModelIntegrityError(f"Model file does not exist: {path}")

    if not zipfile.is_zipfile(path):
        raise ModelIntegrityError(f"Model file is not a valid PyTorch package: {path}")

    try:
        with zipfile.ZipFile(path) as archive:
            broken = archive.testzip()
    except (zipfile.BadZipFile, OSError) as error:
        raise ModelIntegrityError(f"Model file is corrupted: {path} ({error})") from error
    if broken is not None:
        raise ModelIntegrityError(f"Model file is corrupted: {path} (bad entry {broken})")

    actual = sha256_file(path)
    sidecar = checksum_path(path)
    if os.path.isfile(sidecar):
        with open(sidecar, encoding="ascii") as source:
            expected = source.read().strip()
        if expected != actual:
            raise ModelIntegrityError(f"Checksum mismatch for {path}: expected {expected}, got {actual}")
    else:
        with open(sidecar, "w", encoding="ascii") as target:
            target.write(actual + "\n")
    return actual
