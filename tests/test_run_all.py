"""The token-efficiency contract: one report, counts at the top, a cap that stays fair."""

import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

from prose_preflight.finding import Finding
from prose_preflight.run_all import _cap, capped, load_config, report

FIXTURE = Path(__file__).parent / "fixtures" / "terminology.md"
CONFIG = FIXTURE.parent / "config.yaml"


def test_report_shape_and_counts():
    out = report(FIXTURE, load_config(str(CONFIG)), ["terminology"])
    assert out["total"] == 6
    assert out["counts"]["severity"] == {"warning": 6}
    assert out["counts"]["section"] == {"Methods": 4, "Results": 2}
    assert out["truncated"] == {}
    assert len(out["findings"]) == 6
    assert out["findings"][0]["check"] == "terminology.variant"


def test_cap_truncates_and_records_what_it_dropped():
    out = capped(
        report(FIXTURE, load_config(str(CONFIG)), ["terminology"]),
        2,
    )
    assert out["total"] == 6
    assert len(out["findings"]) == 2
    assert out["truncated"] == {"terminology": 4}
    assert out["counts"]["severity"] == {"warning": 6}  # counts cover everything


def make(category, line):
    return asdict(Finding("x", category, "warning", line, 1, "", ""))


def test_cap_is_fair_across_categories():
    noisy = [make("style", n) for n in range(10)]
    quiet = [make("units", 1), make("units", 2)]
    kept = [(noisy + quiet)[i] for i in _cap(noisy + quiet, 4)]
    assert [f["category"] for f in kept].count("units") == 2


def test_unknown_check_is_a_usage_error():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prose_preflight.run_all",
            str(FIXTURE),
            "--checks",
            "nope",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "unknown check" in result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize("flag", [[], ["--max-findings", "0"]])
def test_stdout_is_json_only(flag, tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prose_preflight.run_all",
            str(FIXTURE),
            "--checks",
            "terminology",
            "--config",
            str(CONFIG),
            "--md",
            str(tmp_path / "PREFLIGHT.md"),
            *flag,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout)["total"] == 6


def test_md_holds_every_finding_while_stdout_stays_capped(tmp_path):
    """The point of --md: the file is complete, the transcript is not."""
    md = tmp_path / "PREFLIGHT.md"
    out = subprocess.run(
        [
            sys.executable,
            "-m",
            "prose_preflight.run_all",
            str(FIXTURE),
            "--config",
            str(CONFIG),
            "--md",
            str(md),
            "--max-findings",
            "2",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(out.stdout)
    assert len(data["findings"]) == 2 < data["total"]
    rows = [
        line
        for line in md.read_text().splitlines()
        if line.startswith("| ") and not line.startswith("| Line")
    ]
    assert len(rows) == data["total"]
