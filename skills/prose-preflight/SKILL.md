---
name: prose-preflight
description: Run deterministic prose checks on a Markdown, LaTeX, or plain-text document (grammar, style, readability, terminology, acronyms, structure, units, claim calibration) and report the findings. Read-only — it never edits the document. Use when asked to proofread, copy-edit, preflight, or review a paper, report, or manuscript.
argument-hint: "[file]"
user-invocable: true
allowed-tools:
  - Bash(uvx prose-preflight *)
---

# prose-preflight

The scripts analyze. You report. Run one command on the file the user named, read one
JSON report, summarize it. **Do not edit the document.**

## Run

```bash
uvx prose-preflight FILE --md PREFLIGHT.md
```

The tool writes the **full** report to `PREFLIGHT.md` itself and prints a capped JSON
summary to stdout. You read only stdout. Never transcribe findings into the file by
hand — that would pull every finding through context, which is the thing this design
exists to avoid.

`FILE` is the path the user gave. If they gave none, ask for one — never guess, never
scan the repo.

Options: `--md PATH` (write the full Markdown report there), `--config FILE` (YAML
deep-merged over the bundled config), `--checks a,b` (subset), `--max-findings N`
(default 20; `0` lifts the stdout cap — rarely needed once `--md` is used).

Vale ships with the package. If its binary is unavailable anyway, the run emits one
`vale.unavailable` warning and every other check still reports.

## Report shape

```json
{
  "file": "paper.md",
  "checks": ["acronym", "claim", "readability", "..."],
  "total": 87,
  "counts": {"severity": {...}, "category": {...}, "section": {...}},
  "truncated": {"style": 37},
  "findings": [
    {
      "check": "terminology.variant",
      "category": "terminology",
      "severity": "error",
      "section": "Methods",
      "line": 42,
      "col": 7,
      "excerpt": "...",
      "message": "Use 'data set', not 'dataset'.",
      "suggestion": "data set"
    }
  ]
}
```

`category`: grammar | style | readability | terminology | acronym | structure | units | claim.
`severity`: `error` | `warning` | `review`.
`suggestion` is present only when the fix is mechanical and safe.

`counts` and `total` always cover every finding. `findings` is capped, filled
round-robin across categories so one noisy category cannot crowd out the rest;
`truncated` says how many were dropped per category. `--max-findings 0` lifts the cap.

## What to give the user

Keep the chat message short; `PREFLIGHT.md` holds the detail.

1. **Headline:** total, counts by severity and category, and the path to
   `PREFLIGHT.md`.
2. **Errors** from the stdout summary: `file:line` · message · `suggestion` when
   present.
3. **Warnings**, collapsed by check ("14× terminology.variant 'dataset' → 'data set'"),
   not listed one by one.
4. **Review items**, in their own section. These are claim calibration, hedging, and
   overclaiming — judgment calls, never mechanical. Quote line and excerpt.
5. **Next steps:** two or three concrete options, each naming what you would run, e.g.
   "apply the 14 terminology fixes", "walk the 6 review items one by one", "re-run
   after edits and diff the counts".

Then stop. Wait for the user to choose.

## Hard rules

- **Never edit the document.** Not errors, not mechanical suggestions, not typos. The
  report is the deliverable. Edit only when the user asks for a specific fix in a
  later turn.
- **Never read the source document to find problems.** Findings carry `line`, `col`,
  and `excerpt`; that is the whole context you need.
- **Never auto-apply anything marked `review`.** It is a judgment call, not a softer
  warning.
- Never restate a finding's message in your own words when the message is already one
  line — pass it through.
