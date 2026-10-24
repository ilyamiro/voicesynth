import pytest

from voicesynth.text import foreign_words, script_counts, split_text


def test_short_text_is_single_chunk():
    assert split_text("Hello there.") == ["Hello there."]


def test_empty_text_gives_no_chunks():
    assert split_text("   \n ") == []


def test_invalid_limit():
    with pytest.raises(ValueError):
        split_text("abc", 0)


def test_splits_on_sentences_and_respects_limit():
    text = " ".join(f"Sentence number {i} is here." for i in range(40))
    chunks = split_text(text, 100)
    assert len(chunks) > 1
    assert all(len(chunk) <= 100 for chunk in chunks)
    assert " ".join(chunks) == text


def test_splits_long_sentence_on_clauses():
    text = ", ".join(f"clause {i}" for i in range(60))
    chunks = split_text(text, 80)
    assert all(len(chunk) <= 80 for chunk in chunks)
    assert " ".join(chunks).replace(" ", "") == text.replace(" ", "")


def test_splits_text_without_punctuation_on_words():
    text = " ".join(["word"] * 200)
    chunks = split_text(text, 50)
    assert all(len(chunk) <= 50 for chunk in chunks)
    assert " ".join(chunks) == text


def test_hard_splits_oversized_word():
    chunks = split_text("a" * 25 + " tail", 10)
    assert all(len(chunk) <= 10 for chunk in chunks)
    assert "".join(chunks).replace(" ", "") == "a" * 25 + "tail"


def test_newlines_are_boundaries():
    chunks = split_text("first line\nsecond line\nthird line", 12)
    assert chunks == ["first line", "second line", "third line"]


def test_unicode_text_is_split():
    text = " ".join(["Привет, как дела?"] * 30)
    chunks = split_text(text, 60)
    assert all(len(chunk) <= 60 for chunk in chunks)


def test_script_counts():
    assert script_counts("abc Привет") == {"latin": 3, "cyrillic": 6}
    assert script_counts("123 !?") == {"latin": 0, "cyrillic": 0}


def test_foreign_words_for_cyrillic_model():
    assert foreign_words("Привет hello мир world", "cyrillic") == ["hello", "world"]


def test_foreign_words_for_latin_model():
    assert foreign_words("Hello привет", "latin") == ["привет"]


def test_foreign_words_ignores_ssml_tags_and_pure_text():
    assert foreign_words("<speak>Привет</speak>", "cyrillic") == []
    assert foreign_words("Привет, мир! 123", "cyrillic") == []


def test_mixed_script_word_is_foreign():
    assert foreign_words("прivет", "cyrillic") == ["прivет"]
