import re
import unicodedata
from typing import Dict, List, Optional

_SENTENCE_END = re.compile(r"(?<=[.!?…])\s+|\n+")
_CLAUSE_END = re.compile(r"(?<=[,;:–—])\s+")
_TAG = re.compile(r"<[^>]+>")
_WORD = re.compile(r"\w+", re.UNICODE)


def _pack_words(words: List[str], limit: int) -> List[str]:
    pieces: List[str] = []
    current = ""
    for word in words:
        while len(word) > limit:
            if current:
                pieces.append(current)
                current = ""
            pieces.append(word[:limit])
            word = word[limit:]
        if current and len(current) + 1 + len(word) <= limit:
            current += " " + word
        else:
            if current:
                pieces.append(current)
            current = word
    if current:
        pieces.append(current)
    return pieces


def _break_long(sentence: str, limit: int) -> List[str]:
    if len(sentence) <= limit:
        return [sentence]
    pieces: List[str] = []
    for clause in _CLAUSE_END.split(sentence):
        if len(clause) <= limit:
            pieces.append(clause)
        else:
            pieces.extend(_pack_words(clause.split(), limit))
    return pieces


def split_text(text: str, max_chars: int = 500) -> List[str]:
    if max_chars < 1:
        raise ValueError("max_chars must be positive")
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks: List[str] = []
    current = ""
    for sentence in (part.strip() for part in _SENTENCE_END.split(text)):
        if not sentence:
            continue
        for piece in _break_long(sentence, max_chars):
            if current and len(current) + 1 + len(piece) <= max_chars:
                current += " " + piece
            else:
                if current:
                    chunks.append(current)
                current = piece
    if current:
        chunks.append(current)
    return chunks


def _script_of(char: str) -> Optional[str]:
    if not char.isalpha():
        return None
    name = unicodedata.name(char, "")
    if name.startswith("LATIN"):
        return "latin"
    if name.startswith("CYRILLIC"):
        return "cyrillic"
    return None


def script_counts(text: str) -> Dict[str, int]:
    counts = {"latin": 0, "cyrillic": 0}
    for char in text:
        script = _script_of(char)
        if script:
            counts[script] += 1
    return counts


def foreign_words(text: str, expected: str) -> List[str]:
    other = "latin" if expected == "cyrillic" else "cyrillic"
    plain = _TAG.sub(" ", text)
    return [word for word in _WORD.findall(plain) if any(_script_of(char) == other for char in word)]
