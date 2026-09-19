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
# every command sequence, brace and tie: the markup itself is never prose
CHUNK = re.compile(r"\\[A-Za-z@]+\*?|\\\\|[{}~]")
# commands whose arguments are keys, paths or markup rather than prose -- their
# groups are blanked too, so bib keys and file names never reach a checker
OPAQUE_ARG = re.compile(
    r"\\(?:begin|end|label|nocite|input|include(?:graphics)?|url|href|path"
    r"|texttt|lstinline|verb|SI|si|num|ang|[A-Za-z]*(?:cite|ref)[A-Za-z]*)\*?$"
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
    # one pass over the whole text, so an argument wrapped across lines is still
    # recognized; newlines survive, so the split restores the same line shape
    stripped = _strip("\n".join(masked)).split("\n")
    heads = {n for n, _, _ in doc.headings}
    # a heading line goes entirely -- the title is already indexed, and leaving it as
    # prose would make it a paragraph
    doc.masked = [
        " " * len(line) if n in heads else line for n, line in enumerate(stripped, 1)
    ]
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


def _strip(text: str) -> str:
    """Blank every command, brace and tie, and the whole argument of a command whose
    argument is not prose. Character-for-character: only newlines are kept."""
    out = list(text)

    def wipe(start: int, end: int) -> None:
        for i in range(start, end):
            if out[i] != "\n":
                out[i] = " "

    for m in CHUNK.finditer(text):
        wipe(m.start(), m.end())
        if not OPAQUE_ARG.match(m.group()):
            continue
        i = m.end()
        while (end := _group(text, i)) is not None:
            wipe(i, end)
            i = end
    return "".join(out)


def _group(text: str, i: int) -> int | None:
    """End of the balanced `[...]` or `{...}` starting at `i` (leading whitespace
    skipped), or None if no argument starts there."""
    while i < len(text) and text[i] in " \t\n":
        i += 1
    if i >= len(text) or text[i] not in "[{":
        return None
    opening, closing, depth = text[i], {"[": "]", "{": "}"}[text[i]], 0
    for j in range(i, len(text)):
        if text[j] == opening:
            depth += 1
        elif text[j] == closing:
            depth -= 1
            if depth == 0:
                return j + 1
    return None


def _headings(doc: Document, masked: list[str]) -> None:
    for n, line in enumerate(masked, 1):
        if section := SECTION.search(line):
            title = _strip(section.group(2)).strip()
            doc.headings.append((n, LEVELS[section.group(1)], title))
