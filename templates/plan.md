# The plan

age_floor: 18

## The two rooms

One picked for density, one picked for survivability. If the two axes do not
intersect, this section says so and stays at one room. It does not invent the
room that would have satisfied both.

See [rooms.md](rooms.md) for the table and the verification status of every fact
in it.

## Schedule

Dates are checked against the weekday each row claims. A wrong weekday is not a
typo, it is standing outside a closed room.

| room | date | weekday | start | end | repeats |
|---|---|---|---|---|---|
| REPLACE_ME | 2026-09-01 | Tuesday | 19:00 | 21:00 | weekly |

## The criterion

    sh scripts/criterion.sh .

Exit 0 once the ledger holds one dated row. Not a document. A row.

## What to run, and when

| when | command |
|---|---|
| before anything is generated | `python3 scripts/preflight.py --repo .` |
| once, to collect your own answers | `python3 scripts/interview.py --handoff` then `--ingest` |
| after the rooms table changes | `python3 scripts/calendar_build.py --repo .` |
| before you post any copy | `python3 scripts/profile.py --repo .` |
| before you send any message | `python3 scripts/lint_message.py outreach/draft.md` |
| before you upload any photo | `python3 scripts/strip_exif.py photos/*.jpg --out photos/clean` |
| to see what is still missing | `python3 scripts/shotcard.py --repo .` |
| after every visit | `python3 scripts/log.py --room "..." --visit N --initiated N --minutes N --next "same, next week"` |
| to check whether you are done | `sh scripts/criterion.sh .` |
