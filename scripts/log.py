#!/usr/bin/env python3
"""The ledger. Six columns, append-only, no room for a person in it.

    python3 scripts/log.py --room "Tuesday climbing" --visit 3 --initiated 2 --minutes 90 --next "same, next week"

There is no name column, no attribute column and no free-text field, because a
log with one becomes a file about somebody who never agreed to be in it. `next`
is validated against a short list of moves, not typed freely.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

COLUMNS = ("date", "room", "visit", "initiated", "minutes", "next")
NEXT_MOVES = ("same, next week", "same, skip a week", "different room", "stop", "follow up")
ROOM_OK = re.compile(r"^[\w ,'&()-]{2,60}$")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", type=Path)
    ap.add_argument("--room", required=True, help="the room, not the person")
    ap.add_argument("--visit", type=int, required=True, help="which visit this was: 1, 2, 3, 4...")
    ap.add_argument("--initiated", type=int, required=True, help="conversations you started, not received")
    ap.add_argument("--minutes", type=int, required=True)
    ap.add_argument("--next", dest="nxt", required=True, choices=NEXT_MOVES)
    ap.add_argument("--date", default=dt.date.today().isoformat())
    args = ap.parse_args()

    if not ROOM_OK.match(args.room):
        print(f"--room {args.room!r} is not a room name. Letters, spaces and punctuation only, "
              f"under 60 characters. If you are about to type a person's name, that is the guard working.",
              file=sys.stderr)
        return 1
    for field in ("visit", "initiated", "minutes"):
        if getattr(args, field) < 0:
            print(f"--{field} must be 0 or more", file=sys.stderr)
            return 1
    try:
        dt.date.fromisoformat(args.date)
    except ValueError:
        print(f"--date {args.date!r} is not an ISO date (YYYY-MM-DD)", file=sys.stderr)
        return 1

    path = args.repo / "log.tsv"
    if not path.exists():
        path.write_text("\t".join(COLUMNS) + "\n", encoding="utf-8")
    row = [args.date, args.room, str(args.visit), str(args.initiated), str(args.minutes), args.nxt]
    with path.open("a", encoding="utf-8") as fh:
        fh.write("\t".join(row) + "\n")
    print("\t".join(row))
    if args.visit >= 4:
        print("\nFourth visit to the same room. That is the number that predicts the outcome.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
