---
name: prose-deepread
description: Read a manuscript end to end and report the problems no regex can see — claims the results do not support, terms used before they are defined, sections that do not deliver what their heading promises, and passages that can be cut or tightened. Read-only — it never edits the document. Slower and far more context than prose-preflight; run it only when the user explicitly asks for a deep read.
argument-hint: "[file]"
user-invocable: true
---

# prose-deepread

The companion to `prose-preflight`, and its opposite. Preflight never reads the document
— it runs deterministic checkers and reports their findings. This skill reads the whole
thing, because the four problems below only exist between passages that are far apart.

**This is expensive.** The document enters context in full. Run it only when the user
asks for it by name or asks for a deep/structural/argument read. Never chain into it
automatically after a preflight run, and never run it on a file the user did not name.

If `prose-preflight` has not run on this file yet, run it first and report that
separately. It catches the mechanical problems cheaply, so this pass does not spend
context re-finding them.

## The four passes

Read the document once, then work through all four. Everything you emit is a judgment
call — the equivalent of preflight's `severity: review`. There are no errors here.

**1. Claim vs evidence.** For each claim in the abstract, introduction, and conclusion:
is there a passage in the results that supports it, and at the same strength? Flag
claims with nothing behind them, claims stronger than their evidence, and — the one
people miss — results that support a stronger claim than the abstract makes.

**2. Define before use.** Terms and acronyms that appear before they are defined,
defined more than once, or never defined at all. Preflight's `acronym` checker sees
expansion mechanics; it cannot see argument order. Include domain terms, not just
acronyms.

**3. Heading vs content.** Does each section deliver what its heading promises? Flag
content sitting in the wrong section, headings that describe something the section no
longer contains, and results discussed in Methods or method described in Results.

**4. Cut for length.** Shorter is better. Flag what can go without losing an argument:
a point already made elsewhere in the document, a paragraph that restates its own topic
sentence, throat-clearing before the actual claim, a worked example where one sentence
would do. Give the rewrite, and say roughly how much it saves ("~40 words"). Only a full
read can see the redundancy, because the two passages are usually in different sections.
Never cut a caveat, a limitation, or a qualification that carries meaning — brevity is
not the same as overclaiming, and this skill is the one that flags overclaiming.

## What to give the user

Lead with two or three sentences on the document's argument as you found it — that is
the thing only a full read can tell them. Then the four passes, each as a short list:

`section` · `line` · short excerpt · one line on what is wrong · what you would do.

Nothing in any of these passes is mechanical. Recommend, do not apply. If a pass turns
up nothing, say so in one line and move on — a clean pass is a real result.

## Hard rules

- **Never edit the document.** The report is the deliverable. Edit only when the user
  asks for a specific fix in a later turn.
- **Never invent a citation, a result, or a number** to fill a gap you found. Report the
  gap.
- Do not repeat what `prose-preflight` already reported. If it has not run, run it first
  and keep the two reports separate.
