"""First-use expansion tracking. An acronym is defined by a parenthesized pairing."""

import re

from prose_preflight.checks._text import excerpt
from prose_preflight.extract import Document
from prose_preflight.finding import Finding

ACRONYM = re.compile(r"\b([A-Z]{2,})s?\b")
# "Deep Neural Network (DNN)" -- the words before the parenthesis define it.
DEFINED_AFTER = re.compile(r"(?:\b[\w-]+\s+){1,6}\(([A-Z]{2,})s?\)")
# "DNN (deep neural network)" -- the parenthesis expands it.
DEFINED_BEFORE = re.compile(r"\b([A-Z]{2,})s?\s*\((?=[^)]*[a-z])[^)]{4,}\)")


def check(doc: Document, rule: dict) -> list[Finding]:
    allow = {form.upper() for form in rule.get("allowlist", [])}
    minimum = rule.get("min_uses", 1)
    severity = rule.get("severity", "warning")
    uses, defined = {}, set()
    for n, line in doc.prose():
        defined |= {m.group(1) for m in DEFINED_AFTER.finditer(line)}
        defined |= {m.group(1) for m in DEFINED_BEFORE.finditer(line)}
        for m in ACRONYM.finditer(line):
            form = m.group(1)
            if form in allow or form in defined:
                continue
            uses.setdefault(form, []).append((n, m))
    findings = []
    for form, hits in uses.items():
        if len(hits) < minimum:
            continue
        n, m = hits[0]
        findings.append(
            Finding(
                check="acronym.undefined",
                category="acronym",
                severity=severity,
                line=n,
                col=m.start() + 1,
                excerpt=excerpt(doc.lines[n - 1], m.start(), m.end()),
                message=f"{form!r} is used {len(hits)}× but never expanded; spell it out on first use.",
                section=doc.section_at(n),
            )
        )
    return findings
