"""
Model utilities for voicesynth
"""

# all available models
models = {
    "v4_ru": {"url": "https://models.silero.ai/models/tts/ru/v4_ru.pt",
              "speakers": ['aidar', 'baya', 'kseniya', 'xenia', 'eugene'],
              "language": "russian"},
    "v4_ua": {"url": "https://models.silero.ai/models/tts/ua/v4_ua.pt",
              "speakers": ["mykyta"],
              "language": "ukranian"},
    "v3_en": {"url": "https://models.silero.ai/models/tts/en/v3_en.pt",
              "speakers": [f'en_{i}' for i in range(118)],
              "language": "english"},
    "v3_de": {"url": "https://models.silero.ai/models/tts/de/v3_de.pt",
              "speakers": ["eva_k", "karlsson"],
              "language": "german"},
    "v3_es": {"url": "https://models.silero.ai/models/tts/es/v3_es.pt",
              "speakers": ['es_0', 'es_1', 'es_2'],
              "language": "spanish"},
    "v3_fr": {"url": "https://models.silero.ai/models/tts/fr/v3_fr.pt",
              "speakers": [f'fr_{i}' for i in range(6)],
              "language": "french"}
}


def show_available_models() -> None:
    # Define color codes
    HEADER_COLOR = "\033[95m"
    MODEL_COLOR = "\033[94m"
    URL_COLOR = "\033[96m"
    LANGUAGE_COLOR = "\033[93m"  # Adding a new color for language
    SPEAKERS_COLOR = "\033[92m"
    END_COLOR = "\033[0m"

    # Print colored header
    print(f"{HEADER_COLOR} {'Model':<10}|   {'Url':<50}|   {'Language':<10}|   {'Speakers'}{END_COLOR}")
    print("-" * 160)

    # Print each model's information
    for model_name, model_info in models.items():
        model_url = model_info["url"]
        speakers = model_info["speakers"]
        language = model_info["language"]

        # Break speakers into rows with a maximum of 10 speakers per row
        rows = [speakers[i:i + 10] for i in range(0, len(speakers), 10)]

        # Print the first row with model, url, language, and speakers
        print(
            f"{MODEL_COLOR} {model_name:<10}{END_COLOR}|   {URL_COLOR}{model_url:<50}{END_COLOR}|   {LANGUAGE_COLOR}{language:<10}{END_COLOR}|   {SPEAKERS_COLOR}{', '.join(rows[0])}{END_COLOR}")

        # Print the remaining rows (if any) with model, url, language, and speakers blank
        for row in rows[1:]:
            # Apply color codes to the entire line
            print(
                f"{MODEL_COLOR} {'':<10}{END_COLOR}|   {URL_COLOR}{'':<50}{END_COLOR}|   {LANGUAGE_COLOR}{'':<10}{END_COLOR}|   {SPEAKERS_COLOR}{', '.join(row)}{END_COLOR}")

        # Print separation line between models
        print("-" * 160)




