<div align="center">

# Prose Preflight

**Your manuscript, checked by scripts, read by an agent.**

[![PyPI](https://img.shields.io/pypi/v/prose-preflight?style=flat-square&logo=pypi&logoColor=white&color=fa934e&labelColor=121417)](https://pypi.org/project/prose-preflight/)
[![Python](https://img.shields.io/badge/python-%E2%89%A5%203.11-fa934e?style=flat-square&logo=python&logoColor=white&labelColor=121417)](https://www.python.org)
[![Vale](https://img.shields.io/badge/Vale-bundled-fa934e?style=flat-square&labelColor=121417)](https://vale.sh)
[![uv](https://img.shields.io/badge/uv-managed-fa934e?style=flat-square&logo=uv&logoColor=white&labelColor=121417)](https://docs.astral.sh/uv/)
[![License](https://img.shields.io/badge/license-MIT-fa934e?style=flat-square&labelColor=121417)](LICENSE)
[![last commit](https://img.shields.io/github/last-commit/domrice/prose-preflight?style=flat-square&color=fa934e&labelColor=121417)](https://github.com/domrice/prose-preflight/commits/main)

</div>

---

> No server. No API key. No network. No opinions about your argument.
> Eight deterministic checkers read a Markdown, LaTeX, or plain-text manuscript and emit one
> compact JSON report. The scripts analyze; the agent reports. Same input, same findings,
> every time.

An LLM asked to proofread a text will read all 9,000 words into its context, forget the
middle, and confidently invent a citation error on page 4. This tool doesn't. The checkers
find the problems and hand over line, column, and a short excerpt — the agent summarizes
that and never reads the manuscript to find anything.

## Install

**1. Claude Code plugin**

```
/plugin marketplace add domrice/prose-preflight
/plugin install prose-preflight
```

**2. Any other harness** (Cursor, Codex, Copilot, Gemini, Windsurf, …)

```bash
npx skills@latest add domrice/prose-preflight
```

**3. CLI only, no agent** — for CI or pre-commit

```bash
uvx prose-preflight text.md
```

**4. From source** (contributors)

```bash
git clone https://github.com/domrice/prose-preflight && cd prose-preflight
uv sync && uv run pytest
```

Routes 1–3 resolve the package from PyPI, so none of them needs the repo on disk and
`SKILL.md` carries no paths. Needs [Python ≥ 3.11](https://www.python.org); `uvx` supplies
its own interpreter, so route 3 needs nothing but [uv](https://docs.astral.sh/uv/).

## Use

```bash
uvx prose-preflight text.md
```

The full report is written to `PREFLIGHT_text.md` — one per document, so checking a second
file never overwrites the first. A capped JSON summary goes to stdout, with `report` naming
that file. That split is
the whole point — the agent reads stdout, links the file, and stays small.

| flag               | does                                             |
| ------------------ | ------------------------------------------------ |
| `--md PATH`        | move the report (default `PREFLIGHT_<file>.md`)  |
| `--max-findings N` | cap stdout findings (default `20`; `0` lifts it) |
| `--checks a,b`     | run a subset                                     |
| `--config FILE`    | deep-merge a YAML file over the bundled config   |
| `--version`        | the packaged version                             |

Findings are capped round-robin across categories, so 400 Vale alerts cannot crowd out the
one missing Methods section. `counts` and `total` always cover everything; `truncated` says
what was dropped.

## The two skills

The CLI is deterministic on purpose — offline, no API key, same input same output. So
nothing calls a model inside it. The judgment lives in the agent that drives it, where
it is free, and it ships as two skills:

- **`prose-preflight`** runs the command and reports it, but does not just print it. It
  diagnoses what the counts mean, and gives every `severity: review` finding a verdict —
  `keep`, `soften`, or `cut`, with a rewrite. The checker can see that a hedge is there;
  only the agent can weigh it against the argument. It never edits the document.
- **`prose-deepread`** is the opposite of preflight: it reads the manuscript end to end
  and looks for what no regex can reach — claims the results do not support, terms used
  before they are defined, sections that do not deliver what their heading promises, and
  passages that can be cut without losing an argument. Expensive, so it runs only when
  you ask for it by name. It never edits either.

## Config

Every check is configurable from one YAML file. Write it once per project:

```bash
uvx prose-preflight --init-config    # writes prose-preflight.yaml, every key commented
uvx prose-preflight text.md         # picked up automatically from the working directory
```

A `prose-preflight.yaml` next to where you run is used without any flag; `--config FILE`
points elsewhere. Keep only what you change — the rest falls back to the defaults. Lists are
replaced, not appended, and unknown keys are reported on stderr, so a typo never fails
silently.

Two lists ship **empty**, because there is no universal right answer and a wrong entry costs
you a false positive on every run: `terminology.terms` (your journal's preferred spellings)
and `structure.required_sections` (most documents are fragments, not whole papers). Fill
them in and those checks switch on.

```yaml
checks:
  terminology:
    terms:
      finite element: [finite-element, FE]
  sentence_length:
    max_words: 32
  structure:
    required_sections:
      [Abstract, Introduction, Methods, Results, Discussion, References]
  units:
    disabled_rules: [range_dash] # if your journal insists on hyphens
```

Everything a document convention needs lives in YAML. If a new convention would need a code
change, that's a bug in the checker, not a missing feature.

## Checks

| check                                                                               | flags                                                             | severity      |
| ----------------------------------------------------------------------------------- | ----------------------------------------------------------------- | ------------- |
| `vale.*`                                                                            | grammar, spelling, style — whatever your Vale config says         | error/warning |
| `terminology.variant`                                                               | `dataset` where the config wants `data set` (opt-in: `terms`)     | warning       |
| `acronym.undefined`                                                                 | used without expansion at first use                               | warning       |
| `structure.missing_section` · `.section_order`                                      | required sections, absent or out of order (opt-in)                | error/warning |
| `sentence_length.long`                                                              | sentences over `max_words`                                        | warning       |
| `readability.flesch` · `.fog`                                                       | per section, skipping ones too short to score                     | warning       |
| `units.space_before_unit` · `.percent_spacing` · `.range_dash` · `.p_value_spacing` | `12 mm` → NBSP, `5 %` → `5%`, `3-7` → `3–7`, `p<.05` → `p < 0.05` | warning       |
| `claim.hedge` · `.booster`                                                          | "may possibly suggest", "clearly demonstrates"                    | **review**    |

`review` is not a quieter warning. It is the line between what a script can decide and what
it cannot: hedging and overclaiming are judgment calls about whether your evidence carries
your claim. Nothing marked `review` is ever auto-applied, by either the tool or the agent.

Code, math, verbatim blocks, and LaTeX command sequences are blanked before any regex runs —
character-for-character, so every offset stays a true source position. Your equations are
not prose and are not judged as such.

## Vale

[Vale](https://vale.sh) powers grammar and style and is pinned as a dependency — no
`brew install`, no manual step. The binary is fetched once on first run and cached; after
that, runs are offline.

Vale has no LaTeX reader, so a `.tex` file is handed to it as masked prose — commands,
preamble, math, and verbatim already blanked, line for line — and the alerts still carry true
source positions. Markdown and plain text go to Vale directly, parsed by its own reader.

If that download is blocked (air-gapped machine, proxy, locked-down CI), the run emits one
`vale.unavailable` warning and the other seven checkers still report. Vale is never a hard
prerequisite. Install it yourself and it's picked up from `PATH`:

```bash
brew install vale     # or: apt install vale / scoop install vale
```

## Develop

```bash
uv sync                                    # from the lockfile
uv run prose-preflight text.md --md out.md
uv run pytest                              # all tests
uv run pytest tests/test_checks.py -k units
uv run ruff check . && uv run ruff format .
```

Every checker has a fixture pair in `tests/fixtures/`: an intentionally flawed document and
the exact set of `(check, line)` pairs it must produce. Pinning positions is deliberate —
false positives cost more here than misses, since each one burns agent tokens and spends
trust in the report.

Adding a checker is one module exposing `check(doc, rule) -> list[Finding]` plus one line in
the registry. If it also needs a change to the runner, the design was wrong.

## License

MIT
