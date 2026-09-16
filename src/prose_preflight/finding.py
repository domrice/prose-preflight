"""The one record every checker emits. Changing it breaks the whole repo."""

from dataclasses import dataclass


@dataclass(slots=True)
class Finding:
    check: str  # stable rule id, e.g. "terminology.variant"
    category: str  # grammar|style|readability|terminology|acronym|structure|units|claim
    severity: str  # error | warning | review -- "review" is never auto-applied
    line: int
    col: int
    excerpt: str
    message: str
    section: str | None = None
    suggestion: str | None = None
