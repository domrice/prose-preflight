"""Extraction: pick a reader by suffix, return one normalized `Document`."""

from pathlib import Path

from prose_preflight.extract import document, latex, markdown
from prose_preflight.extract.document import Document

__all__ = ["Document", "read"]

READERS = {".tex": latex.read, ".md": markdown.read, ".markdown": markdown.read}


def read(path: str | Path) -> Document:
    """Anything without a known suffix is read as plain text."""
    path = Path(path)
    reader = READERS.get(path.suffix.lower(), document.read)
    return reader(path, path.read_text(encoding="utf-8"))
