"""Checker registry. Adding a checker is adding a module and one line here."""

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
    "acronym": acronym.check,
    "claim": claim.check,
    "readability": readability.check,
    "sentence_length": sentence_length.check,
    "structure": structure.check,
    "terminology": terminology.check,
    "units": units.check,
    "vale": vale.check,
}

__all__ = ["CHECKERS"]
