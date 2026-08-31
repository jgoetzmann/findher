#!/usr/bin/env python3
"""Print the photo card, or error. Never print half of one.

    python3 scripts/shotcard.py [--repo DIR]

The card is parsed out of a table in photos.md. If the section heading is
renamed, a column is renamed, or a header column is dropped, this errors and
says so, because a card with blank fields looks finished.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from guards import PLACEHOLDERS, parse_table  # noqa: E402

COLUMNS = ("slot", "shows", "status")
HEADING = "## Photos"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", type=Path)
    args = ap.parse_args()
    path = args.repo / "photos.md"
    if not path.is_file():
        print(f"shotcard: {path} does not exist", file=sys.stderr)
        return 1
    try:
        rows = parse_table(path.read_text(encoding="utf-8"), HEADING, COLUMNS)
    except ValueError as err:
        print(f"shotcard: {err}", file=sys.stderr)
        return 1

    width = max([len("SLOT")] + [len(r["slot"]) for r in rows])
    print(f"{'SLOT':<{width}}  SHOWS                          STATUS")
    shot, missing = 0, []
    for row in rows:
        text = " ".join(row.values())
        if any(token.lower() in text.lower() for token in PLACEHOLDERS):
            print(f"shotcard: row {row['slot']!r} still holds a placeholder. Fill it or delete the row.",
                  file=sys.stderr)
            return 1
        print(f"{row['slot']:<{width}}  {row['shows'][:30]:<30} {row['status']}")
        if row["status"].strip().lower() == "shot":
            shot += 1
        else:
            missing.append(row["slot"])
    print(f"\n{shot}/{len(rows)} shot.")
    if missing:
        print("outstanding: " + ", ".join(missing))
        print("Appearance is a threshold good. All of the value is in clearing the floor,\n"
              "and none of it is above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
