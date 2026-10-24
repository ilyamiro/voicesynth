import os

import pytest

import voicesynth.voicesynth as core
from voicesynth.cli import main

from conftest import FakeEngine


def test_models_command(capsys):
    assert main(["models", "--language", "german"]) == 0
    assert "v3_de" in capsys.readouterr().out


def test_speakers_command(capsys):
    assert main(["speakers", "v3_fr"]) == 0
    assert capsys.readouterr().out.split() == [f"fr_{i}" for i in range(6)] + ["random"]


def test_speakers_incomplete_list_hint(capsys):
    main(["speakers", "v3_de"])
    assert "--load" in capsys.readouterr().err


def test_speakers_unknown_model(capsys):
    assert main(["speakers", "nope"]) == 1
    assert "Unknown model" in capsys.readouterr().err


def test_speakers_load(fake_model, monkeypatch, capsys):
    monkeypatch.setattr(core, "_load_engine", lambda *a: FakeEngine(["es_0", "real_one"]))
    assert main(["speakers", fake_model, "--load"]) == 0
    assert capsys.readouterr().out.split() == ["es_0", "real_one"]


def test_say_saves_without_playing(fake_model, monkeypatch, tmp_path):
    monkeypatch.setattr(core, "_load_engine", lambda *a: FakeEngine(["es_0"]))
    output = tmp_path / "o.wav"
    code = main(["say", "hola", "-m", fake_model, "-o", str(output), "--no-play", "--quiet", "--sample-rate", "8000"])
    assert code == 0 and output.exists()


def test_say_no_play_requires_output(capsys):
    assert main(["say", "hi", "--no-play"]) == 2
    assert "--output" in capsys.readouterr().err


def test_say_reads_stdin(fake_model, monkeypatch, tmp_path):
    import io

    monkeypatch.setattr(core, "_load_engine", lambda *a: FakeEngine(["es_0"]))
    monkeypatch.setattr("sys.stdin", io.StringIO("from stdin"))
    output = tmp_path / "s.wav"
    assert main(["say", "-m", fake_model, "-o", str(output), "--no-play", "--quiet"]) == 0
    assert output.exists()


def test_say_reports_errors(fake_model, monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(core, "_load_engine", lambda *a: FakeEngine(["es_0"]))
    code = main(["say", "hola", "-m", fake_model, "-s", "ghost", "-o", str(tmp_path / "e.wav"), "--no-play", "--quiet"])
    assert code == 1
    assert "voicesynth:" in capsys.readouterr().err


def test_cache_commands(fake_model, cache_home, capsys):
    assert main(["cache", "path"]) == 0
    assert capsys.readouterr().out.strip() == str(cache_home)

    main(["cache", "list"])
    assert "No models downloaded" in capsys.readouterr().out

    assert main(["cache", "download", fake_model]) == 0
    assert os.path.isfile(cache_home / f"{fake_model}.pt")

    main(["cache", "list"])
    assert fake_model in capsys.readouterr().out

    assert main(["cache", "verify"]) == 0
    assert f"{fake_model}: ok" in capsys.readouterr().out

    assert main(["cache", "remove", fake_model]) == 0
    assert "removed" in capsys.readouterr().out
    assert main(["cache", "remove", fake_model]) == 0
    assert "not downloaded" in capsys.readouterr().out


def test_cache_verify_failure(fake_model, cache_home, capsys):
    main(["cache", "download", fake_model])
    with open(cache_home / f"{fake_model}.pt", "r+b") as handle:
        handle.seek(300)
        handle.write(b"\x01\x02")
    assert main(["cache", "verify", fake_model]) == 1


def test_cache_clear(fake_model, cache_home, capsys):
    main(["cache", "download", fake_model])
    capsys.readouterr()
    assert main(["cache", "clear"]) == 0
    assert "Removed 1" in capsys.readouterr().out


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as stop:
        main(["--version"])
    assert stop.value.code == 0
    assert "voicesynth" in capsys.readouterr().out
