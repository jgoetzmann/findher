# Working on findher

Repo conventions for anyone, human or agent, editing this package.

## The one rule

Every refusal is code. If you find yourself writing a paragraph that asks the
model not to do something, stop and write a check in `scripts/guards.py`
instead, then a case in `scripts/selftest.py` that injects the defect and
watches the check fail. Prose refusals get argued past.

A guard you have never seen fail is a guard you are asserting, not testing.

## Before you push

```
python3 scripts/validate-package.py
python3 scripts/selftest.py
```

Both run in CI on every push and both must exit 0. `validate-package.py` reads
files; `selftest.py` runs the machinery against injected defects. Neither has a
`--force`.

## Adding a guard

1. Write the check in `scripts/guards.py`, returning `Finding` objects. Give it
   a `rule` name a test can target and a `because` a human can overrule.
2. Wire it into `scripts/preflight.py`.
3. Add a `@case` to `scripts/selftest.py` that breaks the thing on purpose, and
   a second one that asserts an honest input still passes. A gate that flags
   honest input teaches the user to skim the output.
4. Add the case id to `REQUIRED_CASES` in `scripts/validate-package.py`.
5. Row in the guard table in `SKILL.md`, and the bullet list in `README.md`.

## Adding a script

Route it from `SKILL.md` in the same commit. The validator fails on a script
that no document tells the human to run: a document pointing at a missing file
is loud, but a tool that works and that nobody runs is silent.

## What must never ship

- A real place, name, email address, phone number, or account handle. The
  validator greps for all of them.
- A `SKILL.md` outside the repo root, apart from the copy the Vercel build
  writes into `web/`.
- A network import or a send call in any script. The AST scan is not advisory.
- A `REPLACE_ME` outside `templates/`, which is the one place a human is meant
  to fill something in later.

## Writing style
Use Plain Language in code comments, prompts, documentation, descriptions,
validation messages, and progress reports.

Plain Language governs grammar, never content — never replace a number, a
command, or a named failure with a common word, and where the two conflict the
number wins.
- Lead with the main point.
- Use common words and active voice.
- Keep sentences and paragraphs short.
- Use one term for the same item.
- Use `must` for requirements.
- Use headings, lists, and tables when they help the reader.
- Remove repeated or unnecessary words.
- Limit acronyms and explain technical terms.
- Avoid double negatives.
- Keep exact identifiers, commands, paths, schema fields, quotations, watched phrases, and behavior-bearing examples.
- Keep the full technical meaning.

## Versioning

`SKILL.md` `metadata.version`, the first `- **X.Y.Z**` line in `README.md`, and
`plugin.json` `version` must be the same number. The validator checks all three.
A release tag `vX.Y.Z` must match it too.
