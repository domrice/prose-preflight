"""One fixture pair per MVP checker. The pinned (check, line) set is the contract."""

import json
from pathlib import Path

import pytest

from prose_preflight.checks import CHECKERS
from prose_preflight.extract import read
from prose_preflight.run_all import load_config, report

FIXTURES = Path(__file__).parent / "fixtures"
NAMES = ["acronym", "claim", "readability", "sentence_length", "structure", "units"]


# `required_sections` is empty by default (opt-in), so the structure fixture supplies one.
EXTRA_RULES = {
    "structure": {
        "required_sections": [
            "Abstract",
            "Introduction",
            "Methods",
            "Results",
            "Discussion",
            "References",
        ]
    }
}


def rule(name):
    return load_config(None)["checks"].get(name, {}) | EXTRA_RULES.get(name, {})


def run(name):
    return CHECKERS[name](read(FIXTURES / f"{name}.md"), rule(name))


@pytest.mark.parametrize("name", NAMES)
def test_matches_expected_pairs(name):
    expected = [
        tuple(pair)
        for pair in json.loads((FIXTURES / f"{name}.expected.json").read_text())
    ]
    assert sorted((f.check, f.line) for f in run(name)) == sorted(expected)


@pytest.mark.parametrize("name", NAMES)
def test_disabled_by_config(name):
    """Disabling is the runner's gate now, not the checker's."""
    config = load_config(None)
    config["checks"].setdefault(name, {}).update(
        EXTRA_RULES.get(name, {}), enabled=False
    )
    data = report(FIXTURES / f"{name}.md", config, [name])
    assert data["findings"] == []


def test_claim_is_review_only():
    assert {f.severity for f in run("claim")} == {"review"}


def test_units_suggestions():
    by_position = {(f.line, f.col): f.suggestion for f in run("units")}
    assert by_position[(3, 13)] == "12 mm"
    assert by_position[(4, 29)] == "p < 0.05"  # leading zero restored


def test_acronym_reports_first_use_with_count():
    (finding,) = run("acronym")
    assert (finding.line, finding.col) == (4, 25) and "2×" in finding.message


def test_structure_flags_missing_and_order():
    checks = [f.check for f in run("structure")]
    assert checks.count("structure.missing_section") == 2
    assert "structure.section_order" in checks


def test_readability_skips_short_sections():
    assert {f.section for f in run("readability")} == {"Abstract"}


def test_warn_unknown_keys_recurses(capsys):
    from prose_preflight.run_all import warn_unknown_keys

    warn_unknown_keys(
        {"checks": {"acronym": {"min_uses": 1}}},
        {"checks": {"acronym": {"min_use": 2}, "typo": {}}},
    )
    err = capsys.readouterr().err
    assert "'checks.acronym.min_use'" in err and "'checks.typo'" in err
