"""Hedges and boosters. Emits `review` only -- never auto-applied, by design."""

from prose_preflight.checks._text import alternation, excerpt
from prose_preflight.extract import Document
from prose_preflight.finding import Finding

KINDS = {
    "hedge": "Hedge -- check the claim is not weaker than the evidence.",
    "booster": "Booster -- check the evidence supports a claim this strong.",
}


def check(doc: Document, rule: dict) -> list[Finding]:
    findings = []
    for kind, message in KINDS.items():
        words = rule.get(f"{kind}s", [])
        if not words:
            continue
        pattern = alternation(words)
        for n, line in doc.prose():
            for m in pattern.finditer(line):
                findings.append(
                    Finding(
                        check=f"claim.{kind}",
                        category="claim",
                        severity="review",  # load-bearing: never auto-applied
                        line=n,
                        col=m.start() + 1,
                        excerpt=excerpt(doc.lines[n - 1], m.start(), m.end()),
                        message=f"{message} ({m.group()!r})",
                        section=doc.section_at(n),
                    )
                )
    return findings
