#!/usr/bin/env python3
"""Build the calendar, and refuse to build a wrong one.

    python3 scripts/calendar_build.py [--repo DIR] [--out calendar.ics]

This is the only artifact that acts at a time. A wrong weekday is not a typo,
it is someone standing outside a closed room, so every date is checked against
the weekday its own text claims. Recurrences are expanded far enough to find
events stacked on one evening. The output carries an explicit VTIMEZONE and no
naive local timestamps.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from guards import load_config, parse_table  # noqa: E402

COLUMNS = ("room", "date", "weekday", "start", "end", "repeats")
WEEKS_AHEAD = 6


def _stamp(moment: dt.datetime, tz: str) -> str:
    return f";TZID={tz}:{moment.strftime('%Y%m%dT%H%M%S')}"


def vtimezone(tz: str, year: int) -> list[str]:
    """Emit an explicit VTIMEZONE. A floating timestamp is a wrong timestamp."""
    zone = ZoneInfo(tz)
    winter = dt.datetime(year, 1, 15, 12, tzinfo=zone)
    summer = dt.datetime(year, 7, 15, 12, tzinfo=zone)

    def offset(moment: dt.datetime) -> str:
        delta = moment.utcoffset() or dt.timedelta(0)
        total = int(delta.total_seconds())
        sign = "-" if total < 0 else "+"
        total = abs(total)
        return f"{sign}{total // 3600:02d}{(total % 3600) // 60:02d}"

    std_off, dst_off = offset(winter), offset(summer)
    lines = ["BEGIN:VTIMEZONE", f"TZID:{tz}",
             "BEGIN:STANDARD", f"DTSTART:{year}0101T000000",
             f"TZOFFSETFROM:{dst_off}", f"TZOFFSETTO:{std_off}",
             f"TZNAME:{winter.tzname()}", "END:STANDARD"]
    if std_off != dst_off:
        lines += ["BEGIN:DAYLIGHT", f"DTSTART:{year}0701T000000",
                  f"TZOFFSETFROM:{std_off}", f"TZOFFSETTO:{dst_off}",
                  f"TZNAME:{summer.tzname()}", "END:DAYLIGHT"]
    return lines + ["END:VTIMEZONE"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", type=Path)
    ap.add_argument("--out", default="calendar.ics")
    args = ap.parse_args()
    repo = args.repo

    try:
        config = load_config(repo / "planrc.json")
        rows = parse_table((repo / "plan.md").read_text(encoding="utf-8"), "## Schedule", COLUMNS)
    except (ValueError, OSError) as err:
        print(f"calendar: {err}", file=sys.stderr)
        return 1

    tz = config["tz"]
    try:
        zone = ZoneInfo(tz)
    except Exception as err:  # noqa: BLE001 — an unknown zone must stop the run
        print(f"calendar: planrc.json `tz` is {tz!r}, which is not an IANA timezone ({err})", file=sys.stderr)
        return 1

    problems, events = [], []
    for row in rows:
        try:
            date = dt.date.fromisoformat(row["date"])
            start_h, start_m = (int(x) for x in row["start"].split(":"))
            end_h, end_m = (int(x) for x in row["end"].split(":"))
        except ValueError as err:
            problems.append(f"{row['room']}: unreadable date or time ({err})")
            continue
        claimed = row["weekday"].strip().lower()[:3]
        actual = date.strftime("%a").lower()
        if claimed != actual:
            problems.append(
                f"{row['room']}: the row says {row['weekday']}, but {row['date']} is a "
                f"{date.strftime('%A')}. One of the two is wrong, and the wrong one sends "
                f"somebody to a closed room.")
            continue
        repeats = row["repeats"].strip().lower()
        count = WEEKS_AHEAD if repeats in ("weekly", "every week") else 1
        step = dt.timedelta(days=7)
        for n in range(count):
            day = date + step * n
            events.append((row["room"],
                           dt.datetime.combine(day, dt.time(start_h, start_m), zone),
                           dt.datetime.combine(day, dt.time(end_h, end_m), zone)))

    if problems:
        print("calendar refused:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    stacked = defaultdict(list)
    for room, start, _ in events:
        stacked[start.date()].append((room, start.strftime("%H:%M")))
    clashes = {day: items for day, items in stacked.items() if len(items) > 1}

    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//findher//EN", "CALSCALE:GREGORIAN"]
    lines += vtimezone(tz, min(e[1] for e in events).year)
    for n, (room, start, end) in enumerate(sorted(events, key=lambda e: e[1]), 1):
        lines += ["BEGIN:VEVENT",
                  f"UID:findher-{n}-{start:%Y%m%d}@localhost",
                  f"DTSTAMP{_stamp(start, tz)}",
                  f"DTSTART{_stamp(start, tz)}",
                  f"DTEND{_stamp(end, tz)}",
                  f"SUMMARY:{room}",
                  f"LOCATION:{config['place']}",
                  "END:VEVENT"]
    lines.append("END:VCALENDAR")
    out = repo / args.out
    out.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")

    print(f"wrote {out} — {len(events)} events, timezone {tz}")
    for day, items in sorted(clashes.items()):
        listed = ", ".join(f"{room} at {when}" for room, when in sorted(items, key=lambda i: i[1]))
        print(f"stacked on {day:%A %d %B}: {listed}. You will go to one of these.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
