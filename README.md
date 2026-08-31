# findher

[![skills.sh installs](https://skills.sh/b/jgoetzmann/findher)](https://skills.sh/jgoetzmann/findher)

findher builds you a plan for meeting someone, and refuses to write one sentence
about you that you did not say first.

The first guard turns away any seed that names a person. You get two rooms, a
calendar, copy you can defend out loud, and a criterion that is a row in a log
file. The rest is you on a Wednesday, walking in.

Markdown and stdlib Python, so it works with any agent that supports skills and
the scripts run on a fresh machine with nothing installed.

## Quick start

Clone it and scaffold a plan repo beside it:

```
git clone https://github.com/jgoetzmann/findher.git
sh findher/scripts/bootstrap.sh ~/plans/thisyear
```

`bootstrap.sh` stages `.gitignore` before it writes any file with content in it,
refuses a destination that already holds files, and refuses to scaffold inside
the skill repo. Then set `place` and `tz`, write the seed, and run the
preflight — it fails until both are done, which is the point of it.

```
python3 findher/scripts/preflight.py --repo ~/plans/thisyear
```

Or install it as a skill and say `/findher`, and the nine steps run as a
conversation instead.

## Why it exists

Ask a model to help you meet people and it does not go quiet when it has
nothing to go on. It writes confident, well-formed sentences about you, and the
next pass elaborates an invented detail instead of catching it.

So nothing a model wrote about you counts as evidence here. Every claim about
you cites a line you wrote, and every guard is a check that fails the build
rather than a paragraph asking nicely.

## How it works

Two ideas carry the weight.

**Plausible is the failure mode.** Before any copy is generated you run one
prompt in whichever assistant you have the longest history with, and every
sentence the skill writes about you cites a line of the output. If you will not
run it, the skill writes a blank with the question still attached rather than
guessing. A blank you cannot fill is a wrong question, not a hard question.

**Two rooms, and refuse the third.** The metric that predicts the outcome is
showing up to the same thing a fourth time, so being visible in eight places is
being invisible in eight places. One room picked for density, one for
survivability, and the second one decides it.

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

## The guards

Five, all of them code:

- **The seed is a type, not a person.** A name beside an institution, an account
  handle, a profile link, a phone number, "the one in my Tuesday class" — all
  refused, in twelve phrasings including ALL CAPS, all lowercase, and a name
  split across two lines. Everything downstream is a location-intelligence
  pipeline. Pointed at a category it is planning; pointed at one person it is
  stalking.
- **Adult age floor.** Required, machine-readable, 18 or over, agreeing in two
  files.
- **No protected characteristic as a search axis.** A venue whose justification
  needs a demographic word is refused, and moving the word to another column or
  padding it with a real clause does not help.
- **No send path.** An AST scan over every script. The skill drafts; you send.
- **Fail closed.** A missing config, an empty denylist, a renamed column, a
  routing document pointing at nothing — all failures with a reason, and none of
  them prints a green line.

Every one of them has been observed failing on injected input:

```
python3 scripts/selftest.py
```

Twenty-three cases. Each breaks something on purpose and asserts the refusal, and
the honest-input cases assert zero false positives — because a gate that flags
honest input teaches you to skim the output, which is the one habit the
preflight exists to prevent.

## Usage

Call the skill directly:

```
/findher

I want to actually meet people this year. I'm in a new city and I've been
saying that for eight months.
```

Or ask in plain language. It triggers on "help me meet people", "put myself out
there", "find a scene", "write my dating profile", and "where should I actually
go".

It refuses one thing outright: a specific person. There is no version of this
that is safe to point at one human being.

### Running the machinery on its own

```
python3 scripts/preflight.py --repo .     # ten checks, no --force
python3 scripts/interview.py --handoff    # then fill it in, then --ingest
python3 scripts/calendar_build.py --repo .
python3 scripts/lint_message.py outreach/draft.md --repo .
sh scripts/criterion.sh .                 # exits 0 or 1, including on day one
```

## When not to use it

- To find, identify, locate, profile, or approach a particular person. The seed
  guard refuses it and so should you.
- As a replacement for going. Rooms entered is about 35% of the outcome and
  initiating is another 25%. Both of those are you on a Wednesday, walking in.
- For a ninth rewrite of the profile. Appearance and copy are threshold goods:
  below the floor nothing helps, above it nothing helps.

## What's in here

```
SKILL.md                      the skill itself
README.md                     this file
AGENTS.md                     repo conventions for agents working on findher
LICENSE                       MIT
.gitignore                    web/SKILL.md, local scratch
.gitattributes                LF in the repo, so greps and byte compares match
scripts/
  bootstrap.sh                scaffolds a plan repo, ignore rules staged first
  guards.py                   every refusal, one file, each denylist named
  preflight.py                ten checks, fails closed, no --force
  selftest.py                 injects each defect, asserts each refusal
  interview.py                paired-marker questions the human fills in
  profile.py                  refuses to type a block that is not sourced
  calendar_build.py           weekday check, stacking report, explicit VTIMEZONE
  lint_message.py             thirteen rules over a draft, and it cannot send
  shotcard.py                 errors rather than printing half a photo card
  strip_exif.py               metadata off, before anything leaves the machine
  log.py                      six columns, append-only, no name column
  criterion.sh                the acceptance criterion, as a shell command
  validate-package.py         package validator CI runs on every push
templates/
  gitignore                   copied first; every line carries its reason
  planrc.json                 place and tz, asked and restated
  seed.md  plan.md  rooms.md  profile.md  photos.md
  outreach/draft.md           the draft the linter reads, and cannot send
docs/
  BUILD-FINDHER.md            design rationale and the five known failures
  LIKENESS-PROMPT.md          the prompt the user runs before any copy exists
  DECODE.md                   the four bins and the surgery pattern
  METHOD.md                   two rooms, ten rules, the weighting
.claude-plugin/
  plugin.json                 plugin manifest, points the skill loader at ./
  marketplace.json            lets users add this repo as a Claude marketplace
.github/
  workflows/validate.yml      validator, selftest, skill discovery, plugin check
  workflows/release.yml       tagged release, ZIP, notes cut from this file
  workflows/link-check.yml    links in the Markdown
  dependabot.yml              weekly action bumps, grouped into one pull request
web/index.html                landing page
vercel.json                   deploy config for the landing page
```

## Version history

- **1.0.0** — First release. Nine steps, five guards, twenty-three selftest
  cases, and a bootstrap that scaffolds a plan repo outside this one. The ignore
  rules are staged before any file with content exists, and the acceptance
  criterion exits 1 rather than 2 on a fresh install.

## License

MIT

## Installation

With the Skills CLI:

```
npx skills add jgoetzmann/findher --global
```

Leave off `--global` to install into the current project only. Add
`--agent <name>` or `--agent '*'` to choose which agents receive it, then reload
their skills.

Claude Code 2.1.142 or newer can install it as a plugin:

```
/plugin marketplace add jgoetzmann/findher
/plugin install findher@findher
```

The plugin command is `/findher:findher`.

In Claude Desktop, download this repository as a ZIP and upload it as a skill.
For a manual install, copy `SKILL.md`, `scripts/`, `templates/` and `docs/` into
the agent's skill folder. The scripts are not optional — they are the guards,
and without them every rule in `SKILL.md` is a paragraph asking nicely.
