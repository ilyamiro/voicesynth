import os

import pytest

from voicesynth import cache
from voicesynth.exceptions import IncorrectModel, ModelIntegrityError


def test_cache_dir_uses_override(cache_home):
    assert cache.cache_dir() == str(cache_home)
    assert cache.default_model_path("v3_en") == str(cache_home / "v3_en.pt")


def test_cache_dir_defaults_to_xdg(monkeypatch, tmp_path):
    monkeypatch.delenv("VOICESYNTH_HOME", raising=False)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    assert cache.cache_dir() == str(tmp_path / "voicesynth")


def test_download_and_list(fake_model):
    path = cache.download(fake_model, show_progress=False)
    assert os.path.isfile(path)
    entries = cache.cached_models()
    assert [entry.name for entry in entries] == [fake_model]
    assert entries[0].known and entries[0].size > 0


def test_download_is_idempotent(fake_model, server):
    cache.download(fake_model, show_progress=False)
    cache.download(fake_model, show_progress=False)
    assert len(server.requests) == 1


def test_corrupted_model_is_downloaded_again(fake_model, server):
    path = cache.download(fake_model, show_progress=False)
    with open(path, "r+b") as handle:
        handle.seek(300)
        handle.write(b"\xff\xff\xff")
    cache.download(fake_model, show_progress=False)
    assert len(server.requests) == 2
    assert cache.verify(fake_model)


def test_bad_download_is_rejected_and_removed(cache_home, fake_model, server):
    server.files["/v3_es.pt"] = b"definitely not a zip"
    with pytest.raises(ModelIntegrityError):
        cache.download(fake_model, show_progress=False)
    assert not os.path.exists(cache.default_model_path(fake_model))


def test_verify_detects_tampering(fake_model):
    path = cache.download(fake_model, show_progress=False)
    with open(path, "r+b") as handle:
        handle.seek(300)
        handle.write(b"\x00")
    with pytest.raises(ModelIntegrityError):
        cache.verify(fake_model)


def test_remove(fake_model):
    path = cache.download(fake_model, show_progress=False)
    assert cache.remove(fake_model) is True
    assert not os.path.exists(path)
    assert not os.path.exists(path + ".sha256")
    assert cache.remove(fake_model) is False


def test_remove_unknown_model(cache_home):
    with pytest.raises(IncorrectModel):
        cache.remove("nonexistent_model")


def test_clear_removes_everything(fake_model, cache_home):
    cache.download(fake_model, show_progress=False)
    (cache_home / "leftover.pt.part").write_bytes(b"partial")
    (cache_home / "custom.pt").write_bytes(b"custom")
    assert cache.clear() == 2
    assert os.listdir(cache_home) == []


def test_cached_models_empty_without_directory(cache_home):
    assert cache.cached_models() == []


def test_unknown_files_are_listed_as_unknown(cache_home):
    cache_home.mkdir()
    (cache_home / "custom.pt").write_bytes(b"12")
    entries = cache.cached_models()
    assert entries[0].name == "custom" and not entries[0].known
