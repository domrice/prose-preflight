"""The fixture pins the exact set of (check, line) pairs. False positives cost most."""

import json
from pathlib import Path

from prose_preflight.checks import CHECKERS
from prose_preflight.extract import read
from prose_preflight.run_all import load_config

FIXTURES = Path(__file__).parent / "fixtures"


def run():
    doc = read(FIXTURES / "terminology.md")
    return CHECKERS["terminology"](doc, load_config(None)["checks"]["terminology"])


def test_matches_expected_pairs():
    expected = [
        tuple(pair)
        for pair in json.loads((FIXTURES / "terminology.expected.json").read_text())
    ]
    assert sorted((f.check, f.line) for f in run()) == sorted(expected)


def test_suggestions_keep_case_and_columns():
    by_line = {(f.line, f.col): f for f in run()}
    assert by_line[(3, 16)].suggestion == "dataset"
    assert by_line[(16, 1)].suggestion == "Dataset"  # sentence case carried over
    assert by_line[(4, 15)].section == "Methods"
    assert by_line[(16, 1)].section == "Results"
