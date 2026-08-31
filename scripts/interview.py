#!/usr/bin/env python3
"""The interview, as a file the human fills in at their own pace.

    python3 scripts/interview.py --handoff [--repo DIR]   write the questions
    python3 scripts/interview.py --ingest  [--repo DIR]   read the answers back

Answers live between paired open and close markers, so a slot the user left
blank is distinguishable from a slot they filled with a blank line, and the
last slot in the file round-trips like every other one. A test that fills every
slot passes and proves nothing; the last slot is the one that breaks.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from guards import FILLER_ANSWERS  # noqa: E402

FILE = "interview.md"

QUESTIONS: list[tuple[str, str]] = [
    ("place", "What city and neighbourhood are you actually in on a normal Wednesday? Name it, do not let a script read it off the clock."),
    ("tz", "What timezone are you in? Write the IANA name, like America/Chicago."),
    ("age_floor", "What is the lowest age you would consider? It must be 18 or over and it goes in two files."),
    ("rooms_known", "Name every recurring thing you already show up to, however small. Include the ones you stopped going to."),
    ("rooms_possible", "Name three things that run weekly near you that you have never been to."),
    ("survivable", "Of those, which one could you attend four times without it becoming a chore? That is the answer that matters."),
    ("evenings", "Which evenings are actually free, allowing for the commute home first?"),
    ("likeness", "Paste the path to your likeness file, or write NONE. If NONE, every claim about you stays blank."),
    ("photos", "How many photographs of you exist that were taken this year by another person?"),
    ("dealbreaker", "What is the one thing you would end a good date over? One line, in your words."),
    ("last", "Anything the questions above got wrong about you. This is the slot that gets skipped, so answer it."),
]

OPEN = "<!-- answer:{key} -->"
CLOSE = "<!-- /answer:{key} -->"


def handoff(repo: Path) -> int:
    path = repo / FILE
    if path.exists():
        print(f"{path} already exists. Delete it to start over, or run --ingest.", file=sys.stderr)
        return 1
    out = ["# Interview", "",
           "Type between the markers. Leave a slot blank and it stays blank in the output —",
           "a blank you cannot fill is a wrong question, not a hard question.", ""]
    for n, (key, question) in enumerate(QUESTIONS, 1):
        out += [f"## {n}. {question}", "", OPEN.format(key=key), "", CLOSE.format(key=key), ""]
    path.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {path} — {len(QUESTIONS)} questions. Fill it in, then run --ingest.")
    return 0


def ingest(repo: Path) -> int:
    path = repo / FILE
    if not path.is_file():
        print(f"{path} does not exist. Run --handoff first.", file=sys.stderr)
        return 1
    text = path.read_text(encoding="utf-8")
    answers, blank, filler = {}, [], []
    for key, _ in QUESTIONS:
        pattern = re.compile(re.escape(OPEN.format(key=key)) + r"(.*?)" + re.escape(CLOSE.format(key=key)), re.S)
        match = pattern.search(text)
        if match is None:
            print(f"{FILE}: slot {key!r} has no matching open and close markers. "
                  f"Both must be present and in that order.", file=sys.stderr)
            return 1
        value = match.group(1).strip()
        if not value:
            blank.append(key)
        elif value.lower().strip(".!") in FILLER_ANSWERS:
            filler.append(key)
        else:
            answers[key] = value
    for key, value in answers.items():
        print(f"{key}\t{value}")
    if filler:
        print(f"\nrefused as filler: {', '.join(filler)}. Answer them or delete the question.", file=sys.stderr)
    if blank:
        print(f"blank: {', '.join(blank)}. Every claim these would have supported stays blank.", file=sys.stderr)
    return 1 if filler else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--handoff", action="store_true")
    mode.add_argument("--ingest", action="store_true")
    ap.add_argument("--repo", default=".", type=Path)
    args = ap.parse_args()
    return handoff(args.repo) if args.handoff else ingest(args.repo)


if __name__ == "__main__":
    raise SystemExit(main())
