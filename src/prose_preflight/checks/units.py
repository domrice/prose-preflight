"""Number and unit *formatting* only -- spacing and dashes. Regex, not Pint."""

import re

from prose_preflight.checks._text import excerpt
from prose_preflight.extract import Document
from prose_preflight.finding import Finding

NBSP = " "
RULES = {  # rule suffix: (pattern template, replacement, message)
    "space_before_unit": (
        r"(?<![\w.])(\d+(?:[.,]\d+)?)[ ]({units})\b",
        lambda m: f"{m.group(1)}{NBSP}{m.group(2)}",
        "Use a non-breaking space between value and unit.",
    ),
    "percent_spacing": (
        r"(?<![\w.])(\d+(?:[.,]\d+)?)\s+%",
        lambda m: f"{m.group(1)}%",
        "Write the percent sign attached to the number.",
    ),
    "range_dash": (
        r"(?<![\w.-])(\d+(?:[.,]\d+)?)-(\d+(?:[.,]\d+)?)(?![\w-])",
        lambda m: f"{m.group(1)}–{m.group(2)}",
        "Use an en dash for numeric ranges.",
    ),
    "p_value_spacing": (
        r"\bp\s*([<>=≤≥])\s*(\.\d+|0\.\d+)",
        lambda m: (
            f"p {m.group(1)} {m.group(2) if m.group(2)[0] == '0' else '0' + m.group(2)}"
        ),
        "Write p-values as 'p < 0.05', with spaces and a leading zero.",
    ),
}


def check(doc: Document, rule: dict) -> list[Finding]:
    severity = rule.get("severity", "warning")
    units = "|".join(
        re.escape(u) for u in sorted(rule.get("units", []), key=len, reverse=True)
    )
    findings = []
    for name, (template, replace, message) in RULES.items():
        if name in rule.get("disabled_rules", []) or (
            "{units}" in template and not units
        ):
            continue
        pattern = re.compile(template.format(units=units))
        for n, line in doc.prose():
            for m in pattern.finditer(line):
                suggestion = replace(m)
                if suggestion == m.group():
                    continue
                findings.append(
                    Finding(
                        check=f"units.{name}",
                        category="units",
                        severity=severity,
                        line=n,
                        col=m.start() + 1,
                        excerpt=excerpt(doc.lines[n - 1], m.start(), m.end()),
                        message=message,
                        section=doc.section_at(n),
                        suggestion=suggestion,
                    )
                )
    return findings
