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
uvx prose-preflight FILE
```

The tool writes the **full** report to `PREFLIGHT_<filename>.md` itself and prints a
capped JSON summary to stdout, whose `report` field is where that file landed — always
take the path from there rather than guessing it. You read only stdout. Never transcribe findings into the file by
hand — that would pull every finding through context, which is the thing this design
exists to avoid.

`FILE` is the path the user gave. If they gave none, ask for one — never guess, never
scan the repo.

A `prose-preflight.yaml` in the working directory is picked up automatically; say so in
your report when the run prints `using prose-preflight.yaml` on stderr. Its `contract`
block comes back in the JSON — that is the project's writing contract, and it is what
you judge `review` findings against. If `contract` is empty, offer `prose-init` in your
next steps, once, and move on.

Options: `--config FILE` (deep-merged over the bundled config; the project file is used
when this is omitted), `--checks a,b` (subset), `--md PATH` (move the Markdown report),
`--max-findings N` (default 20; `0` lifts the stdout cap — rarely needed, the full
report is already on disk).

Vale ships with the package. If its binary is unavailable anyway, the run emits one
`vale.unavailable` warning and every other check still reports.

## Report shape

```json
{
  "file": "paper.md",
  "report": "PREFLIGHT_paper.md",
  "checks": ["acronym", "claim", "readability", "..."],
  "contract": {"document": "journal article", "audience": "...", "venue": "...", "voice": "..."},
  "total": 87,
  "counts": {"severity": {...}, "category": {...}, "section": {...}},
  "truncated": {"style": 37},
  "findings": [
    {"check": "terminology.variant", "category": "terminology", "severity": "error",
     "section": "Methods", "line": 42, "col": 7, "excerpt": "...",
     "message": "Use 'data set', not 'dataset'.", "suggestion": "data set"}
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

Keep the chat message short; the report file holds the detail.

1. **Diagnosis**, two or three sentences, before any list. Read `counts.section` and
   `counts.category` for the shape of the problem and say what it means: "Methods
   carries 60% of the readability flags"; "the terminology drift is one word used both
   ways throughout, not 14 separate mistakes". No checker can write this paragraph —
   it is why you are here. Then the headline numbers and the path from `report`.
2. **Errors** from the stdout summary: `file:line` · message · `suggestion` when
   present.
3. **Warnings**, collapsed by check ("14× terminology.variant 'dataset' → 'data set'"),
   not listed one by one.
4. **Review items**, in their own section, each with a **verdict**: `keep`, `soften`,
   or `cut`, plus a one-line rewrite. These are hedges and boosters — the checker can
   only see that the word is there, you can weigh it against the argument. Weigh it
   against `contract` — venue and audience decide what counts as overclaiming, voice
   decides what counts as too hedged — not against generic good prose. Judge from
   the `excerpt` and whatever of the document is already in context; where the excerpt
   is too thin to judge, say so rather than guessing. A verdict is a recommendation,
   never an edit.
5. **Next steps:** two or three concrete options, each naming what you would run, e.g.
   "apply the 14 terminology fixes", "accept the soften verdicts", "run prose-edit to
   apply the ones you pick", "run prose-init to
   set the contract" (only when `contract` is empty), "run prose-deepread
   for claim-vs-evidence and define-before-use — it reads the whole document, so it is
   slower and costs more context than this run".

Then stop. Wait for the user to choose.

## Hard rules

- **Never edit the document.** Not errors, not mechanical suggestions, not typos. The
  report is the deliverable. Edit only when the user asks for a specific fix in a
  later turn.
- **Never read the source document to find problems.** Findings carry `line`, `col`,
  and `excerpt`; that is the whole context you need.
- **Never auto-apply anything marked `review`.** It is a judgment call, not a softer
  warning. Give it a verdict, not a restatement — and never an edit.
- Never restate a finding's message in your own words when the message is already one
  line — pass it through. `review` items are the exception: they get your judgment.
- Never chain into `prose-deepread` on your own. Offer it; run it only when asked.
