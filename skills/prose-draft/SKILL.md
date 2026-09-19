---
name: prose-draft
description: Draft a passage of a manuscript from content the user supplies — bullets, notes, numbers, a described argument — following the writing contract in prose-preflight.yaml, and insert it into the document under a heading the user named. Proposes an outline first and writes nothing until the user approves it. Use when asked to draft, write, or fill in a section, paragraph, or abstract.
argument-hint: "[file] [section]"
user-invocable: true
---

# prose-draft

The one skill here that writes. `prose-preflight` and `prose-deepread` judge a document
against `prose-preflight.yaml`; this one composes against the same file. Same contract,
opposite direction.

Four gates, in order. Do not advance until each one holds.

## 1. Contract — hard gate

Read `prose-preflight.yaml` in the working directory. **No file, no contract, no draft.**

Do not fall back to generic good prose, and do not ask the contract questions inline —
say the contract is missing, point at `prose-init`, and stop. Everything below is defined
relative to the contract, so there is nothing to fall back to.

## 2. Content — hard gate

**Never write prose from a topic.** "Write my methods section" is not content. Content is
a bulleted list, notes, numbers, an argument the user described — something with the
substance already in it. Without that, the only honest output is invention.

So ask. Three or four questions, in one pass, concrete: what was done or found, what the
reader must take away, which results or sources the passage leans on, how long it should
be. Then stop and wait. Asking twice is cheaper than a paragraph of fiction.

## 3. Outline — hard gate

Before any prose, propose:

- the passage's claim, in one sentence;
- one line per paragraph: what it does, and which of the user's inputs it uses;
- the target file and the heading the passage lands under.

Then stop and wait for approval. An outline is cheap to redirect; a draft is not.

## 4. Draft and insert

On approval, write the passage and insert it into the file under the named heading. Then
report in two or three lines what went where, and offer `prose-preflight FILE` as the
next step — offer it, never run it.

## The contract is the rule of law

`voice`, `venue`, `audience`, and `notes` override every default below, including the
default toward concision. If the contract asks for formal, expansive, third-person
passive prose, write that and do not argue. `checks.terminology.terms` gives the
preferred spelling of every term it lists; `checks.acronym.allowlist` says which
acronyms need no expansion. Use them.

**Where the contract is silent**, and only there: one idea per sentence. The claim before
the qualification. Active voice. No throat-clearing ("It is important to note that"), no
metadiscourse ("In this section we will"), no word that earns nothing but length. Every
noun the user supplied survives; nothing appears that they did not supply.

## The marker

Every paragraph this skill writes gets a marker comment on its own line immediately
above, so a later reader — human or agent — can tell drafted prose from reviewed prose.
Syntax follows `contract.format`:

| `format` | marker                 |
| -------- | ---------------------- |
| `md`     | `<!-- prose-draft -->` |
| `tex`    | `% prose-draft`        |
| `txt`    | `# prose-draft`        |

The `md` and `tex` markers are masked by the extractor, so they never reach a preflight
report. Plain text has no comment syntax: the `txt` marker **is** visible to the
checkers. Say so once, the first time you write into a `txt` document.

Never remove a marker. The user strips them when they have reviewed the passage.

## Hard rules

- **No `prose-preflight.yaml`, no draft.** Run `prose-init` first.
- **Never draft without content from the user.** Questions, not prose.
- **Never insert without outline approval** in this conversation.
- **Insert only.** Never rewrite, reflow, or delete existing text — this skill adds
  prose at the approved anchor and touches nothing else in the file. Edits to what is
  already there happen only when the user asks for a specific one.
- **Never invent a result, a citation, or a number** to fill a gap. Report the gap.
- Never omit a paragraph marker.
- Never chain into `prose-preflight` or `prose-deepread`. Offer them.
