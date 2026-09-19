# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this repo is

`prose-preflight` is an **agent skill**: deterministic CLI checkers plus thin `SKILL.md`
files that tell an agent how to drive them. The scripts are the analyzer, not the agent.

**No model is ever called from inside the Python.** That would cost determinism, offline
runs, and per-run money — the same trade that ruled out LanguageTool. Judgment lives in the
agent turn.

**Writing boundary.** The checkers never edit. `prose-preflight` and `prose-deepread`
report only. Two skills write, both narrowly:

- `prose-draft` adds prose that was not there — insert at an approved anchor, never rewrite
  or delete, never without an outline approved in the same conversation.
- `prose-edit` changes prose that is — only findings the user picked out of a report,
  previewed before writing.

Neither writes without `prose-preflight.yaml`. A `review` finding reaches the file only
because a human named it.

## The token-efficiency contract

This is the reason the project exists. Violating it defeats the skill.

- **One command, one report.** `run_all.py` once. Never invoke individual checkers, never
  read Vale output, never pipe raw tool stdout into context.
- **Never read the source document to find problems.** Findings carry `line`/`col` and a
  short `excerpt`.
- **Reports are summarized by default.** Top level is counts; findings are capped
  (`--max-findings`, default 20), filled round-robin across categories so one noisy
  category cannot crowd out the rest. `--md PATH` puts the full report on disk; the agent
  links it, never transcribes it.
- **`SKILL.md` stays short** (< 120 lines). Rule catalogs live in `README.md` and
  `default.yaml` comments.
- **No checker prints prose.** Diagnostics to stderr; stdout is JSON only.

## Layout

```
src/prose_preflight/
  finding.py    the one record every checker emits
  run_all.py    CLI: extract, fan out, aggregate, cap, serialize
  default.yaml  the only config; package data, resolved via importlib.resources
  extract/      document.py (Document + shared passes), markdown.py, latex.py
  checks/       acronym claim readability sentence_length structure terminology units vale
                + _text.py + __init__.py (CHECKERS registry)
skills/         prose-init, prose-preflight, prose-deepread, prose-draft, prose-edit
.claude-plugin/ plugin.json + marketplace.json
```

Four layers, each replaceable without touching the others:

1. **Extraction** — dispatch on file suffix (unknown reads as plain text). `Document.masked`
   is a character-for-character copy with code, math, and verbatim replaced by spaces, so
   regex offsets over `masked` *are* source `line`/`col`. Losing line numbers is not
   acceptable — every finding depends on it.
2. **Checkers** — each module exposes exactly `check(doc, rule) -> list[Finding]`. Pure,
   stateless, mutually ignorant. The runner does config lookup, the `enabled` gate, and
   sorting. Adding a checker is a module plus one line in `CHECKERS` — never a runner change.
3. **Config** — one bundled `default.yaml` as package data (a repo-root `profiles/` would be
   invisible to `uvx`). `--config FILE` deep-merges over it. **If a new document convention
   requires a code change, the design is wrong** — push specifics into YAML.
4. **Runner** — extract, fan out, aggregate, cap, serialize. No domain knowledge.

### The `Finding` record

Shared by every checker; changing it is a breaking change across the repo.

```
check      str        stable rule id, e.g. "terminology.variant"
category   str        grammar|style|readability|terminology|acronym|structure|units|claim
severity   str        error | warning | review
line, col  int        1-based
excerpt    str        short, trimmed
message    str        one line, imperative
section    str|None   nearest enclosing heading
suggestion str|None   the replacement, when mechanical and safe
```

`severity: review` is load-bearing, not a softer warning. Claim, hedging, and overclaiming
checks emit **only** `review`, and nothing marked `review` is ever auto-applied. This is the
boundary between deterministic checking and judgment; it must never blur.

## Scope discipline

Each addition costs install weight, runtime, and report noise.

**In:** Markdown/LaTeX/plain text · Vale · readability (`textstat`) · sentence length ·
terminology · acronyms · structure · units · claim calibration · JSON and Markdown reports.
The extractor also indexes citations and labels; no checker consumes them yet.

**Deferred:** DOCX/PDF extraction (Pandoc/PyMuPDF weight); spaCy/Stanza (hundreds of MB for
segmentation a regex handles); Pint (these checks are formatting, not unit calculus); DOI
network validation (breaks determinism); statistical-reporting checks; figure/table
cross-references; `--profile NAME` layering (purely additive later).

**Vale over LanguageTool:** one static binary, offline and deterministic, versus a Java
server. Vale is pinned in `pyproject.toml`, but the checker must degrade around it: if the
binary is unavailable, emit one `vale.unavailable` warning and continue. Never abort.

## Commands

`uv` manages Python; `uv.lock` is committed, `requires-python = ">=3.11"`.

```bash
uv sync
uv run prose-preflight FILE --md PREFLIGHT.md
uv run pytest                                # or: -k units
uv run ruff check . && uv run ruff format .
```

Pushing a `v*` tag publishes to PyPI via trusted publishing; the workflow asserts the tag
matches the packaged version. CI smoke-tests the built wheel with `uv run --isolated`, so a
missing `default.yaml` or unresolvable Vale binary fails there, not in a user's environment.

## Tests

`tests/fixtures/` pairs intentionally flawed documents with expected findings;
`tests/test_checks.py` asserts the exact set of `(check, line)` pairs per checker. That is
what keeps checkers from drifting into false positives, which cost far more than misses —
each one burns agent tokens and spends trust in the report. `tests/test_packaging.py`
guards package data and the entry point.

## The contract

`prose-preflight.yaml` carries a top-level `contract:` block beside `checks:`. No checker
reads it; `report()` echoes it into the JSON and `render_md()` into the Markdown, so the
agent judging `review` findings knows the document's audience, venue, and voice. Same file
as `checks:` deliberately — one init, one file, nothing to drift.

`contract.format` (`md` | `tex` | `txt`) is the one key with a closed set of values. It
names the format `prose-draft` writes and the comment syntax of the `prose-draft` /
`prose-edit` markers. Markdown and LaTeX comments are masked by the extractors, so markers
never reach a report; plain text has no comment syntax, so a `txt` marker is visible to the
checkers — the cost of allowing that format.

`prose-init` conducts the interview and writes the file by piping JSON answers into
`prose-preflight --init`: the agent supplies data, Python serializes and validates. A skill
hand-writing YAML would be non-deterministic, which is the trade this repo never makes.
