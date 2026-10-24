import shutil
import sys
from typing import Dict, List, Optional, TypedDict

from voicesynth.exceptions import IncorrectModel

BASE_URL = "https://models.silero.ai/models/tts"
SAMPLE_RATES = (8000, 24000, 48000)
DEFAULT_MODEL = "v5_6_ru"


class ModelInfo(TypedDict):
    url: str
    language: str
    speakers: List[str]
    exhaustive: bool
    script: Optional[str]


def _entry(path: str, language: str, speakers: List[str], exhaustive: bool = True) -> ModelInfo:
    return {
        "url": f"{BASE_URL}/{path}",
        "language": language,
        "speakers": speakers,
        "exhaustive": exhaustive,
        "script": None,
    }


models: Dict[str, ModelInfo] = {
    "v5_6_ru": _entry("ru/v5_6_ru.pt", "russian", ['aidar', 'baya', 'kseniya', 'xenia', 'eugene']),
    "v5_5_ru": _entry("ru/v5_5_ru.pt", "russian", ['aidar', 'baya', 'kseniya', 'xenia', 'eugene']),
    "v5_4_ru": _entry("ru/v5_4_ru.pt", "russian", ['aidar', 'baya', 'kseniya', 'xenia']),
    "v5_3_ru": _entry("ru/v5_3_ru.pt", "russian", ['aidar', 'baya', 'kseniya', 'xenia', 'eugene']),
    "v5_2_ru": _entry("ru/v5_2_ru.pt", "russian", ['aidar', 'baya', 'kseniya', 'xenia', 'eugene']),
    "v5_1_ru": _entry("ru/v5_1_ru.pt", "russian", ['aidar', 'baya', 'kseniya', 'xenia', 'eugene']),
    "v5_ru": _entry("ru/v5_ru.pt", "russian", ['aidar', 'baya', 'kseniya', 'xenia', 'eugene']),
    "v5_cis_base": _entry("ru/v5_cis_base.pt", "cis languages", ['aze_gamat', 'hye_zara', 'bak_aigul', 'bak_alfia', 'bak_alfia2', 'bak_miyau', 'bak_ramilia', 'bel_anatoliy', 'bel_dmitriy', 'bel_larisa', 'kat_vika', 'kbd_eduard', 'kaz_zhadyra', 'kaz_zhazira', 'xal_kejilgan', 'xal_kermen', 'kir_nurgul', 'mdf_oksana', 'tgk_onaoy', 'tgk_safarhuja', 'tat_albina', 'tat_marat', 'udm_bogdan', 'uzb_saida', 'ukr_igor', 'ukr_roman', 'kjh_karina', 'kjh_sibday', 'chv_ekaterina', 'erz_alexandr', 'sah_zinaida', 'ru_aze_gamat', 'ru_hye_zara', 'ru_bak_aigul', 'ru_bak_alfia', 'ru_bak_alfia2', 'ru_bak_miyau', 'ru_bak_ramilia', 'ru_bel_anatoliy', 'ru_bel_dmitriy', 'ru_bel_larisa', 'ru_kat_vika', 'ru_kbd_eduard', 'ru_kaz_zhadyra', 'ru_kaz_zhazira', 'ru_xal_kejilgan', 'ru_xal_kermen', 'ru_kir_nurgul', 'ru_mdf_oksana', 'ru_tgk_onaoy', 'ru_tgk_safarhuja', 'ru_tat_albina', 'ru_tat_marat', 'ru_udm_bogdan', 'ru_uzb_saida', 'ru_ukr_igor', 'ru_ukr_roman', 'ru_kjh_karina', 'ru_kjh_sibday', 'ru_chv_ekaterina', 'ru_erz_alexandr', 'ru_sah_zinaida']),
    "v5_cis_base_nostress": _entry("ru/v5_cis_base_nostress.pt", "cis languages", ['aze_gamat', 'hye_zara', 'bak_aigul', 'bak_alfia', 'bak_alfia2', 'bak_miyau', 'bak_ramilia', 'bel_anatoliy', 'bel_dmitriy', 'bel_larisa', 'kat_vika', 'kbd_eduard', 'kaz_zhadyra', 'kaz_zhazira', 'xal_kejilgan', 'xal_kermen', 'kir_nurgul', 'mdf_oksana', 'tgk_onaoy', 'tgk_safarhuja', 'tat_albina', 'tat_marat', 'udm_bogdan', 'uzb_saida', 'ukr_igor', 'ukr_roman', 'kjh_karina', 'kjh_sibday', 'chv_ekaterina', 'erz_alexandr', 'sah_zinaida', 'ru_aze_gamat', 'ru_hye_zara', 'ru_bak_aigul', 'ru_bak_alfia', 'ru_bak_alfia2', 'ru_bak_miyau', 'ru_bak_ramilia', 'ru_bel_anatoliy', 'ru_bel_dmitriy', 'ru_bel_larisa', 'ru_kat_vika', 'ru_kbd_eduard', 'ru_kaz_zhadyra', 'ru_kaz_zhazira', 'ru_xal_kejilgan', 'ru_xal_kermen', 'ru_kir_nurgul', 'ru_mdf_oksana', 'ru_tgk_onaoy', 'ru_tgk_safarhuja', 'ru_tat_albina', 'ru_tat_marat', 'ru_udm_bogdan', 'ru_uzb_saida', 'ru_ukr_igor', 'ru_ukr_roman', 'ru_kjh_karina', 'ru_kjh_sibday', 'ru_chv_ekaterina', 'ru_erz_alexandr', 'ru_sah_zinaida']),
    "v5_cis_ext": _entry("ru/v5_cis_ext.pt", "cis languages", ['kaz_abai', 'kaz_aidana', 'kaz_aisha', 'kaz_bakir', 'kaz_danara', 'xal_delghir', 'xal_erdni', 'tat_adiba', 'tat_alsou', 'tat_amir', 'tat_azat', 'tat_batir', 'tat_bulat', 'tat_damir', 'tat_guzel', 'tat_ildar', 'tat_ilgiz', 'tat_karim', 'tat_mansur', 'tat_murat', 'tat_rasima', 'tat_rustem', 'tat_timur', 'tat_zifa', 'tat_zufar', 'tat_zulfiya', 'uzb_anora', 'uzb_dilnavoz', 'ukr_kateryna', 'ukr_lada', 'ukr_mykyta', 'ukr_oleksa', 'ukr_tetiana', 'chv_aihwa', 'chv_alima']),
    "v5_turkic": _entry("ru/v5_turkic.pt", "turkic languages", ['chv_0', 'chv_1', 'crh_0', 'crh_1', 'crh_2', 'gag_0', 'gag_1', 'gag_2', 'kaa_0', 'kaa_1', 'kir_0', 'kjh_0', 'sah_0', 'sah_1', 'sah_2', 'sty_0', 'tat_0', 'tgk_0', 'tuk_0', 'tuk_1', 'tuk_2', 'tyv_0', 'uzb_0', 'xal_0', 'xal_1', 'xal_2']),
    "v5_caucasian": _entry("ru/v5_caucasian.pt", "caucasian languages", ['abq_0', 'abq_1', 'abq_2', 'ady_0', 'ady_1', 'ady_2', 'ady_3', 'agx_0', 'ava_0', 'che_0', 'che_1', 'che_2', 'che_3', 'che_4', 'darg_0', 'darg_1', 'inh_0', 'inh_1', 'kbd_0', 'kbd_1', 'kbd_2', 'krc_0', 'krc_1', 'krc_2', 'kum_0', 'kum_1', 'kum_2', 'lbe_0', 'lez_0', 'oss_0', 'tab_0', 'tab_1', 'tkr_0']),
    "v4_ru": _entry("ru/v4_ru.pt", "russian", ['aidar', 'baya', 'kseniya', 'xenia', 'eugene', 'random']),
    "v4_ua": _entry("ua/v4_ua.pt", "ukrainian", ['mykyta', 'random']),
    "v4_uz": _entry("uz/v4_uz.pt", "uzbek", ['dilnavoz']),
    "v4_cyrillic": _entry("cyr/v4_cyrillic.pt", "cyrillic languages", ['b_ava', 'b_bashkir', 'b_bulb', 'b_bulc', 'b_che', 'b_cv', 'cv_ekaterina', 'b_myv', 'b_kalmyk', 'b_krc', 'kz_M1', 'kz_M2', 'kz_F3', 'kz_F1', 'kz_F2', 'b_kjh', 'b_kpv', 'b_lez', 'b_mhr', 'b_mrj', 'b_nog', 'b_oss', 'b_ru', 'b_tat', 'marat_tt', 'b_tyv', 'b_udm', 'b_uzb', 'b_sah', 'kalmyk_erdni', 'kalmyk_delghir']),
    "v4_indic": _entry("indic/v4_indic.pt", "indic languages", ['hindi_male', 'hindi_female', 'random'], False),
    "v3_1_ru": _entry("ru/v3_1_ru.pt", "russian", ['aidar', 'baya', 'kseniya', 'xenia', 'random']),
    "v3_en": _entry("en/v3_en.pt", "english", [f"en_{i}" for i in range(118)] + ["random"]),
    "v3_en_indic": _entry("en/v3_en_indic.pt", "english (indic accents)", ['tamil_female', 'assamese_male', 'random'], False),
    "v3_de": _entry("de/v3_de.pt", "german", ['eva_k', 'karlsson', 'random'], False),
    "v3_es": _entry("es/v3_es.pt", "spanish", ['es_0', 'es_1', 'es_2', 'random']),
    "v3_fr": _entry("fr/v3_fr.pt", "french", [f"fr_{i}" for i in range(6)] + ["random"]),
    "v3_ua": _entry("ua/v3_ua.pt", "ukrainian", ['mykyta', 'random'], False),
    "v3_uz": _entry("uz/v3_uz.pt", "uzbek", ['dilnavoz', 'random'], False),
    "v3_tt": _entry("tt/v3_tt.pt", "tatar", ['dilyara', 'random'], False),
    "v3_xal": _entry("xal/v3_xal.pt", "kalmyk", ['erdni', 'delghir', 'random'], False),
    "v3_indic": _entry("indic/v3_indic.pt", "indic languages", ['hindi_male', 'hindi_female', 'random'], False),
}

