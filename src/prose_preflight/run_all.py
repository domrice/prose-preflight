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
REPORT_NAME = "PREFLIGHT_{stem}.md"  # written on every run; --md moves it
PROJECT_CONFIG = "prose-preflight.yaml"  # picked up from the working directory
SEVERITY_ORDER = {"error": 0, "warning": 1, "review": 2}


def load_config(override: str | None) -> dict:
    config = yaml.safe_load(DEFAULT_CONFIG.read_text()) or {}
    if override:
        user = yaml.safe_load(Path(override).read_text()) or {}
        warn_unknown_keys(config, user)
        merge(config, user)
    return config


def warn_unknown_keys(base: dict, over: dict, path: str = "") -> None:
    """A typo merges in silently and does nothing; say so on stderr."""
    for key, value in over.items():
        where = f"{path}{key}"
        if key not in base:
            print(f"prose-preflight: unknown config key {where!r}", file=sys.stderr)
        elif isinstance(value, dict) and isinstance(base[key], dict):
            warn_unknown_keys(base[key], value, f"{where}.")


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
        # agent-facing, no checker reads it; unset keys are dropped so an untouched
        # contract arrives as {} and the agent can offer prose-init
        "contract": {k: v for k, v in (config.get("contract") or {}).items() if v},
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
    findings = data["findings"]
    keep = set(_cap(findings, cap))
    dropped = [f for i, f in enumerate(findings) if i not in keep]
    return data | {
        "truncated": _counts(dropped, "category"),
        "findings": [findings[i] for i in sorted(keep)],
    }


def render_md(data: dict) -> str:
    """Full report as Markdown, grouped by severity then category."""
    lines = [f"# Preflight: {data['file']}", ""]
    lines += [f"- **{k}:** {v}" for k, v in data["contract"].items() if v]
    lines += ["", f"{data['total']} findings."]
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
    parser.add_argument("file", nargs="?")
    parser.add_argument(
        "--version", action="version", version=version("prose-preflight")
    )
    parser.add_argument(
        "--config",
        help=f"YAML deep-merged over the bundled config "
        f"(default: ./{PROJECT_CONFIG} when it exists)",
    )
    parser.add_argument(
        "--checks",
        help=f"comma-separated subset of: {', '.join(CHECKERS)}",
        type=lambda value: value.split(","),
        default=list(CHECKERS),
    )
    parser.add_argument("--max-findings", type=int, default=20, help="0 lifts the cap")
    parser.add_argument(
        "--init",
        nargs="?",
        const=PROJECT_CONFIG,
        metavar="PATH",
        help=f"read config answers as JSON on stdin, write them there as YAML "
        f"(default: {PROJECT_CONFIG}) and exit",
    )
    parser.add_argument(
        "--md",
        metavar="PATH",
        help=f"where the full Markdown report goes (default: ./{REPORT_NAME})",
    )
    args = parser.parse_args()

    if args.init:
        answers = json.load(sys.stdin)
        warn_unknown_keys(load_config(None), answers)
        Path(args.init).write_text(
            yaml.safe_dump(answers, sort_keys=False, allow_unicode=True)
        )
        print(f"wrote {args.init}", file=sys.stderr)
        return 0
    if not args.file:
        parser.error("a file is required")
    if unknown := [name for name in args.checks if name not in CHECKERS]:
        parser.error(f"unknown check(s): {', '.join(unknown)}")
    config = args.config
    if not config and Path(PROJECT_CONFIG).is_file():  # discovery is the CLI's job,
        config = PROJECT_CONFIG  # never load_config's
        print(f"prose-preflight: using {PROJECT_CONFIG}", file=sys.stderr)
    full = report(Path(args.file), load_config(config), args.checks)
    # one report per document, so checking a second file never clobbers the first
    md = args.md or REPORT_NAME.format(stem=Path(args.file).stem)
    Path(md).write_text(render_md(full))
    print(f"prose-preflight: wrote {md}", file=sys.stderr)
    json.dump(capped(full, args.max_findings) | {"report": md}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
