"""Required sections and their order, from the YAML list. Titles match case-insensitively."""

from itertools import pairwise

from prose_preflight.extract import Document
from prose_preflight.finding import Finding


def check(doc: Document, rule: dict) -> list[Finding]:
    required = rule.get("required_sections", [])
    if not required:
        return []
    found = {}  # required title (as configured) -> source line of its first match
    for line, _, title in doc.headings:
        for want in required:
            if title.strip().lower() == want.lower() and want not in found:
                found[want] = line
    findings = [
        Finding(
            check="structure.missing_section",
            category="structure",
            severity=rule.get("severity", "error"),
            line=1,
            col=1,
            excerpt=doc.path.name,
            message=f"Required section {want!r} is missing.",
        )
        for want in required
        if want not in found
    ]
    present = [want for want in required if want in found]
    for earlier, later in pairwise(present):
        if found[later] < found[earlier]:
            findings.append(
                Finding(
                    check="structure.section_order",
                    category="structure",
                    severity=rule.get("order_severity", "warning"),
                    line=found[later],
                    col=1,
                    excerpt=later,
                    message=f"Section {later!r} appears before {earlier!r}; expected order is {' → '.join(required)}.",
                    section=later,
                )
            )
    return findings
