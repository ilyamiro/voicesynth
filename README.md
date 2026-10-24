<h2>voicesynth</h2>
<strong>Offline voice synthesis library</strong> <br><br>

> [!NOTE]
> The project uses [Silero TTS](https://github.com/snakers4/silero-models) models

### Install

```bash
pip install voicesynth
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

PyTorch is not pulled in automatically so you can pick the build you want (CPU, CUDA, ...). `pip install voicesynth[torch]` installs the default one.

### Quick start

```python
from voicesynth import Model, Synthesizer

synthesizer = Synthesizer(Model("v5_6_ru"))
synthesizer.say("В н+едрах т+ундры в+ыдры в г+етрах т+ырят в в+ёдра +ядра к+едров.")
```

The model is downloaded on first use into `~/.cache/voicesynth` (override with `model_path=` or the `VOICESYNTH_HOME` environment variable).

### Models

```python
from voicesynth import show_available_models, available_models

show_available_models()
show_available_models("tatar")
available_models("russian")
```

| Family | Models |
| --- | --- |
| Russian | `v5_6_ru`, `v5_5_ru`, `v5_4_ru`, `v5_3_ru`, `v5_2_ru`, `v5_1_ru`, `v5_ru`, `v4_ru`, `v3_1_ru` |
| CIS languages | `v5_cis_base`, `v5_cis_base_nostress`, `v5_cis_ext` |
| Turkic / Caucasian | `v5_turkic`, `v5_caucasian` |
| Cyrillic | `v4_cyrillic` |
| Ukrainian / Uzbek / Tatar / Kalmyk | `v4_ua`, `v3_ua`, `v4_uz`, `v3_uz`, `v3_tt`, `v3_xal` |
| Indic | `v4_indic`, `v3_indic`, `v3_en_indic` |
| English / German / Spanish / French | `v3_en`, `v3_de`, `v3_es`, `v3_fr` |

`v5_cis_base`, `v5_cis_ext`, `v5_turkic` and `v5_caucasian` expect stress marks (`к+ошка`) in the text; the `nostress` variant needs them only for Slavic languages. Speakers are prefixed with the language code, for example `tat_albina` or `kaz_abai`.

### Speakers and speed

```python
model = Model("v3_en", speaker="en_73")
model.set_speaker("en_12")

synthesizer = Synthesizer(model)
synthesizer.say("Hello there", speaker="en_5", prosody_rate=90)
print(synthesizer.speakers)
```

### Saving audio and other outputs

```python
synthesizer.synthesize("Saved for later", path="audio.wav")
synthesizer.say("Saved and played", path="audio.wav")

wav = synthesizer.synthesize_bytes("In memory")
samples = synthesizer.generate("As a numpy array")
synthesizer.synthesize("Into a buffer", io.BytesIO())
```

`say()` without a path plays through a temporary file. Pass `ssml=True` to send your own SSML, `sample_rate=` (8000, 24000 or 48000) to change quality, and `device="cuda"` or `threads=4` to the `Synthesizer` constructor.

### Long text

Text longer than `max_chars` (500 by default) is split on sentence and clause boundaries, synthesized piece by piece and joined with `pause` seconds of silence:

```python
synthesizer = Synthesizer(model, max_chars=300, pause=0.4)
from voicesynth import split_text
split_text(long_text, 300)
```

### Non-blocking playback and asyncio

```python
playback = synthesizer.say("Talking in the background", blocking=False)
playback.is_playing
playback.wait(timeout=2)
playback.stop()

await synthesizer.say_async("Does not block the event loop")
await synthesizer.synthesize_async("hello", "hello.wav")
```

Audio playback is native: `winsound` on Windows, `afplay` on macOS and the first available of `paplay`, `pw-play`, `aplay`, `ffplay`, `mpv`, `play` on Linux.

### Speakers

Some catalog entries (Indic, German, Tatar, Kalmyk and a few more) list only the speakers known in advance. After loading a model, `synthesizer.speakers` holds the real list. Without creating a synthesizer:

```python
Model("v3_de").fetch_speakers()
```

### Model cache

Models are stored in `~/.cache/voicesynth` (or `$VOICESYNTH_HOME`). Every download is checked: the size, the archive CRCs and a SHA-256 checksum saved next to the file, which is re-verified on every `Model(...)`. A damaged file is deleted and downloaded again. Interrupted downloads resume where they stopped.

```python
from voicesynth import cache

cache.download("v3_en")
cache.cached_models()
cache.verify("v3_en")
cache.remove("v3_en")
cache.clear()
```

### Mixed language text

Cyrillic models read Cyrillic and Latin models read Latin letters. When text contains words in the other script, a warning is logged because those words are skipped or mispronounced. Silence it with `Synthesizer(model, warn_mixed_language=False)`.

### Command line

```bash
voicesynth models
voicesynth models --language russian
voicesynth speakers v3_en
voicesynth speakers v3_de --load
voicesynth say "Hello world" -m v3_en -s en_73
voicesynth say "Saved only" -m v3_en -o hello.wav --no-play
echo "Piped text" | voicesynth say -m v3_en
voicesynth cache list
voicesynth cache download v3_en v5_6_ru
voicesynth cache verify
voicesynth cache remove v3_en
voicesynth cache clear
```

### Logging

```python
from voicesynth import disable_logging, enable_logging

disable_logging()
```

### Errors

All exceptions derive from `voicesynth.exceptions.VoiceSynthError`: `IncorrectModel`, `IncorrectSpeaker`, `ModelDownloadError`, `SynthesisError`, `AudioPlayingError`, `ModelIntegrityError`, `PackageError` and others.

### Tests

```bash
pip install voicesynth[dev]
pytest
mypy
```
