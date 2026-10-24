import pytest

from voicesynth import integrity
from voicesynth.exceptions import ModelIntegrityError

from conftest import make_package


def write(tmp_path, data):
    path = tmp_path / "m.pt"
    path.write_bytes(data)
    return str(path)


def test_valid_package_records_checksum(tmp_path):
    path = write(tmp_path, make_package())
    digest = integrity.verify_model(path)
    assert digest == integrity.sha256_file(path)
    assert (tmp_path / "m.pt.sha256").read_text().strip() == digest


def test_second_verification_uses_sidecar(tmp_path):
    path = write(tmp_path, make_package())
    integrity.verify_model(path)
    assert integrity.verify_model(path)


def test_missing_file(tmp_path):
    with pytest.raises(ModelIntegrityError):
        integrity.verify_model(str(tmp_path / "none.pt"))


def test_not_a_zip(tmp_path):
    with pytest.raises(ModelIntegrityError):
        integrity.verify_model(write(tmp_path, b"not a package"))


def test_truncated_package(tmp_path):
    with pytest.raises(ModelIntegrityError):
        integrity.verify_model(write(tmp_path, make_package()[:-100]))


def test_corrupted_payload_fails_crc(tmp_path):
    data = bytearray(make_package())
    data[200] ^= 0xFF
    with pytest.raises(ModelIntegrityError):
        integrity.verify_model(write(tmp_path, bytes(data)))


def test_checksum_mismatch(tmp_path):
    path = write(tmp_path, make_package())
    (tmp_path / "m.pt.sha256").write_text("0" * 64 + "\n")
    with pytest.raises(ModelIntegrityError, match="Checksum mismatch"):
        integrity.verify_model(path)
