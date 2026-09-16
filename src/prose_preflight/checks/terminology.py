"""Preferred-form enforcement. The table is data; this module is the matcher."""

from prose_preflight.checks._text import alternation, excerpt
from prose_preflight.extract import Document
from prose_preflight.finding import Finding


def check(doc: Document, rule: dict) -> list[Finding]:
    severity = rule.get("severity", "warning")
    findings = []
    for preferred, variants in rule.get("terms", {}).items():
        pattern = alternation(variants, rule.get("ignore_case", True))
        for n, line in doc.prose():
            for m in pattern.finditer(line):
                if m.group() == preferred:
                    continue
                findings.append(
                    Finding(
                        check="terminology.variant",
                        category="terminology",
                        severity=severity,
                        line=n,
                        col=m.start() + 1,
                        excerpt=excerpt(doc.lines[n - 1], m.start(), m.end()),
                        message=f"Use {preferred!r}, not {m.group()!r}.",
                        section=doc.section_at(n),
                        suggestion=_match_case(m.group(), preferred),
                    )
                )
    return findings


def _match_case(found: str, preferred: str) -> str:
    """Carry the variant's case over to the suggestion. A single capital letter is
    sentence case, not an acronym, so only multi-character ALL CAPS becomes ALL CAPS."""
    if len(found) > 1 and found.isupper():
        return preferred.upper()
    return preferred[:1].upper() + preferred[1:] if found[:1].isupper() else preferred
