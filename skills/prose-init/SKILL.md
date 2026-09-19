---
name: prose-init
description: Interview the user about a writing project — what it is, who reads it, which venue and style, which terms and acronyms — and write the result to prose-preflight.yaml, the contract that prose-preflight and prose-deepread read on every run. Use when starting a new manuscript, when no prose-preflight.yaml exists yet, or when asked to set up or update the prose contract.
argument-hint: "[path]"
user-invocable: true
allowed-tools:
  - Bash(uvx prose-preflight *)
---

# prose-init

One interview, one file. `prose-preflight.yaml` holds both halves of a project's
writing setup: a `contract:` block that tells an agent what the document is meant to
be, and the `checks:` keys that ship empty because only the author knows them.

**Never write the YAML by hand.** You supply the answers as JSON; the tool serializes
them, and validates the keys against the bundled defaults while it does.

If `prose-preflight.yaml` already exists, read it, show what it says, and ask what to
change. Re-run with the merged answers — the write replaces the file.

## The questions

Ask them in one pass, not one at a time. Offer concrete options; the user can always
answer freely. Omit any key they skip — never invent a value.

| ask                                                     | lands in                        |
| ------------------------------------------------------- | ------------------------------- |
| What are you writing?                                   | `contract.document`             |
| Who reads it, and what do they already know?            | `contract.audience`             |
| Where does it go — journal, conference, course, team? Does it have a style guide? | `contract.venue` |
| Voice: first or third person, past or present, passive or active? | `contract.voice`      |
| Anything else — banned words, citation style, house rules? | `contract.notes`             |
| Which file format do you write in?                      | `contract.format`               |
| Terms with one preferred spelling? Acronyms that never need expanding? | `checks.terminology.terms`, `checks.acronym.allowlist` |
| Required sections, in order? (skip for a fragment)      | `checks.structure.required_sections` |

`format` is one of `md`, `tex`, `txt` — nothing else. These are the formats the tools
read and a skill can write; a closed binary format like `.docx` is not one of them, so
never record it, even if the user names it. `prose-draft` reads this key to pick the
file it writes and the comment syntax it marks its paragraphs with.

`terms` maps the **preferred** form to the variants that should become it:
`{finite element: [finite-element, FE]}`. `allowlist` and `required_sections` replace
the defaults rather than appending, so repeat the bundled acronyms you still want.

## Write it

```bash
uvx prose-preflight --init <<'JSON'
{
  "contract": {
    "document": "journal article",
    "audience": "structural engineers, non-specialist in machine learning",
    "venue": "Engineering Structures — Elsevier house style, numbered citations",
    "voice": "first person plural, past tense for methods, active where possible",
    "format": "md"
  },
  "checks": {
    "terminology": {"terms": {"finite element": ["finite-element", "FE"]}},
    "structure": {"required_sections": ["Abstract", "Introduction", "Methods", "Results", "Discussion", "References"]}
  }
}
JSON
```

`--init PATH` writes elsewhere; the default is `prose-preflight.yaml` in the working
directory, which every later run picks up with no flag. Unknown keys are reported on
stderr — if you see one, you mistyped it, so fix it and re-run.

## Then

Confirm in two or three lines what the contract now says, and offer the obvious next
step: `prose-preflight FILE` on something already written, or `prose-draft` on something
not written yet. Do not run either yourself unless asked.
