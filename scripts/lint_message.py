#!/usr/bin/env python3
"""Thirteen rules over an outgoing draft. It cannot send.

    python3 scripts/lint_message.py DRAFT.md [--repo DIR]

Every rule prints the document that argued for it, so it can be overruled by a
human who read the argument. Exit 0 on an ordinary draft, 1 on a block.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from guards import COMMON_WORDS, PROTECTED_TERMS  # noqa: E402

MAX_CHARS = 420
MAX_QUESTIONS = 1
MAX_EMOJI = 2
EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")
EXIT_RAMPS = ("no worries", "no pressure", "if you're free", "if you are free",
              "either way", "no stress", "whenever suits", "if you'd rather not",
              "totally fine if", "up to you")
ASKS = ("would you", "do you want", "want to", "are you free", "can i", "could i",
        "let's", "lets ", "shall we", "coffee sometime", "grab a")

RULES: list[tuple[str, str]] = [
    ("appearance", "docs/METHOD.md — appearance is a threshold good, and saying so out loud moves it back below the threshold"),
    ("exit-ramp", "docs/METHOD.md — an ask with no easy no is a demand, and it reads as one"),
    ("seed-words", "docs/BUILD-FINDHER.md §2 — your seed is a shopping list, and a shopping list read aloud is an audit"),
    ("length", "docs/METHOD.md — the first message is an opening, not a case"),
    ("questions", "docs/METHOD.md — two questions makes the reply a form to fill in"),
    ("platform-hop", "docs/METHOD.md — moving apps before a reply asks for a commitment nothing earned"),
    ("apology-opener", "docs/METHOD.md — an apology in line one asks them to reassure you first"),
    ("pet-name", "docs/METHOD.md — a name you were not given"),
    ("negging", "docs/METHOD.md — a compliment with a hook in it is a hook"),
    ("surveillance-tell", "docs/BUILD-FINDHER.md §4 — telling someone what you observed about them is the tell"),
    ("presumption", "docs/METHOD.md — deciding on their behalf, before they have said one word"),
    ("emoji", "docs/METHOD.md — punctuation standing in for a sentence you did not write"),
    ("no-room", "docs/METHOD.md — a message that names no shared room could have been sent to anybody"),
]


def seed_words(repo: Path) -> set[str]:
    """The distinctive words of the seed. These must never reach a draft."""
    text = (repo / "seed.md").read_text(encoding="utf-8") if (repo / "seed.md").is_file() else ""
    body = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith(("#", ">")))
    return {w.lower() for w in re.findall(r"[A-Za-z][\w'-]{4,}", body) if w.lower() not in COMMON_WORDS}


def lint(draft: str, repo: Path) -> list[tuple[str, str]]:
    low = draft.lower()
    hits: list[tuple[str, str]] = []

    def flag(rule: str, detail: str) -> None:
        hits.append((rule, detail))

    if found := [w for w in re.findall(r"[A-Za-z'-]+", low) if w in PROTECTED_TERMS]:
        flag("appearance", f"comments on appearance or a protected characteristic: {', '.join(sorted(set(found)))}")
    if any(a in low for a in ASKS) and not any(r in low for r in EXIT_RAMPS):
        flag("exit-ramp", "the draft asks for something and gives no easy way to decline")
    if overlap := seed_words(repo) & {w.lower() for w in re.findall(r"[A-Za-z][\w'-]{4,}", draft)}:
        flag("seed-words", f"your own seed vocabulary is in the draft: {', '.join(sorted(overlap))}")
    if len(draft.strip()) > MAX_CHARS:
        flag("length", f"{len(draft.strip())} characters, over {MAX_CHARS}")
    if (q := draft.count("?")) > MAX_QUESTIONS:
        flag("questions", f"{q} questions, over {MAX_QUESTIONS}")
    if re.search(r"\b(snap|snapchat|instagram|insta|whatsapp|number|texting|my phone)\b", low):
        flag("platform-hop", "asks to move platform or hand over a number")
    if re.search(r"^\W*(sorry|apologies|this is (so )?random|hope this isn't weird)", low):
        flag("apology-opener", "opens by apologising for existing")
    if re.search(r"\b(hey|hi|hello)[, ]+(beautiful|gorgeous|sexy|cutie|princess|darling|babe)\b", low):
        flag("pet-name", "uses a name you were not given")
    if re.search(r"\b(most (girls|guys|people)|not like|unlike (most|other)|for someone who)\b", low):
        flag("negging", "compliment with a comparison attached")
    if re.search(r"\b(i saw you|i noticed you|i've seen you|i looked you up|i found your|you were wearing|you always)\b", low):
        flag("surveillance-tell", "reports back something you observed about them")
    if re.search(r"\b(we should|you'll love|you will love|i'll take you|i'm going to take you|you have to)\b", low):
        flag("presumption", "decides for them before they have replied")
    if (e := len(EMOJI.findall(draft))) > MAX_EMOJI:
        flag("emoji", f"{e} emoji, over {MAX_EMOJI}")
    if not re.search(r"\b(here|tonight|tomorrow|last week|the (class|club|night|group|session|gig|run|table|wall|shop))\b", low):
        flag("no-room", "names no shared room, so it could have been sent to anybody")
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("draft", type=Path)
    ap.add_argument("--repo", default=".", type=Path)
    args = ap.parse_args()
    if not args.draft.is_file():
        print(f"lint: {args.draft} does not exist", file=sys.stderr)
        return 1

    reasons = dict(RULES)
    hits = lint(args.draft.read_text(encoding="utf-8"), args.repo)
    if not hits:
        print(f"{args.draft}: clean against {len(RULES)} rules. Nothing here sends it. That part is yours.")
        return 0
    print(f"{args.draft}: {len(hits)} block(s)\n", file=sys.stderr)
    for rule, detail in hits:
        print(f"  {rule}: {detail}\n    argued in: {reasons[rule]}\n", file=sys.stderr)
    print("Overrule any of these if you read the argument and disagree. Edit the draft "
          "and run it again.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
