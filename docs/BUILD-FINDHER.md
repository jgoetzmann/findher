# Build brief

Why this repo is shaped the way it is. Nothing here is required reading to use
the skill; it is the argument behind the guards, and every rule in
`scripts/guards.py` points back at a paragraph in it.

## 1. What this is

A truth-maintenance system for a personal plan — a set of guards that stop a
language model writing plausible, well-formed, false statements about a real
person into places those statements reach other people.

`findher` refuses any seed that names a person. The room, the calendar and the
criterion deliver what the user is actually after; pointing the pipeline at a
human being delivers none of it, and the pipeline refuses to be pointed.

The guards are the product. Nothing personal is in this package: no seed, no
appearance notes, no week, no outbound mail. Each of the ten checks is a
regression test for a defect this class of work produces, and §4 names the five
that recur.

## 2. The input that has to exist first

The skill writes public-facing copy about a person. If it has no source
material it will produce plausible sentences, and plausible is exactly the
failure mode. So before any copy is generated, the user runs the likeness
prompt in whatever assistant they have the most history with, saves the output
into the plan repo, and every claim the skill writes cites a line of it.

The prompt is in [LIKENESS-PROMPT.md](LIKENESS-PROMPT.md). It is the step most
likely to be skipped and the one that decides whether this is a working skill or
a fabrication engine.

Two properties of that file drive the design. It is the most sensitive file in
the repo, and the exposure in it is mostly **other people's**: a filled-in
likeness file names friends, family and colleagues, often in full and sometimes
by detail none of them agreed to have written down. So it is gitignored on
arrival, it is never quoted, and the decode cites the seed by line number rather
than reproducing it.

## 3. Two failures the design rules out

1. **Sensitive files documented as ignored while git still tracks them.** A
   rule added after the file exists does not un-track it, so `git ls-files`
   keeps returning it while the history reads clean. Here the gitignore is
   copied **first**, before any file with content in it exists, and every line
   of it carries its reason — `scripts/selftest.py` case A5 fails the build if
   one does not.
2. **An acceptance criterion never run in the state a fresh install is in.**
   `grep -c $'\tdate\t' log.tsv` exits **2** with no log file: neither pass nor
   fail, and every caller checking for 0 or 1 is wrong. Here it is
   `scripts/criterion.sh`, it handles the missing file, and case C3 runs it on
   an empty directory.

## 4. The five things that will go wrong

1. **The model invents a fact about the user and then refines the invention.**
   An ambiguous line in the seed gets read the wrong way, and every later pass
   builds on the reading instead of rechecking it. Competent, good-faith work
   makes the invention more convincing rather than less, and a guard written
   against one symptom of it still passes while the premise stays false.
   → **Nothing a model wrote about the user is evidence.** §2 exists because of
   this.
2. **A negative finding stated confidently is not evidence the premise is
   true.** A thorough search that returns nothing reads as proof the thing
   exists somewhere else, when it is equally evidence the premise was wrong.
   → **Re-ask the premise, not the search.**
3. **A change that never reached the file consuming it.** A fact gets corrected
   where it was discovered, not in the file that routes the human. The last
   surviving stale copy is reliably the one they actually open.
   → The preflight resolves every link in every routing document, and fails on a
   dangling one.
4. **A guard that passes for a reason unrelated to the hazard.** A denylist
   built from ordinary words matches everything and blinds the check. A length
   cap set above the real placeholder never fires. An exemption added to quiet
   a failing case lets the banned input back in.
   → **Verify every guard by injecting the defect and watching it fail.** That
   is the whole of `scripts/selftest.py`. A guard you have never seen fail is a
   guard you are asserting, not testing.
5. **Location and time inferred rather than asked.** A machine clock reports
   where the machine is, not where the user is. Every venue, travel time and
   calendar entry downstream inherits the error, and copy written from it keeps
   the wrong city after the calendar is corrected.
   → `place` and `tz` are required, asked, restated, and never inferred.

## 5. The machinery, and the bug each piece exists for

| Script | The mechanism |
|---|---|
| `guards.py` | Every refusal in one file, each denylist named and checked for emptiness. An empty required list is the defect, not a clean run. |
| `preflight.py` | Ten checks and no `--force`. The orphan check is the subtle one: a document pointing at a missing file is loud, but **a tool that works and that nothing tells the human to run** is silent. |
| `calendar_build.py` | Checks every date against the weekday its own text claims, expands recurrences to find events stacked on one evening, emits an explicit `VTIMEZONE`. The only artifact that acts *at a time*. |
| `profile.py` | Refuses to type any block holding a placeholder, and **parses the spec table** to build its refusal list rather than restating it, so the guard cannot drift from the spec. |
| `interview.py` | Questions live in a file the human fills in at their own pace, keyed by **paired** open and close markers, refusing filler answers. Tested on the last slot, because a test that fills every slot passes and proves nothing. |
| `lint_message.py` | Thirteen rules over an outgoing draft. Every rule prints the document that argued for it, so it can be overruled. It cannot send. |
| `log.py` | Six columns, append-only. No name column, no attribute column, no free-text field. |
| `shotcard.py` | Parses the photo table and **errors rather than printing an empty card** if the columns are renamed. |
| `strip_exif.py` | Strips metadata, because raw camera files carry the GPS of wherever they were taken, including home. |
| `criterion.sh` | Exits 0 or 1, including on day one. |
| `selftest.py` | Injects each defect and records the failure. Twenty-three cases. |

## 6. What "done" is not

- **Not a document.** If the output is one more markdown file explaining the
  plan, the plan was not built.
- **Not a menu.** If it ends on "here are some options", do the thing instead.
- **Not a person.** No tool here returns one. The skill produces the plan, the
  calendar, the copy and the criterion, and then says the rest is theirs —
  rooms entered is about 35% of the outcome and initiating is another 25%, and
  both of those are the user on a Wednesday, walking in.

The criterion is a row in a log file, and not a document, for exactly that
reason.
