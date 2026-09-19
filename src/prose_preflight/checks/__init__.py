"""Checker registry. Adding a checker is adding a module and one name here."""

from prose_preflight.checks import (
    acronym,
    claim,
    readability,
    sentence_length,
    structure,
    terminology,
    units,
    vale,
)

CHECKERS = {
    module.__name__.rsplit(".", 1)[1]: module.check
    for module in (
        acronym,
        claim,
        readability,
        sentence_length,
        structure,
        terminology,
        units,
        vale,
    )
}

__all__ = ["CHECKERS"]
