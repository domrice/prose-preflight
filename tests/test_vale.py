"""Two paths matter: the mapping, and degrading when the binary is absent."""

import json
import shutil
from pathlib import Path

import pytest

from prose_preflight.checks import vale
from prose_preflight.extract import read
from prose_preflight.run_all import load_config

FIXTURES = Path(__file__).parent / "fixtures"

ALERT = {
    "Action": {"Name": "replace", "Params": ["dataset"]},
    "Check": "Vale.Terms",
    "Line": 3,
    "Match": "data set",
    "Message": "Use 'dataset' instead of 'data set'.",
    "Severity": "suggestion",
    "Span": [16, 23],
}


def test_alerts_map_onto_findings(monkeypatch):
    monkeypatch.setattr(vale, "_run", lambda path, rule: [ALERT])
    (finding,) = vale.check(
        read(FIXTURES / "vale.md"), load_config(None)["checks"]["vale"]
    )
    assert (finding.check, finding.line, finding.col) == ("vale.Vale.Terms", 3, 16)
    assert finding.severity == "warning"  # suggestion, per the configured map
    assert finding.section == "Methods"
    assert finding.suggestion == "dataset"
    assert finding.excerpt == "data set"


def test_degrades_to_one_warning_without_the_binary(monkeypatch):
    monkeypatch.setenv("PATH", "")
    (finding,) = vale.check(
        read(FIXTURES / "vale.md"), load_config(None)["checks"]["vale"]
    )
    assert (finding.check, finding.severity, finding.line) == (
        "vale.unavailable",
        "warning",
        1,
    )
    assert "vale.sh/docs/install" in finding.message


@pytest.mark.skipif(shutil.which("vale") is None, reason="vale binary not on PATH")
def test_against_the_real_binary():
    expected = [
        tuple(p) for p in json.loads((FIXTURES / "vale.expected.json").read_text())
    ]
    findings = vale.check(
        read(FIXTURES / "vale.md"), load_config(None)["checks"]["vale"]
    )
    assert sorted((f.check, f.line) for f in findings) == sorted(expected)
