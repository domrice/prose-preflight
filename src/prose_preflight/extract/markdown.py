"""Markdown reader. Fenced code, display math, HTML comments and inline code/math are
masked to spaces; ATX and Setext headings are indexed. See `document.py` for the
model and the contract.
"""

import re
from pathlib import Path

from prose_preflight.extract.document import Document, blank, paragraphs

FENCE = re.compile(r"^\s{0,3}(```+|~~~+)")
DISPLAY_MATH = re.compile(r"^\s{0,3}\$\$")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
# ponytail: single-line Setext text only -- a heading spread over several lines is not
# indexed at all. Upgrade to walking the run backwards if a real document needs it.
SETEXT = re.compile(r"^\s{0,3}(=+|-+)\s*$")
INLINE = re.compile(r"`+[^`\n]*`+|\$[^$\n]+\$")
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


def read(path: Path, text: str) -> Document:
    lines = text.splitlines()
    doc = Document(path, lines, _mask(_uncomment(text).splitlines()))
    _headings(doc)
    paragraphs(doc)
    return doc


def _uncomment(text: str) -> str:
    """Blank HTML comments across the whole text; newlines survive, so line numbers and
    column offsets still match the source. Multi-line comments need the whole text, not
    one line at a time -- hence a pass of its own before `_mask`.
    """
    return COMMENT.sub(lambda m: re.sub(r"[^\n]", " ", m.group()), text)


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
    """Index ATX headings, and Setext ones from the underline on the following line.
    The underline is blanked so `paragraphs` does not index it as prose of its own."""
    for n, line in doc.prose():
        if heading := HEADING.match(line):
            doc.headings.append((n, len(heading.group(1)), heading.group(2)))
            continue
        under = SETEXT.match(doc.masked[n]) if n < len(doc.masked) else None
        # a blank line above keeps the last line of a paragraph from becoming a
        # heading, and a lone `---` from reading as one
        if under and (n == 1 or not doc.masked[n - 2].strip()):
            doc.headings.append((n, 1 if under.group(1)[0] == "=" else 2, line.strip()))
            doc.masked[n] = " " * len(doc.masked[n])
