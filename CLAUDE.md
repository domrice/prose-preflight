# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

## What this repo is

`prose-preflight` is an **agent skill**: deterministic CLI checkers plus a thin `SKILL.md`
that tells an agent how to drive them. The scripts are the analyzer, not the agent.

The agent runs one command, reads one compact JSON report, and reports it. It does **not**
edit the document — not errors, not mechanical suggestions. Fixes happen only when the user
asks for a specific one in a later turn. `skills/prose-preflight/SKILL.md` is the binding
agent contract: report, never edit, never auto-apply `review`.

No model is ever called from inside the Python — that would cost determinism, offline runs,
and per-run money, which is the same trade that ruled out LanguageTool. Judgment lives in the
agent turn: preflight gives `review` findings a verdict, and `prose-deepread` is the one
opt-in exception to "never read the source", run only when the user asks for it by name.

## The token-efficiency contract

This is the reason the project exists. Violating it defeats the skill.

- **One command, one report.** `run_all.py` once, one JSON document. Never invoke individual
  checkers, never read Vale output, never pipe raw tool stdout into context.
- **Never read the source document to find problems.** Findings carry `line`/`col` and a
  short `excerpt`, so edits can be targeted without a full read.
- **Reports are summarized by default.** Top level is counts by severity/category/section;
  findings are capped (`--max-findings`, default 20), filled round-robin across categories so
  one noisy category cannot crowd out the rest; `--max-findings 0` lifts the cap. Never let a
  900-issue Vale run flood the transcript.
- **`--md PATH` writes the full report to disk.** The agent summarizes stdout and links the
  file; it never transcribes findings through context.
- **`SKILL.md` stays short** (< 120 lines): the workflow and the JSON shape, nothing else.
  Rule catalogs and rationale live in `README.md` and `default.yaml`'s comments.
- **No checker prints prose.** Diagnostics to stderr; stdout is JSON only.

## Layout

```
src/prose_preflight/
  finding.py    the one record every checker emits
  run_all.py    CLI: extract, fan out, aggregate, cap, serialize
  default.yaml  the only config; package data, resolved via importlib.resources
  extract/      document.py (Document + shared passes), markdown.py, latex.py
  checks/       acronym claim readability sentence_length structure terminology units vale
                + _text.py (shared helpers) + __init__.py (CHECKERS registry)
skills/prose-preflight/SKILL.md   the agent-facing workflow
skills/prose-deepread/SKILL.md    the opt-in full-read pass (the only thing allowed to read the source)
.claude-plugin/                   plugin.json + marketplace.json
```

Four layers, each replaceable without touching the others. The constraints that make that
true:

1. **Extraction** — `extract/__init__.py` dispatches on file suffix (unknown suffix reads as
   plain text). `Document.masked` is a character-for-character copy of the source with fenced
   code, display math, inline code and inline math replaced by spaces, so a regex over
   `masked` yields match offsets that *are* the source `line`/`col`. Every indexed element
   keeps its 1-based source line. A reader that loses line numbers is not acceptable — every
   downstream finding depends on it.

2. **Checkers** — each module exposes exactly `check(doc: Document, rule: dict) ->
   list[Finding]`. Pure, stateless, knowing nothing about each other. They receive their
   slice of the resolved config; the runner does the lookup, the `enabled` gate, and the
   sorting, so checkers may return findings in any order. Adding a checker is a module plus
   one line in `CHECKERS` — never a change to the runner's logic.

3. **Config** — one bundled `default.yaml`, shipped as package data (a repo-root `profiles/`
   would be invisible to `uvx`, which runs from a cached wheel). `--config FILE` deep-merges
   over it. **If a new document convention requires a code change, the design is wrong** —
   generalize the checker and push the specifics into YAML.

4. **Runner** — extracts, fans out, aggregates, caps, serializes. No domain knowledge.

### The `Finding` record

One dataclass, shared by every checker. Changing it is a breaking change across the repo.

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

`severity: review` is a load-bearing distinction, not a softer warning. Claim-calibration,
hedging, and overclaiming checks emit **only** `review`. Nothing marked `review` is ever
auto-applied — it is surfaced to a human or reasoned about by the agent in context. This is
the boundary between deterministic checking and qualitative judgment, and it must never blur.

## Scope discipline

Each addition costs install weight, runtime, and report noise.

**In:** Markdown/LaTeX/plain text · Vale · readability (`textstat`) · sentence-length outliers
· terminology · acronyms · section structure · numbers and units · claim calibration · JSON
and Markdown reports. The extractor also indexes citations and labels; no checker consumes
them yet.

**Deferred:** DOCX/PDF extraction (Pandoc/PyMuPDF weight); spaCy/Stanza (hundreds of MB for
segmentation `textstat` plus a regex already handles); Pint (a unit *calculus*, where these
checks are formatting — NBSP, `%` spacing, ranges, p-values — so regex is right); DOI network
validation (breaks determinism and offline runs); statistical-reporting checks;
figure/table cross-references; `--profile NAME` layering (one audience today; adding it later
is a lookup returning a bundled path, purely additive).

**Vale over LanguageTool:** a single static binary with YAML config, fully offline and
deterministic, versus a Java server or API that makes runs non-reproducible. Vale is pinned in
`pyproject.toml` and ships with the package, but the checker must still degrade around it: if
the binary is unavailable, emit one `vale.unavailable` warning and continue. Never abort.

## Commands

Python is managed with `uv`; `uv.lock` is committed and `requires-python = ">=3.11"`.

```bash
uv sync                                                 # install, from the lockfile
uvx prose-preflight FILE                                # the distributed invocation
uv run prose-preflight FILE --md PREFLIGHT.md           # from source, full report to disk
uv run prose-preflight FILE --checks terminology,acronym --max-findings 0
uv run pytest                                           # all tests
uv run pytest tests/test_checks.py -k units             # one test
uv run ruff check . && uv run ruff format .
```

Pushing a `v*` tag publishes to PyPI via trusted publishing (`.github/workflows/release.yml`,
which also asserts the tag matches the packaged version). CI smoke-tests the built wheel with
`uv run --isolated`, so a `default.yaml` missing from the wheel or an unresolvable Vale binary
fails there rather than in a user's environment.

## Tests

Fixtures in `tests/fixtures/` are intentionally flawed documents paired with expected-findings
JSON. `tests/test_checks.py` parametrizes one pair per checker and asserts the exact set of
`(check, line)` pairs — this is what keeps checkers from drifting into false positives, which
are far more costly here than misses: every false positive burns agent tokens and erodes trust
in the report. `tests/test_packaging.py` guards the package data and entry point.
