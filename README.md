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

> No server. No API key. No network. Five agent skills over eight deterministic checkers.
> Same input, same findings, every time.

An LLM asked to proofread a text reads all 9,000 words into its context, forgets the middle,
and invents a citation error on page 4. This doesn't. The checkers find the problems and
hand over line, column, and a short excerpt; the agent judges and reports, and never reads
the manuscript to find anything.

## Install

**Claude Code plugin**

```
/plugin marketplace add domrice/prose-preflight
/plugin install prose
```

**Any other harness** (Cursor, Codex, Copilot, Gemini, Windsurf, …)

```bash
npx skills@latest add domrice/prose-preflight
```

Both resolve the package from PyPI — no repo on disk, no paths in `SKILL.md`. Needs
[uv](https://docs.astral.sh/uv/); it supplies its own [Python ≥ 3.11](https://www.python.org).

## The five skills

```
/prose-init         once per project — writes the contract
/prose-preflight    check and report            ┐
/prose-deepread     read end to end and report  ┘ never edit
/prose-draft        write new prose             ┐
/prose-edit         apply findings you picked   ┘ only with your yes
```

- **`prose-init`** interviews you once — what you are writing, who reads it, which venue and
  style, which terms and acronyms — and writes `prose-preflight.yaml`. The other four read it.
- **`prose-preflight`** runs the checkers and diagnoses the result: what the counts mean, and
  a verdict on every `severity: review` finding — `keep`, `soften`, or `cut`, with a rewrite.
  A checker can see a hedge; only the agent can weigh it against your argument.
- **`prose-deepread`** is the opposite: it reads the manuscript end to end for what no regex
  reaches — claims the results do not support, terms used before they are defined, sections
  that do not deliver what their heading promises, passages that can go. Expensive, so it
  runs only when you ask for it by name.
- **`prose-draft`** is the only one that writes new text. Give it content — bullets, notes,
  numbers — and it proposes an outline, waits for your yes, drafts against the contract, and
  inserts under the heading you named. No contract, no draft; no content, only questions.
- **`prose-edit`** closes the loop: it applies the findings you picked out of a report, and
  only those. It reads the paragraph around each finding rather than the file, previews every
  change before touching disk, and marks what it changed. A `review` finding is edited only
  because you named it.

## The contract

One file per project, `prose-preflight.yaml`, holds both halves of your setup. Run
`/prose-init` once; it writes the file through the tool, so the YAML is serialized and its
keys validated, never hand-typed. A `prose-preflight.yaml` in the working directory is
picked up automatically.

The `contract:` block is **agent-facing** — no checker reads it, but every report carries it,
so the agent judging your hedges knows whether "may indicate" is right for your journal. The
`checks:` block is the deterministic half.

```yaml
contract:
  document: conference paper
  audience: graphics researchers, non-specialist in differentiable rendering
  venue: SIGGRAPH — ACM house style, numbered citations
  voice: first person plural, past tense for methods, active where possible
  format: tex # md | tex | txt

checks:
  terminology:
    terms:
      ray tracing: [raytracing, ray-tracing]
      signed distance field: [SDF, signed-distance field]
  sentence_length:
    max_words: 32
  structure:
    required_sections:
      [Abstract, Introduction, Related Work, Method, Results, Conclusion, References]
  units:
    disabled_rules: [range_dash] # if your venue insists on hyphens
```

Keep only what you change; the rest falls back to defaults. Lists are replaced, not appended,
and unknown keys are reported on stderr, so a typo never fails silently.

Two lists ship **empty**, because a wrong entry costs a false positive on every run:
`terminology.terms` and `structure.required_sections`. Fill them in and those checks switch on.

Everything a document convention needs lives in YAML. If a new convention would need a code
change, that's a bug in the checker.

## Checks

| check                                                                               | flags                                                             | severity      |
| ----------------------------------------------------------------------------------- | ----------------------------------------------------------------- | ------------- |
| `vale.*`                                                                            | grammar, spelling, style — whatever your Vale config says         | error/warning |
| `terminology.variant`                                                               | `dataset` where the config wants `data set` (opt-in)              | warning       |
| `acronym.undefined`                                                                 | used without expansion at first use                               | warning       |
| `structure.missing_section` · `.section_order`                                      | required sections, absent or out of order (opt-in)                | error/warning |
| `sentence_length.long`                                                              | sentences over `max_words`                                        | warning       |
| `readability.flesch` · `.fog`                                                       | per section, skipping ones too short to score                     | warning       |
| `units.space_before_unit` · `.percent_spacing` · `.range_dash` · `.p_value_spacing` | `12 mm` → NBSP, `5 %` → `5%`, `3-7` → `3–7`, `p<.05` → `p < 0.05` | warning       |
| `claim.hedge` · `.booster`                                                          | "may possibly suggest", "clearly demonstrates"                    | **review**    |

`review` is not a quieter warning. It is the line between what a script can decide and what
it cannot: whether your evidence carries your claim. Nothing marked `review` is ever
auto-applied, by the tool or the agent.

Code, math, verbatim blocks, and LaTeX command sequences are blanked before any regex runs —
character-for-character, so every offset stays a true source position. Your equations are not
prose and are not judged as such.

The full report lands in `PREFLIGHT_<file>.md`, one per document; only a capped summary goes
through the agent's context. That split is the whole point.

## Vale

[Vale](https://vale.sh) powers grammar and style and is pinned as a dependency — no
`brew install`, no manual step. The binary is fetched once on first run and cached; after
that, runs are offline. If that download is blocked (air-gapped, proxy, locked-down CI), the
run emits one `vale.unavailable` warning and the other seven checkers still report. Vale is
never a hard prerequisite; install it yourself and it's picked up from `PATH`.

Vale has no LaTeX reader, so a `.tex` file is handed to it as masked prose — commands,
preamble, math, and verbatim already blanked, line for line — and the alerts still carry true
source positions.

## Develop

```bash
git clone https://github.com/domrice/prose-preflight && cd prose-preflight
uv sync && uv run pytest
```

Every checker has a fixture pair in `tests/fixtures/`: an intentionally flawed document and
the exact set of `(check, line)` pairs it must produce. Pinning positions is deliberate —
false positives cost more here than misses, since each one burns agent tokens and spends
trust in the report.

Adding a checker is one module exposing `check(doc, rule) -> list[Finding]` plus one line in
the registry. If it also needs a change to the runner, the design was wrong.

## License

MIT
