import re

import pytest

from voicesynth.exceptions import IncorrectModel
from voicesynth.models import (
    DEFAULT_MODEL,
    SAMPLE_RATES,
    available_models,
    get_model_info,
    models,
    show_available_models,
)


def test_default_model_exists():
    assert DEFAULT_MODEL in models


def test_catalog_entries_are_well_formed():
    for name, info in models.items():
        assert re.fullmatch(r"https://models\.silero\.ai/models/tts/[a-z]+/[\w]+\.pt", info["url"]), name
        assert info["url"].endswith(f"/{name}.pt")
        assert info["speakers"], name
        assert len(set(info["speakers"])) == len(info["speakers"]), name
        assert info["language"], name
        assert info["script"] in (None, "latin", "cyrillic"), name


def test_newest_silero_models_are_present():
    for name in ("v5_6_ru", "v5_cis_base", "v5_cis_ext", "v5_turkic", "v5_caucasian"):
        assert name in models


def test_sample_rates():
    assert SAMPLE_RATES == (8000, 24000, 48000)


def test_get_model_info_unknown():
    with pytest.raises(IncorrectModel):
        get_model_info("v99_xx")


def test_available_models_filters_by_language():
    russian = available_models("russian")
    assert "v5_6_ru" in russian and "v3_en" not in russian
    assert available_models("RUSSIAN") == russian
    assert available_models("klingon") == []
    assert available_models() == list(models)


def test_show_available_models_output(capsys):
    show_available_models("english")
    output = capsys.readouterr().out
    assert "v3_en" in output
    assert "v5_6_ru" not in output
    assert "\033[" not in output


def test_show_available_models_no_match(capsys):
    show_available_models("klingon")
    assert "No models found" in capsys.readouterr().out
