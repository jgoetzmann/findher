#!/usr/bin/env python3
"""Type the profile, and refuse to type the parts that are not true yet.

    python3 scripts/profile.py [--repo DIR]

The refusal list is parsed out of the spec table in profile.md rather than
restated here, so the guard cannot drift from the spec. Every block carries a
source. Only blocks sourced to something the user wrote or said are postable;
invented, aspirational and unfillable blocks are printed as blanks with the
question still attached.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from guards import PLACEHOLDERS, PROTECTED_TERMS, parse_table  # noqa: E402

COLUMNS = ("block", "max", "source", "text")
POSTABLE_SOURCES = ("likeness", "interview", "seed-neutral", "observed")
NOT_POSTABLE = ("invented", "aspirational", "unfillable")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", type=Path)
    args = ap.parse_args()
    path = args.repo / "profile.md"
    if not path.is_file():
        print(f"profile: {path} does not exist", file=sys.stderr)
        return 1
    try:
        rows = parse_table(path.read_text(encoding="utf-8"), "## Blocks", COLUMNS)
    except ValueError as err:
        print(f"profile: {err}", file=sys.stderr)
        return 1

    postable, withheld, refused = [], [], []
    for row in rows:
        block, text, source = row["block"], row["text"].strip(), row["source"].strip().lower()
        max_chars = int(row["max"]) if row["max"].strip().isdigit() else 0
        if any(token.lower() in text.lower() for token in PLACEHOLDERS):
            refused.append((block, "holds a placeholder"))
            continue
        if not text:
            withheld.append((block, "blank — the question it answers has not been answered"))
            continue
        if source.split(":")[0] in NOT_POSTABLE or not source:
            withheld.append((block, f"source is {source or 'unset'}, which is not postable"))
            continue
        if source.split(":")[0] not in POSTABLE_SOURCES:
            refused.append((block, f"source {source!r} is not one of: {', '.join(POSTABLE_SOURCES)}"))
            continue
        if max_chars and len(text) > max_chars:
            refused.append((block, f"{len(text)} characters, over the {max_chars} the spec allows"))
            continue
        if hit := [w for w in text.lower().split() if w.strip(".,!?") in PROTECTED_TERMS]:
            refused.append((block, f"names a protected characteristic: {', '.join(hit)}"))
            continue
        postable.append((block, text, row["source"]))

    if refused:
        print(f"profile refused {len(refused)} block(s):", file=sys.stderr)
        for block, reason in refused:
            print(f"  - {block}: {reason}", file=sys.stderr)
        return 1

    print("POSTABLE\n")
    for block, text, source in postable:
        print(f"## {block}   [{source}]\n{text}\n")
    if withheld:
        print("BLANK — do not fill these in from nothing\n")
        for block, reason in withheld:
            print(f"  {block}: {reason}")
        print("\nA blank you cannot fill is a wrong question, not a hard question. Delete the clause.")
    print(f"\nprovenance: {len(postable)} sourced, {len(withheld)} blank, 0 invented")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
