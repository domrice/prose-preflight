"""Shared paragraph and sentence helpers. Not a checker, not registered."""

import re

from prose_preflight.extract import Document

# ponytail: regex sentence split -- misses "e.g. Foo" and "Fig. 3 shows". No spaCy for
# this; upgrade the lookbehind when a fixture shows a real miss.
SENTENCE_END = re.compile(r"(?<=[.!?])[\"')\]]*\s+(?=[\"'(\[]*[A-Z0-9])")
WORD = re.compile(r"\S+")


def alternation(words, ignore_case: bool = True):
    """Compile `words` into one word-bounded alternation. Longest first, so a variant
    that starts another one still matches in full."""
    return re.compile(
        r"\b(?:{})\b".format(
            "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))
        ),
        re.IGNORECASE if ignore_case else 0,
    )


def paragraphs(doc: Document):
    """Yield (text, positions) per paragraph: masked text joined with single spaces,
    plus a (line, col) per character, so a match offset maps back to the source."""
    for first, last in doc.paragraphs:
        chunks, positions = [], []
        for n in range(first, last + 1):
            line = doc.masked[n - 1]
            if positions:
                chunks.append(" ")
                positions.append(positions[-1])
            chunks.append(line)
            positions += [(n, col) for col in range(1, len(line) + 1)]
        yield "".join(chunks), positions


def sentences(text: str):
    """Yield (offset, sentence) over `text`."""
    start = 0
    for split in SENTENCE_END.finditer(text):
        yield start, text[start : split.start()]
        start = split.end()
    if text[start:].strip():
        yield start, text[start:]


def excerpt(line: str, start: int, end: int, pad: int = 30) -> str:
    left, right = max(0, start - pad), min(len(line), end + pad)
    return (
        ("…" if left else "")
        + line[left:right].strip()
        + ("…" if right < len(line) else "")
    )
