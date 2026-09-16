"""Vale, behind the checker interface. An external binary that must never abort the run."""

import json
import subprocess
import tempfile
from pathlib import Path

from prose_preflight.extract import Document
from prose_preflight.finding import Finding

# The `vale` dependency ships the binary, so reaching this message means the
# environment blocked it: no network on first run, or a binary quarantined by the OS.
MISSING = (
    "The Vale binary could not be found, so grammar and style were not checked. "
    "It is normally installed with this package; a blocked first-run download is the "
    "usual cause. Install it manually from https://vale.sh/docs/install and it will be "
    "picked up from PATH."
)


def check(doc: Document, rule: dict) -> list[Finding]:
    try:
        alerts = _run(doc, rule)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        return [
            Finding(
                check="vale.unavailable",
                category="style",
                severity="warning",
                line=1,
                col=1,
                excerpt="",
                message=MISSING
                if isinstance(exc, FileNotFoundError)
                else f"Vale failed: {exc}",
                section=None,
                suggestion=None,
            )
        ]
    return [
        Finding(
            # ponytail: every Vale rule lands in `style`. Split into grammar/spelling
            # by rule prefix once a config needs to weight them differently.
            check=f"vale.{alert['Check']}",
            category="style",
            severity="error" if alert["Severity"].lower() == "error" else "warning",
            line=alert["Line"],
            col=alert["Span"][0],
            excerpt=alert["Match"],
            message=alert["Message"],
            section=doc.section_at(alert["Line"]),
            suggestion=next(iter(alert.get("Action", {}).get("Params") or []), None),
        )
        for alert in alerts
    ]


def _run(doc: Document, rule: dict) -> list[dict]:
    """Invoke Vale on the document. Vale exits nonzero when it finds alerts, so only
    the JSON on stdout decides success."""
    with tempfile.TemporaryDirectory() as tmp:
        ini = rule.get("config_file") or _write_ini(Path(tmp), rule)
        path = _readable(doc, Path(tmp))
        result = subprocess.run(
            ["vale", "--output=JSON", f"--config={ini}", str(path)],
            capture_output=True,
            check=False,  # nonzero just means "alerts found"
            text=True,
            timeout=rule.get("timeout", 60),
        )
    if not result.stdout.strip():
        raise subprocess.SubprocessError(result.stderr.strip() or "no output")
    report = json.loads(result.stdout)
    return [alert for alerts in report.values() for alert in alerts]


def _readable(doc: Document, tmp: Path) -> Path:
    """Vale parses Markdown and plain text; it has no LaTeX reader, and pointed at a
    .tex file it would flag the preamble and every command. `doc.masked` is already
    the prose alone, line for line, so any other format goes to Vale as masked text."""
    if doc.path.suffix.lower() in {".md", ".markdown", ".txt"}:
        return doc.path
    masked = tmp / f"{doc.path.stem}.txt"
    masked.write_text("\n".join(doc.masked))
    return masked


def _write_ini(tmp: Path, rule: dict) -> Path:
    """Vale's own config is an INI string in `default.yaml`, so it stays data."""
    ini = tmp / ".vale.ini"
    ini.write_text(rule.get("ini", ""))
    return ini
