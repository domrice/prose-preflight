---
name: prose-edit
description: Apply specific findings from a prose-preflight or prose-deepread report to the manuscript — the fixes the user picked, and only those. Rewrites against the writing contract in prose-preflight.yaml, previews every change before touching the file, and marks each paragraph it edits. Use when asked to apply, fix, or act on findings already reported. Not for finding problems — that is prose-preflight.
argument-hint: "[file] [items]"
user-invocable: true
---

# prose-edit

The skill that closes the loop. `prose-preflight` and `prose-deepread` report; this one
acts on the report — on the items the user picked out of it, and on nothing else.

Four gates, in order. Do not advance until each one holds.

## 1. Contract — hard gate

Read `prose-preflight.yaml` in the working directory. **No file, no contract, no edit.**

Say the contract is missing, point at `prose-init`, and stop. Do not fall back to generic
good prose: the contract is the only reason this skill can be trusted to rewrite someone's
sentence.

If `contract.guide` is set, read that file too — it is part of the contract, the
long-form half. **Named but missing is a broken contract:** say so, point at
`prose-init`, and stop, exactly as for a missing `prose-preflight.yaml`. An unset
`guide` is not missing; it means the project has no guide, and the YAML is the whole
contract.

## 2. Selection — hard gate

Act on the items the user named, and only those. Two sources:

- **This conversation** — the usual case. "Do 2 and 5 from what you just said."
- **`PREFLIGHT_<file>.md`** — read it only when the user points at it, and read the lines
  they named. Never swallow the report whole.

Never widen a selection. "Fix the terminology findings" is a selection; "clean up the
Methods section" is not — ask which items. If nothing is selected, list what is on the
table and stop.

## 3. Read narrowly

Findings carry `line`, `col`, and `excerpt`. Read the paragraph around each line, not the
file. Widen only where the selected item's own scope demands it — a move between sections
needs both ends — and say so when you do.

## 4. Preview, then apply

For every item: the current text, the replacement, one line on what changed. Then stop and
wait.

Batch the mechanical ones — `severity: error` with a `suggestion` — into a single preview
block. Fourteen `dataset` → `data set` swaps are one approval, not fourteen. Anything with
judgment in it previews on its own.

There is no ceiling on what a selected item may reach: if the item says a paragraph belongs
in Discussion, move it. The preview is what keeps that safe, so never skip it.

## `review` findings

A `review` finding may be edited **only** because the user selected it by name. Nothing
marked `review` is ever auto-applied — selecting it _is_ the human judgment that severity
exists to require. An unselected `review` item stays untouched, however obvious its fix
looks.

## The marker

Every paragraph this skill changes gets a marker comment on its own line immediately above.
Syntax follows `contract.format`:

| `format` | marker                |
| -------- | --------------------- |
| `md`     | `<!-- prose-edit -->` |
| `tex`    | `% prose-edit`        |
| `txt`    | `# prose-edit`        |

The `md` and `tex` markers are masked by the extractor, so they never reach a preflight
report. Plain text has no comment syntax: the `txt` marker **is** visible to the checkers.
Say so once, the first time you edit a `txt` document.

A paragraph that already carries a `prose-draft` marker keeps it and gains a `prose-edit`
marker. Never swap one for the other — the pair is the honest record. Never remove a
marker; the user strips them when they have reviewed the passage.

## The contract is the rule of law

`voice`, `venue`, `audience`, `notes`, and every rule in the guide override every default
below, **including the default toward concision**. If the contract asks for formal,
expansive, third-person passive prose, write that and do not argue. Where a guide rule and
a contract key disagree, the guide is the more specific statement and wins.
`checks.terminology.terms` gives the preferred spelling of every term it lists;
`checks.acronym.allowlist` says which acronyms need no expansion. Use them.

**Where the contract is silent** — both files — and only there: one idea per sentence. The claim before
the qualification. Active voice. No throat-clearing ("It is important to note that"), no
metadiscourse ("In this section we will"), no word that earns nothing but length. Every
fact, number, and citation in the original survives the rewrite.

## Then

Report in two or three lines: what changed, where, and what you skipped and why. Offer
`prose-preflight FILE` as the re-check — offer it, never run it.

## Hard rules

- **No `prose-preflight.yaml`, no edit.** Run `prose-init` first.
- **A guide named by `contract.guide` and missing from disk is a stop, not a warning.**
- **Only selected items.** Never fix something you noticed along the way — report it and
  let the user select it.
- **Never apply without preview approval** in this conversation.
- **Never delete a caveat, limitation, hedge, citation, number, or result** to tighten
  prose. Brevity is not the same as overclaiming.
- **Never invent a citation, a result, or a number** to patch a gap a finding exposed.
  Report the gap.
- Never remove or replace an existing marker; never omit one on a paragraph you changed.
- Never chain into `prose-preflight` or `prose-deepread`. Offer them.
