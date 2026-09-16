from dataclasses import asdict

from prose_preflight.finding import Finding


def test_finding_serializes():
    f = Finding(
        "terminology.variant",
        "terminology",
        "warning",
        3,
        5,
        "e.g.",
        "Use 'for example'.",
        suggestion="for example",
    )
    assert asdict(f) == {
        "check": "terminology.variant",
        "category": "terminology",
        "severity": "warning",
        "line": 3,
        "col": 5,
        "excerpt": "e.g.",
        "message": "Use 'for example'.",
        "section": None,
        "suggestion": "for example",
    }
