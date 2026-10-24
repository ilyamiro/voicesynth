import os

import pytest

from voicesynth.download import download_file
from voicesynth.exceptions import ModelDownloadError


def fetch(server, destination, **options):
    options.setdefault("backoff", 0)
    options.setdefault("show_progress", False)
    download_file(server.url("/f.bin"), str(destination), **options)


def test_downloads_file(server, tmp_path):
    server.files["/f.bin"] = b"x" * 3000
    destination = tmp_path / "sub" / "f.bin"
    fetch(server, destination)
    assert destination.read_bytes() == b"x" * 3000
    assert not os.path.exists(f"{destination}.part")


def test_http_error_is_reported(server, tmp_path):
    with pytest.raises(ModelDownloadError, match="404"):
        fetch(server, tmp_path / "f.bin")


def test_resumes_existing_partial(server, tmp_path):
    payload = bytes(range(256)) * 40
    server.files["/f.bin"] = payload
    destination = tmp_path / "f.bin"
    (tmp_path / "f.bin.part").write_bytes(payload[:1000])
    fetch(server, destination)
    assert destination.read_bytes() == payload
    assert server.requests[0]["Range"] == "bytes=1000-"


def test_server_without_range_restarts(server, tmp_path):
    payload = bytes(range(256)) * 40
    server.files["/f.bin"] = payload
    server.support_range = False
    (tmp_path / "f.bin.part").write_bytes(b"garbage" * 10)
    fetch(server, tmp_path / "f.bin")
    assert (tmp_path / "f.bin").read_bytes() == payload


def test_retries_after_truncated_response(server, tmp_path):
    payload = bytes(range(256)) * 400
    server.files["/f.bin"] = payload
    server.truncate_budget = 1
    fetch(server, tmp_path / "f.bin")
    assert (tmp_path / "f.bin").read_bytes() == payload
    assert len(server.requests) == 2
    assert "Range" in server.requests[1]


def test_retries_server_errors(server, tmp_path):
    server.files["/f.bin"] = b"data" * 100
    server.fail_status = 503
    server.fail_budget = 2
    fetch(server, tmp_path / "f.bin")
    assert (tmp_path / "f.bin").read_bytes() == b"data" * 100


def test_gives_up_but_keeps_partial(server, tmp_path):
    payload = bytes(range(256)) * 400
    server.files["/f.bin"] = payload
    server.truncate_budget = 10
    with pytest.raises(ModelDownloadError, match="resume"):
        fetch(server, tmp_path / "f.bin", retries=1)
    assert not (tmp_path / "f.bin").exists()
    assert os.path.getsize(tmp_path / "f.bin.part") > 0


def test_invalid_partial_longer_than_file_is_discarded(server, tmp_path):
    payload = b"short" * 10
    server.files["/f.bin"] = payload
    (tmp_path / "f.bin.part").write_bytes(b"y" * 5000)
    fetch(server, tmp_path / "f.bin")
    assert (tmp_path / "f.bin").read_bytes() == payload


def test_progress_is_written_to_stderr(server, tmp_path, capsys):
    server.files["/f.bin"] = b"z" * 2000
    fetch(server, tmp_path / "f.bin", show_progress=True)
    assert "100%" in capsys.readouterr().err
