"""Runner: extract, fan out over checkers, aggregate, serialize. No domain knowledge."""

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import asdict
from importlib.metadata import version
from importlib.resources import files
from itertools import zip_longest
from pathlib import Path

import yaml

from prose_preflight.checks import CHECKERS
from prose_preflight.extract import read

DEFAULT_CONFIG = files("prose_preflight") / "default.yaml"
SEVERITY_ORDER = {"error": 0, "warning": 1, "review": 2}


def load_config(override: str | None) -> dict:
    config = yaml.safe_load(DEFAULT_CONFIG.read_text()) or {}
    if override:
        merge(config, yaml.safe_load(Path(override).read_text()) or {})
    return config


def merge(base: dict, over: dict) -> dict:
    """Deep-merge `over` into `base`, in place."""
    for key, value in over.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge(base[key], value)
        else:
            base[key] = value
    return base


def report(path: Path, config: dict, checks: list[str]) -> dict:
    """The complete report: every finding, nothing truncated."""
    doc = read(path)
    rules = config.get("checks", {})
    enabled = [n for n in checks if rules.get(n, {}).get("enabled", True)]
    findings = sorted(
        (asdict(f) for n in enabled for f in CHECKERS[n](doc, rules.get(n, {}))),
        key=lambda f: (
            SEVERITY_ORDER.get(f["severity"], 9),
            f["line"],
            f["col"],
            f["check"],
        ),
    )
    return {
        "file": str(path),
        "checks": checks,
        "total": len(findings),
        "counts": {
            field: _counts(findings, field)
            for field in ("severity", "category", "section")
        },
        "truncated": {},
        "findings": findings,
    }


def capped(data: dict, cap: int) -> dict:
    """The same report with `findings` limited to the worst `cap`, taken round-robin
    across categories so one noisy category cannot crowd out the rest. `cap` of 0 keeps
    everything. `counts` and `total` still cover everything; `truncated` says what was
    dropped, per category."""
    if not cap:
        return data
    keep = set(_cap(data["findings"], cap))
    kept, dropped = [], []
    for i, finding in enumerate(data["findings"]):
        (kept if i in keep else dropped).append(finding)
    return data | {"truncated": _counts(dropped, "category"), "findings": kept}


def render_md(data: dict) -> str:
    """Full report as Markdown, grouped by severity then category."""
    lines = [f"# Preflight: {data['file']}", "", f"{data['total']} findings."]
    for field, counts in data["counts"].items():
        lines += [
            "",
            f"**By {field}:** "
            + ", ".join(f"{k or '(none)'} {n}" for k, n in counts.items()),
        ]
    by_severity = defaultdict(list)
    for f in data["findings"]:
        by_severity[f["severity"]].append(f)
    for severity in sorted(by_severity, key=lambda s: SEVERITY_ORDER.get(s, 9)):
        lines += [
            "",
            f"## {severity}",
            "",
            "| Line | Check | Message | Suggestion | Excerpt |",
            "|---|---|---|---|---|",
        ]
        lines += [
            f"| {f['line']}:{f['col']} | `{f['check']}` | {f['message']} | "
            f"{'`' + f['suggestion'] + '`' if f['suggestion'] else ''} | {f['excerpt']} |"
            for f in by_severity[severity]
        ]
    return "\n".join(lines) + "\n"


def _counts(findings: list[dict], field: str) -> dict:
    return dict(Counter(f[field] or "" for f in findings).most_common())


def _cap(findings: list[dict], cap: int) -> list[int]:
    """Indices of the worst `cap` findings. `findings` is already sorted by severity
    then position, so each round takes the next-worst of every category."""
    buckets = defaultdict(list)
    for i, finding in enumerate(findings):
        buckets[finding["category"]].append(i)
    rounds = zip_longest(*buckets.values())
    return [i for group in rounds for i in group if i is not None][:cap]


def main() -> int:
    parser = argparse.ArgumentParser(prog="prose-preflight")
    parser.add_argument("file")
    parser.add_argument(
        "--version", action="version", version=version("prose-preflight")
    )
    parser.add_argument(
        "--config", help="YAML file deep-merged over the bundled config"
    )
    parser.add_argument(
        "--checks",
        help=f"comma-separated subset of: {', '.join(CHECKERS)}",
        type=lambda value: value.split(","),
        default=list(CHECKERS),
    )
    parser.add_argument("--max-findings", type=int, default=20, help="0 lifts the cap")
    parser.add_argument("--md", help="write the full Markdown report to this path")
    args = parser.parse_args()

    if unknown := [name for name in args.checks if name not in CHECKERS]:
        parser.error(f"unknown check(s): {', '.join(unknown)}")
    full = report(Path(args.file), load_config(args.config), args.checks)
    if args.md:
        Path(args.md).write_text(render_md(full))
    json.dump(capped(full, args.max_findings), sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