_CYRILLIC = (
    "v5_6_ru", "v5_5_ru", "v5_4_ru", "v5_3_ru", "v5_2_ru", "v5_1_ru", "v5_ru", "v5_turkic",
    "v5_caucasian", "v4_ru", "v4_ua", "v4_cyrillic", "v3_1_ru", "v3_ua", "v3_tt", "v3_xal",
)
_LATIN = ("v4_uz", "v3_uz", "v4_indic", "v3_indic", "v3_en", "v3_en_indic", "v3_de", "v3_es", "v3_fr")

for _name in _CYRILLIC:
    models[_name]["script"] = "cyrillic"
for _name in _LATIN:
    models[_name]["script"] = "latin"


def get_model_info(name: str) -> ModelInfo:
    try:
        return models[name]
    except KeyError:
        raise IncorrectModel(f"Unknown model '{name}'. Ensure it's one of {', '.join(models)}") from None


def available_models(language: Optional[str] = None) -> List[str]:
    if language is None:
        return list(models)
    needle = language.lower()
    return [name for name, info in models.items() if needle in info["language"].lower()]


def _paint(text: str, code: str, enabled: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if enabled else text


def show_available_models(language: Optional[str] = None, max_speakers: int = 8) -> None:
    color = sys.stdout.isatty()
    names = available_models(language)
    if not names:
        print(f"No models found for language '{language}'")
        return

    width = shutil.get_terminal_size((120, 20)).columns
    name_w = max(len(n) for n in names) + 1
    lang_w = max(len(models[n]["language"]) for n in names) + 1
    header = f"{'Model':<{name_w}} {'Language':<{lang_w}} Speakers"
    print(_paint(header, "95", color))
    print("-" * min(width, len(header) + 60))

    for name in names:
        info = models[name]
        speakers = info["speakers"]
        shown = ", ".join(speakers[:max_speakers])
        if len(speakers) > max_speakers:
            shown += f", ... ({len(speakers)} total)"
        elif not info["exhaustive"]:
            shown += ", ..."
        name_col = _paint(name.ljust(name_w), "94", color)
        lang_col = _paint(info["language"].ljust(lang_w), "93", color)
        print(f"{name_col} {lang_col} {_paint(shown, '92', color)}")
