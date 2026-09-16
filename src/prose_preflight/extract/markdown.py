"""Markdown reader. Fenced code, display math and inline code/math are masked to
spaces; ATX headings are indexed. See `document.py` for the model and the contract.
"""

import re
from pathlib import Path

from prose_preflight.extract.document import Document, blank, paragraphs

FENCE = re.compile(r"^\s{0,3}(```+|~~~+)")
DISPLAY_MATH = re.compile(r"^\s{0,3}\$\$")
# ponytail: ATX headings only. Setext (underlined) headings are missed; upgrade is a
# two-line lookahead in _headings.
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
INLINE = re.compile(r"`+[^`\n]*`+|\$[^$\n]+\$")


def read(path: Path, text: str) -> Document:
    lines = text.splitlines()
    doc = Document(path, lines, _mask(lines))
    _headings(doc)
    paragraphs(doc)
    return doc


def _mask(lines: list[str]) -> list[str]:
    """Blank fenced code, display math, inline code and inline math.

    ponytail: indented (4-space) code blocks are not masked -- they need blank-line and
    list context to tell from a wrapped line. Upgrade if fixtures show false positives.
    """
    out, closing = [], None
    for line in lines:
        if closing:
            out.append(" " * len(line))
            if line.strip().startswith(closing):
                closing = None
            continue
        fence = FENCE.match(line)
        if fence or DISPLAY_MATH.match(line):
            closing = fence.group(1) if fence else "$$"
            out.append(" " * len(line))
            continue
        out.append(INLINE.sub(blank, line))
    return out


def _headings(doc: Document) -> None:
    for n, line in doc.prose():
        if heading := HEADING.match(line):
            doc.headings.append((n, len(heading.group(1)), heading.group(2)))
