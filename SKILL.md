---
name: findher
description: |
  Build a personal plan for meeting someone that cannot write a false statement
  about the user into a public place. Use when the user says "findher", or asks
  for help meeting people, making friends, dating, "putting myself out there",
  finding a scene or a hobby group, writing a dating profile, or planning where
  to actually go. Also use when they want the plan repo scaffolded or cloned.
  Also use when they hand over a list of what they are looking for and want it
  turned into a plan, a calendar, and something to say. The guards are the
  product: the seed must describe a type and not a person, the age floor is 18
  or over, no venue may be justified by who is demographically there, nothing
  sends, and every claim about the user cites something the user wrote. Do not
  use to find, identify, profile, locate, or approach a specific person.
license: MIT
metadata:
  version: "1.0.0"
---

# findher

Build the user a plan for meeting someone, and refuse to write one sentence
about them that they did not say first.

The first guard turns away any seed that names a person. The user gets two
rooms, a calendar, copy they can defend out loud, and a criterion that is a row
in a log file. The rest is them on a Wednesday, walking in.

It is a truth-maintenance system: a set of guards that stop a language model
writing plausible, well-formed, false statements about a real person into the
places those statements reach other people.

Two things carry the weight. **Plausible is the failure mode**: with no source
material a model does not go quiet, it writes competent sentences, and the next
pass elaborates an invented fact instead of catching it. **Two rooms, and
refuse the third**: the metric that predicts the outcome is showing up to the
same thing a fourth time, so being visible in eight places is being invisible
in eight places.

## The run

| # | Step | Output |
|---|---|---|
| 1 | Bootstrap: clone or scaffold | a plan repo, ignore rules staged first |
| 2 | Seed and decode | seed + four-bin decode |
| 3 | Place and time, asked and restated | `planrc.json` |
| 4 | Research the rooms | venue table, every row marked |
| 5 | Pick two rooms | the plan |
| 6 | Likeness, then presentation | profile + provenance |
| 7 | Messages and the linter | outreach queue |
| 8 | The rig | scripts, `.ics` |
| 9 | The criterion and the ledger | ledger, then stop |

Steps 2, 6 and 9 are the ones that make it stop feeling like a toy.

## The guards

These are non-negotiable and they are code, not prose. Prose refusals get
argued past. Each of these is a check that fails the build, and each has been
observed failing on injected input — run `python3 scripts/selftest.py` to watch
it happen.

| Guard | What it does | Why |
|---|---|---|
| **Seed is a type, not a person** | Refuses a seed naming an individual: a name beside an institution, an account handle, a profile link, a phone number, "the one in my Tuesday class". | Everything downstream — venue lookup, organiser calendars, recurrence, travel time — is a location-intelligence pipeline. Pointed at a category it is planning. Pointed at one person it is stalking, and the only difference is text you would otherwise accept as freeform. |
| **Adult age floor** | Required, machine-readable, 18 or over, and it must agree in two files. | The seed is freeform and nothing else constrains it. |
| **No protected characteristic as a search axis** | Every venue row carries a reason that must still hold with any demographic word deleted, so no demographic word may appear in the row. | A recommendation you cannot justify without naming the category is targeting, not taste. The justification language is the tell, because that is the language that leaks into how the user talks about it. |
| **No send path** | The skill drafts. The human sends, types, and walks in. | No autonomous sending, no scraping, no bulk action, no driving an account whose terms forbid scripted access. |
| **Fail closed** | A missing config, an empty required denylist, a renamed table column, a routing document that points at nothing — all failures with a reason. | A preflight that ships with empty lists passes vacuously while printing a green line. That is the defect it exists to catch, sold as a feature. |

Refuse the whole run if the user's goal is a particular person. There is no
version of this that is safe to point at one human being.

## Step 1 — Bootstrap: clone or scaffold

The plan repo is a **separate directory with its own git history**. Nothing
personal ever lands in the skill package.

If the user already has the skill installed, scaffold in place:

    sh scripts/bootstrap.sh ~/plans/thisyear

If they would rather start from the repo, clone it first and scaffold out of
the clone:

    git clone https://github.com/jgoetzmann/findher.git
    sh findher/scripts/bootstrap.sh ~/plans/thisyear

Either way `bootstrap.sh` writes and stages `.gitignore` **before** any file
with content in it exists, then copies the templates, then refuses to run at
all if the destination already holds files or sits inside the skill repo.

Order matters, because a rule added after a file exists does not un-track it.
Write the templates first and the ignore rules second, and the repo can document
its sensitive files as ignored while `git ls-files` still returns them. History
looks clean. The working tree is not.

## Step 2 — Seed and decode

The user writes the seed unpolished, in their own words, into `seed.md`. Do not
tidy it for them; the untidy version is the one that decodes.

Then sort every line into four bins and hand the sorting back:

- **Identity** — taste and subculture. These co-occur, and they have addresses.
  This is the bin that becomes rooms.
- **Logistical** — age, institution, schedule. These name buildings, and two of
  them intersecting implies a population nobody wrote down.
