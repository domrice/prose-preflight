---
name: prose-outline
description: Plan the structure of a manuscript — paper, blog post, or newspaper article — or re-plan an existing draft. Proposes the document's claim and one section per question the reader will ask, waits for approval, then writes headings and one intent comment per section into the file; never body text. Use when asked to outline, plan, structure, or restructure a document.
argument-hint: "[file]"
user-invocable: true
allowed-tools:
  - Bash(uvx prose-preflight *)
---

# prose-outline

The skill that comes before `prose-draft`. Draft plans one passage; this one plans the
document. The plan lands in the manuscript itself — headings, and under each one an intent
comment saying what the section must deliver — so `prose-draft` finds its anchor and
`prose-deepread` finds the promise each section is judged against.

Four gates, in order. Do not advance until each one holds.

## 1. Contract — hard gate

Read `prose-preflight.yaml` in the working directory. **No file, no contract, no outline.**
Genre, audience, and venue decide the shape — a journal article, a blog post, and a news
story answer different questions in a different order. Say the contract is missing, point
at `prose-init`, and stop.

If `contract.guide` is set, read that file too. **Named but missing is a broken contract:**
say so, point at `prose-init`, and stop. An unset `guide` means the YAML is the whole
contract.

## 2. Material — hard gate

**New document.** Ask, in one pass: the one thing the reader must take away; what the
material is — results, sources, the story's facts; what the reader already believes or
asks first; target length. Then stop and wait. Never outline from a topic alone.

**Existing draft.** Read the headings and the opening paragraph of each section — the topic
sentences carry the argument — not the whole file. Say what the draft argues as you found
it, in two or three sentences. Ask only what the headings cannot tell you. A full read for
content problems is `prose-deepread`; offer it, never chain into it.

## 3. Plan — hard gate

Propose, before writing anything:

- the document's claim, in one sentence;
- one line per section: heading, and what the reader knows after it that they did not
  before. Order them as the reader's questions arrive, not as the work happened;
- for an existing draft, a numbered list of structural changes — move, merge, split,
  rename, cut — each naming the section it touches and why.

Use the genre's conventions where the contract implies one (IMRaD, inverted pyramid, hook
and payoff); `checks.structure.required_sections`, when set, overrides them. Then stop and
wait. A plan is cheap to redirect; a restructured draft is not.

## 4. Write the skeleton

On approval, insert into the file — creating it when new, in `contract.format`:

- each approved heading that does not exist yet;
- an intent comment on the line directly below every planned heading, new or existing.

The intent is the section's deliverable from the plan, one line. Syntax follows
`contract.format`:

| `format` | intent comment                            |
| -------- | ----------------------------------------- |
| `md`     | `<!-- prose-outline: what it delivers -->` |
| `tex`    | `% prose-outline: what it delivers`        |
| `txt`    | `# prose-outline: what it delivers`        |

The `md` and `tex` comments are masked by the extractor and never reach a preflight report.
Plain text has neither comments nor headings the checkers index: a `txt` outline is visible
to the checkers, and `required_sections` cannot check it. Say so once.

When the headings are fixed, offer to record them as `checks.structure.required_sections`,
so every later preflight run checks presence and order. On a yes, send only that key;
`--merge` keeps the rest of the file:

```bash
uvx prose-preflight --init --merge <<'JSON'
{"checks": {"structure": {"required_sections": ["Introduction", "Methods", "..."]}}}
JSON
```

Skip it for a document with no headings — a news story's structure lives in its
paragraphs, and the intent comments carry it alone.

## Then

Report in two or three lines what went where. For an existing draft, repeat the numbered
structural changes the skeleton did not make: they move or rename existing text, which is
`prose-edit`'s job, and the user can select them by number. Offer `prose-draft` for the
first empty section — offer it, never run it.

## Hard rules

- **No `prose-preflight.yaml`, no outline.** Run `prose-init` first.
- **A guide named by `contract.guide` and missing from disk is a stop, not a warning.**
- **Never write without plan approval** in this conversation.
- **Headings and intent comments only.** Never write body text, and never move, rename,
  rewrite, or delete existing text — list those changes for `prose-edit`.
- Never remove an existing intent comment or `prose-draft` / `prose-edit` marker. Replace
  an intent comment only when the approved plan changed that section's deliverable.
- **Never invent a result, a source, or a fact** to fill a section. An empty section is the
  honest output; name what it is waiting for.
- Never chain into `prose-draft`, `prose-edit`, `prose-preflight`, or `prose-deepread`.
  Offer them.
