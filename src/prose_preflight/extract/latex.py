"""LaTeX reader. Same `Document` and the same contract as the Markdown reader:
nothing is deleted, opaque spans become spaces, every offset is a true source
line/col.

Two masking stages. First verbatim, math and comments are blanked, and headings are
indexed from that. Then command sequences and braces are blanked too, so what a
checker regexes over is the prose alone.
"""

import re

from prose_preflight.extract.document import Document, blank, paragraphs

OPAQUE = (
    "verbatim|Verbatim|lstlisting|minted|equation|align|displaymath|gather|"
    "multline|eqnarray|alignat|tikzpicture|tabular"
)
BEGIN = re.compile(rf"\\begin\{{({OPAQUE})\*?\}}|\\\[")
COMMENT = re.compile(r"(?<!\\)%.*")
INLINE = re.compile(r"\$[^$\n]+\$|\\\([^\n]*?\\\)|\\verb\*?(.)(?:(?!\1).)*\1")
# whole-command-with-argument first (labels, cites, refs, \begin/\end), then bare
# commands, braces and ties -- so key and environment names never leak into prose
COMMAND = re.compile(
    r"\\(?:begin|end|label|nocite|[A-Za-z]*(?:cite|ref)[A-Za-z]*)\*?"
    r"(?:\[[^\]\n]*\])*\{[^}\n]*\}"
    r"|\\[A-Za-z@]+\*?(?:\[[^\]\n]*\])?|[{}~]|\\\\"
)
SECTION = re.compile(
    r"\\(part|chapter|section|subsection|subsubsection|paragraph)\*?\{(.*)\}"
)
LEVELS = {
    "part": 1,
    "chapter": 1,
    "section": 1,
    "subsection": 2,
    "subsubsection": 3,
    "paragraph": 4,
}


def read(path, text: str) -> Document:
    lines = text.splitlines()
    masked = _mask(lines)
    doc = Document(path, lines, masked)
    _headings(doc, masked)
    doc.masked = [_blank_line(n, line, doc) for n, line in enumerate(masked, 1)]
    paragraphs(doc)
    return doc


def _mask(lines: list[str]) -> list[str]:
    """Blank the preamble, verbatim and display-math environments, and comments."""
    out, closing, preamble = (
        [],
        None,
        any("\\begin{document}" in line for line in lines),
    )
    for line in lines:
        line = COMMENT.sub(blank, line)
        if preamble:
            out.append(" " * len(line))
            preamble = "\\begin{document}" not in line
            continue
        if closing:
            out.append(" " * len(line))
            if closing in line:
                closing = None
            continue
        if begin := BEGIN.search(line):
            closing = "\\]" if begin.group() == "\\[" else f"\\end{{{begin.group(1)}"
            out.append(" " * len(line))
            continue
        out.append(INLINE.sub(blank, line))
    return out


def _headings(doc: Document, masked: list[str]) -> None:
    for n, line in enumerate(masked, 1):
        if section := SECTION.search(line):
            title = COMMAND.sub(" ", section.group(2)).strip()
            doc.headings.append((n, LEVELS[section.group(1)], title))


def _blank_line(n: int, line: str, doc: Document) -> str:
    """Heading lines go entirely -- the title is already indexed, and leaving it as
    prose would make it a paragraph. Elsewhere only the markup goes."""
    if any(start == n for start, _, _ in doc.headings):
        return " " * len(line)
    return COMMAND.sub(blank, line)