- **Inoperable** — things you cannot observe from outside, or cannot act on
  without ranking people. Name them and set them down.
- **Refused** — protected characteristics. Not filters. Not search axes.

For each line: diagnosis, then what they probably mean, then a one-line
rewrite. See [docs/DECODE.md](docs/DECODE.md) for the pattern worked through.

**Cite the seed by line number. Never quote it.** The decode lives in a tracked
file and the seed does not.

## Step 3 — Place and time, asked and restated

Ask for the city, the neighbourhood, and the IANA timezone. Restate the answer
and wait for confirmation. Write them into `planrc.json`.

Never read either off the system clock. A machine clock reports where the
machine is, not where the user is. Every venue, travel time and calendar entry
downstream inherits the error, and copy written from it keeps the wrong city
after the calendar is corrected.

## Step 4 — Research the rooms

Structured endpoints over search engines. The organiser's own page over any
aggregator. Every fact marked `VERIFIED` or `UNVERIFIED` in `rooms.md`, where
verified means read off the organiser's page this week.

Every row carries a `why`. If the reason needs a demographic word, the row is
refused — and rewriting the reason to hide the word does not help, because the
preflight reads every column.

A negative finding stated confidently is not evidence the premise is true. A
thorough search that returns nothing reads as proof the thing exists somewhere
else, when it is equally evidence the premise was wrong. **Re-ask the premise,
not the search.**

## Step 5 — Pick two rooms

One for density, one for survivability. Survivability is the one that decides
it: the question is not whether the room is full of the right people, it is
whether the user could go a fourth time without it becoming a chore.

If the two axes do not intersect, **report the gap**. Do not invent the room
that would have satisfied both.

Weighting, for arguments about where effort goes: rooms entered ~35%,
initiating ~25%, company kept ~20%, appearance ~15%, follow-up ~5%.

## Step 6 — Likeness, then presentation

**This is the step most likely to be skipped, and it is the one that separates
a working skill from a fabrication engine.**

Before any copy is written, the user runs the likeness prompt in whichever
assistant they have the longest history with, in a new chat, and saves the
output into the plan repo as `likeness-<source>.md`. It is gitignored on
arrival: it is the most sensitive file in the repo and the exposure in it is
mostly other people's. The prompt is in [docs/LIKENESS-PROMPT.md](docs/LIKENESS-PROMPT.md)
— hand it over verbatim.

Then every claim in `profile.md` carries a source, and `scripts/profile.py`
parses the spec table to build its own refusal list, so the guard cannot drift
from the spec. Sort every claim into verified, invented, unfillable,
aspirational. **Only verified is postable.**

If the user will not or cannot run the prompt, the skill does not get to guess.
It writes a blank with the question still next to it. A blank you cannot fill is
a wrong question, not a hard question — delete the clause.

    python3 scripts/profile.py --repo .
    python3 scripts/shotcard.py --repo .

Appearance is a threshold good, not a linear one: all of the value is in
clearing the floor and none of it is above. Every photo recommendation must be
justifiable without naming the group it hopes to appeal to.

## Step 7 — Messages and the linter

Openers per room type, and an outbound queue ordered by whose reply unblocks the
most. Thirteen rules run over every draft, and each rule prints the document
that argued for it so a human who read the argument can overrule it.

    python3 scripts/lint_message.py outreach/draft.md --repo .

It blocks on appearance comments, an ask with no exit ramp, and the user's own
seed words appearing in a draft. It cannot send. Nothing here can.

## Step 8 — The rig

    python3 scripts/interview.py --handoff        # then the user fills it in
    python3 scripts/interview.py --ingest
    python3 scripts/calendar_build.py --repo .
    python3 scripts/strip_exif.py photos/*.jpg --out photos/clean

The calendar checks every date against the weekday its own row claims, expands
recurrences far enough to find events stacked on one evening, and emits an
explicit `VTIMEZONE`. It is the only artifact that acts *at a time*, so a wrong
weekday is not a typo — it is someone standing outside a closed room.

`strip_exif.py` runs before any photograph leaves the machine, because raw
camera files carry the GPS of wherever they were taken, including home.

## Step 9 — The criterion and the ledger

    python3 scripts/log.py --room "Tuesday climbing" --visit 3 --initiated 2 --minutes 90 --next "same, next week"
    sh scripts/criterion.sh .

Six columns, append-only. **No name column, no attribute column, no free-text
field**, because a log with one becomes a file about somebody who never agreed
to be in it.

The criterion is a shell command that exits 0 or 1, including on day one with
no log file. It is a row in a log, not a document, because rooms entered is
about 35% of the outcome and initiating is another 25%, and both of those are
the user on a Wednesday, walking in.

Then stop and say the rest is theirs.

## Before anything is generated

    python3 scripts/preflight.py --repo .

Ten checks. There is no `--force`. If it exits 1, nothing downstream runs.

## What done is not

- **Not a document.** If the output is one more markdown file explaining the
  plan, the plan was not built.
- **Not a menu.** If it ends on "here are some options", do the thing instead.
- **Not a person.** No tool here returns one.
