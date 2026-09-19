"""The shared domain model and the passes every reader needs.

Line fidelity is the hard requirement, so nothing is ever deleted. Code and math
become `masked`: a character-for-character copy of the text with those spans
replaced by spaces. Checkers regex over `masked` and the offsets they get back are
true source `line`/`col`.
"""

from dataclasses import dataclass, field
from pathlib import Path


def blank(match) -> str:
    return " " * len(match.group())


@dataclass(slots=True)
class Document:
    path: Path
    lines: list[str]  # source lines, no trailing newline, index 0 == line 1
    masked: list[str]  # same shape, code and math blanked to spaces
    headings: list[tuple[int, int, str]] = field(
        default_factory=list
    )  # line, level, title
    paragraphs: list[tuple[int, int]] = field(
        default_factory=list
    )  # first line, last line

    def section_at(self, line: int) -> str | None:
        """Title of the nearest heading at or above `line`."""
        return next(
            (t for start, _, t in reversed(self.headings) if start <= line), None
        )

    def prose(self):
        """Yield (line, masked_text) for every line outside code and math."""
        return ((n, t) for n, t in enumerate(self.masked, 1) if t.strip())


def paragraphs(doc: Document) -> None:
    """Index runs of non-blank, non-heading lines. A masked-out block breaks a run.
    Readers index headings first, so a heading line is recognized by its line number."""
    heads = {n for n, _, _ in doc.headings}
    start = None
    for n, line in enumerate(doc.masked, 1):
        if line.strip() and n not in heads:
            start = start or n
        elif start:
            doc.paragraphs.append((start, n - 1))
            start = None
    if start:
        doc.paragraphs.append((start, len(doc.masked)))


def read(path: Path, text: str) -> Document:
    """Plain text: no construct is recognized, so `masked` is the source verbatim."""
    lines = text.splitlines()
    doc = Document(path, lines, list(lines))
    paragraphs(doc)
    return doc
