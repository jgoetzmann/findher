#!/usr/bin/env python3
"""Inject every defect and watch every guard fail.

    python3 scripts/selftest.py [-v]

A guard you have never seen fail is a guard you are asserting, not testing.
Every check in this file breaks something on purpose and then asserts the
refusal, and every check that is meant to pass cleanly is run against honest
input as well, because a gate that flags honest input teaches the user to skim
the output — which is the one habit the preflight exists to prevent.

Exit 0 when every case behaves. Exit 1 on the first that does not.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import guards  # noqa: E402

PY = sys.executable
CASES: list[tuple[str, str, object]] = []


def case(cid: str, label: str):
    def wrap(fn):
        CASES.append((cid, label, fn))
        return fn
    return wrap


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

HONEST_SEED = ("someone who reads, goes to the Music Society shows, and would "
               "rather cook than go out. into board games, not competitive about it.")

REFUSING_SEEDS = [
    ("full name + institution", "Jane Doe at Northwestern"),
    ("first name + workplace", "Sarah from the coffee shop on Halsted"),
    ("account handle", "someone like @sarahdoe, that energy"),
    ("profile url", "https://instagram.com/sarahdoe basically"),
    ("deictic", "the one in my Tuesday class"),
    ("name split across lines", "Jane\nDoe at Northwestern"),
    ("all caps", "JANE DOE AT NORTHWESTERN"),
    ("all lowercase", "jane doe at northwestern"),
    ("mixed case", "JaNe DoE at Northwestern"),
    ("comma connector", "Jane Doe, Northwestern"),
    ("phone number", "her number is 555-555-0143"),
    ("email", "jane.doe@example.com"),
]

HONEST_SEEDS = [
    HONEST_SEED,
    "into bouldering and board games; Board Games Club regulars, not competitive about it",
    "a grad student or someone with a real job, over 25, patient, into live music",
    "someone who runs, likes long walks, and reads nonfiction. no phones at dinner",
    "quiet, funny, into film. goes to repertory screenings. bikes everywhere",
    "someone in a choir or a running club, wants kids eventually",
    "kind, curious, plays board games, works in something creative",
]

ORDINARY_DRAFTS = [
    "Good talking at the table tonight. I'm usually there Tuesdays if you fancy another round, no pressure either way.",
    "That was a better session than last week. Same time tomorrow?",
    "Enjoyed the class. I'll be at the wall again Thursday, come say hi if you're around, no worries if not.",
]

RULE_DRAFTS = {
    "appearance": "You looked beautiful at the class tonight.",
    "exit-ramp": "Would you want to get a drink after the class on Thursday?",
    "seed-words": "You seemed like a Music Society sort of person at the class.",
    "length": "Great to meet you at the class. " + ("I talk a lot when I am nervous and this is what that looks like. " * 8),
    "questions": "Good to meet you at the class. How long have you been coming? What got you into it?",
    "platform-hop": "Nice chatting at the class, what's your instagram?",
    "apology-opener": "Sorry to bother you, this is so random, but you were at the class earlier.",
    "pet-name": "hey gorgeous, saw you at the class",
    "negging": "You're not like most people at the class, in a good way.",
    "surveillance-tell": "I saw you at the class on Tuesday and again on Thursday.",
    "presumption": "We should get dinner after the class, you'll love the place round the corner.",
    "emoji": "Good class tonight \U0001F600 \U0001F604 \U0001F60E \U0001F44D",
    "no-room": "Hey, you seem interesting.",
}


def scaffold(dest: Path, *, seed: str = HONEST_SEED, place: str = "Springfield, Riverside",
             tz: str = "America/Chicago", age_cfg: int | None = 21, age_plan: int | None = 21,
             rooms_why: tuple[str, str] = ("regulars stay for the whole session",
                                           "one hour, close enough to walk home from"),
             schedule_weekday: str | None = None, extra_schedule: bool = False,
             routing_drop: str | None = None) -> Path:
    """Write a plan repo. Every argument is a lever a defect-injection pulls."""
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("photos.md", "profile.md"):
        shutil.copy(ROOT / "templates" / name, dest / name)
    shutil.copy(ROOT / "templates" / "gitignore", dest / ".gitignore")
    (dest / "seed.md").write_text(seed + "\n", encoding="utf-8")

    config: dict = {"place": place, "tz": tz, "rooms_max": 2}
    if age_cfg is not None:
        config["age_floor"] = age_cfg
    (dest / "planrc.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    (dest / "rooms.md").write_text(
        "# Two rooms, and why\n\n## Rooms\n\n"
        "| room | kind | when | why | status |\n|---|---|---|---|---|\n"
        f"| Tuesday climbing | density | Tuesdays 19:00 | {rooms_why[0]} | VERIFIED |\n"
        f"| Sunday chorus | survivability | Sundays 10:00 | {rooms_why[1]} | VERIFIED |\n",
        encoding="utf-8")

    date = dt.date(2026, 9, 1)
    weekday = schedule_weekday or date.strftime("%A")
    rows = [f"| Tuesday climbing | {date.isoformat()} | {weekday} | 19:00 | 21:00 | once |"]
    if extra_schedule:
        rows.append(f"| Sunday chorus | {date.isoformat()} | {weekday} | 20:00 | 21:30 | once |")
    plan = ["# The plan", ""]
    if age_plan is not None:
        plan += [f"age_floor: {age_plan}", ""]
    plan += ["## The two rooms", "", "See [rooms.md](rooms.md).", "",
             "## Schedule", "", "| room | date | weekday | start | end | repeats |",
             "|---|---|---|---|---|---|", *rows, "",
             "## What to run", "", "| when | command |", "|---|---|"]
    runners = ["preflight.py", "interview.py", "calendar_build.py", "profile.py",
               "lint_message.py", "strip_exif.py", "shotcard.py", "log.py", "criterion.sh"]
    for script in runners:
        if script == routing_drop:
            continue
        plan.append(f"| step | `scripts/{script}` |")
    (dest / "plan.md").write_text("\n".join(plan) + "\n", encoding="utf-8")
    return dest


def preflight(repo: Path) -> tuple[int, str]:
    out = subprocess.run([PY, str(HERE / "preflight.py"), "--repo", str(repo)],
                         capture_output=True, text=True)
    return out.returncode, out.stdout + out.stderr


# --------------------------------------------------------------------------
# B1 / B2 — the seed guard, both directions
# --------------------------------------------------------------------------

@case("B1", "12 phrasings that name an individual are all refused")
def b1():
    missed = [label for label, seed in REFUSING_SEEDS if not guards.check_seed(seed)]
    return not missed, f"missed: {', '.join(missed)}" if missed else "all 12 refused"


@case("B2", "7 honest seeds are not refused")
def b2():
    wrong = [(s[:40], guards.check_seed(s)[0].rule) for s in HONEST_SEEDS if guards.check_seed(s)]
    return not wrong, "; ".join(f"{s!r} -> {r}" for s, r in wrong) or "0 false positives"


# --------------------------------------------------------------------------
# B3 — the age floor
# --------------------------------------------------------------------------

@case("B3", "age floor absent, under 18, or disagreeing between files")
def b3():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        cases = {
            "absent": scaffold(base / "absent", age_cfg=None, age_plan=None),
            "sixteen": scaffold(base / "sixteen", age_cfg=16, age_plan=16),
            "disagree": scaffold(base / "disagree", age_cfg=21, age_plan=25),
        }
        passing = [name for name, repo in cases.items() if preflight(repo)[0] == 0]
        return not passing, f"passed when it should not: {', '.join(passing)}" if passing else "all 3 refused"


# --------------------------------------------------------------------------
# B4 — protected characteristic as a search axis
# --------------------------------------------------------------------------

@case("B4", "a venue justified by who is demographically there, in 4 shapes")
def b4():
    rows = [
        {"room": "in the why", "kind": "density", "when": "Tue", "why": "lots of asian students go", "status": "VERIFIED"},
        {"room": "moved column", "kind": "density", "when": "Tue", "why": "good crowd", "status": "VERIFIED — jewish crowd"},
        {"room": "padded", "kind": "density", "when": "Tue",
         "why": "the session runs two hours and the regulars stay, and it skews young and attractive", "status": "VERIFIED"},
        {"room": "in the name", "kind": "density", "when": "Tue", "why": "close to home", "status": "VERIFIED"},
    ]
    rows[3]["room"] = "queer night at the bar"
    missed = [r["room"] for r in rows if not guards.check_room_rows([r])]
    return not missed, f"missed: {', '.join(missed)}" if missed else "all 4 refused"


# --------------------------------------------------------------------------
# B5 — no send path, and the scan itself is verified by injection
# --------------------------------------------------------------------------

@case("B5a", "no shipped script has a send path")
def b5a():
    hits = guards.check_no_send_path((ROOT / "scripts").glob("*.py"))
    return not hits, "; ".join(h.detail for h in hits) or "clean across every script"


@case("B5b", "the send-path scan fires when a send path is injected")
def b5b():
    with tempfile.TemporaryDirectory() as tmp:
        bad = Path(tmp) / "sender.py"
        bad.write_text("import smtplib\n\n\ndef go(m):\n    smtplib.SMTP('x').sendmail('a', 'b', m)\n", encoding="utf-8")
        hits = guards.check_no_send_path([bad])
        rules = {h.rule for h in hits}
        return rules >= {"network-import", "network-call"}, f"rules fired: {sorted(rules) or 'none'}"


# --------------------------------------------------------------------------
# B6 — fail closed
# --------------------------------------------------------------------------

@case("B6a", "a deleted config fails and names the unset fields")
def b6a():
    with tempfile.TemporaryDirectory() as tmp:
        repo = scaffold(Path(tmp) / "repo")
        (repo / "planrc.json").unlink()
        code, out = preflight(repo)
        return code == 1 and "planrc.json" in out, f"exit {code}"


@case("B6b", "an emptied denylist fails rather than passing every input")
def b6b():
    saved = guards.DENYLISTS["protected_terms"]
    try:
        guards.DENYLISTS["protected_terms"] = ()
        hits = guards.check_denylists()
    finally:
        guards.DENYLISTS["protected_terms"] = saved
    return bool(hits), hits[0].detail if hits else "an empty denylist passed"


@case("B6c", "a renamed table column fails rather than emptying the table")
def b6c():
    with tempfile.TemporaryDirectory() as tmp:
        repo = scaffold(Path(tmp) / "repo")
        text = (repo / "rooms.md").read_text(encoding="utf-8").replace("| why |", "| reason |")
        (repo / "rooms.md").write_text(text, encoding="utf-8")
        code, out = preflight(repo)
        return code == 1 and "why" in out, f"exit {code}"


@case("B6d", "a routing document pointing at a missing file fails")
def b6d():
    with tempfile.TemporaryDirectory() as tmp:
        repo = scaffold(Path(tmp) / "repo")
        (repo / "plan.md").write_text(
            (repo / "plan.md").read_text(encoding="utf-8") + "\nSee [gone.md](gone.md).\n", encoding="utf-8")
        code, out = preflight(repo)
        return code == 1 and "gone.md" in out, f"exit {code}"


@case("B6e", "no green line is printed while any check fails")
def b6e():
    with tempfile.TemporaryDirectory() as tmp:
        repo = scaffold(Path(tmp) / "repo", seed="Jane Doe at Northwestern")
        code, out = preflight(repo)
        return code == 1 and "preflight ok" not in out, f"exit {code}, output {out[:80]!r}"


# --------------------------------------------------------------------------
# C — it actually works
# --------------------------------------------------------------------------

@case("C1", "a fresh unconfigured scaffold fails and names place and tz")
def c1():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "fresh"
        repo.mkdir()
        for name in ("planrc.json", "seed.md", "plan.md", "rooms.md", "photos.md", "profile.md"):
            shutil.copy(ROOT / "templates" / name, repo / name)
        code, out = preflight(repo)
        return code == 1 and "place" in out and "tz" in out, f"exit {code}"


@case("C2", "a fresh configured scaffold runs clean end to end")
def c2():
    with tempfile.TemporaryDirectory() as tmp:
        repo = scaffold(Path(tmp) / "repo")
        code, out = preflight(repo)
        return code == 0, out.strip().splitlines()[-1] if out.strip() else f"exit {code}"


@case("C3", "the criterion exits 1 on day one, not 2")
def c3():
    with tempfile.TemporaryDirectory() as tmp:
        empty = subprocess.run(["sh", str(HERE / "criterion.sh"), tmp], capture_output=True, text=True)
        subprocess.run([PY, str(HERE / "log.py"), "--repo", tmp, "--room", "Tuesday climbing",
                        "--visit", "1", "--initiated", "2", "--minutes", "90",
                        "--next", "same, next week"], capture_output=True, text=True)
        filled = subprocess.run(["sh", str(HERE / "criterion.sh"), tmp], capture_output=True, text=True)
        ok = empty.returncode == 1 and filled.returncode == 0
        return ok, f"empty exit {empty.returncode} (must be 1), after one row exit {filled.returncode} (must be 0)"


@case("C4", "the calendar refuses a wrong weekday and reports a stacked evening")
def c4():
    with tempfile.TemporaryDirectory() as tmp:
        wrong = scaffold(Path(tmp) / "wrong", schedule_weekday="Friday")
        bad = subprocess.run([PY, str(HERE / "calendar_build.py"), "--repo", str(wrong)],
                             capture_output=True, text=True)
        stacked = scaffold(Path(tmp) / "stacked", extra_schedule=True)
        good = subprocess.run([PY, str(HERE / "calendar_build.py"), "--repo", str(stacked)],
                              capture_output=True, text=True)
        ok = bad.returncode == 1 and "Friday" in bad.stderr and good.returncode == 0 and "stacked on" in good.stdout
        return ok, f"wrong weekday exit {bad.returncode}; stacked reported: {'stacked on' in good.stdout}"


@case("C5", "the calendar emits VTIMEZONE and no naive timestamps")
def c5():
    with tempfile.TemporaryDirectory() as tmp:
        repo = scaffold(Path(tmp) / "repo")
        subprocess.run([PY, str(HERE / "calendar_build.py"), "--repo", str(repo)],
                       capture_output=True, text=True)
        ics = (repo / "calendar.ics").read_text(encoding="utf-8")
        # A VTIMEZONE carries its own floating DTSTART by design, so only the
        # VEVENT block is scanned for naive stamps.
        body = ics.split("END:VTIMEZONE", 1)[-1]
        naive = [l for l in body.splitlines() if l.startswith(("DTSTART:", "DTEND:", "DTSTAMP:"))]
        ok = "BEGIN:VTIMEZONE" in ics and "TZID=" in ics and not naive
        return ok, f"VTIMEZONE {'yes' if 'BEGIN:VTIMEZONE' in ics else 'no'}, naive stamps {len(naive)}"


@case("C6", "the photo card errors on 4 kinds of schema drift")
def c6():
    edits = {
        "renamed index column": ("| slot |", "| n |"),
        "renamed content column": ("| shows |", "| depicts |"),
        "renamed section heading": ("## Photos", "## Pictures"),
        "dropped header column": ("| slot | shows | status |", "| slot | shows |"),
    }
    survived = []
    with tempfile.TemporaryDirectory() as tmp:
        for label, (old, new) in edits.items():
            repo = scaffold(Path(tmp) / label.replace(" ", "_"))
            text = (repo / "photos.md").read_text(encoding="utf-8")
            (repo / "photos.md").write_text(text.replace(old, new, 1), encoding="utf-8")
            run = subprocess.run([PY, str(HERE / "shotcard.py"), "--repo", str(repo)],
                                 capture_output=True, text=True)
            if run.returncode == 0:
                survived.append(label)
    return not survived, f"printed anyway: {', '.join(survived)}" if survived else "all 4 errored"


@case("C7", "the message linter blocks each rule and passes 3 ordinary drafts")
def c7():
    import lint_message
    with tempfile.TemporaryDirectory() as tmp:
        repo = scaffold(Path(tmp) / "repo")
        missed = [rule for rule, draft in RULE_DRAFTS.items()
                  if rule not in {r for r, _ in lint_message.lint(draft, repo)}]
        noisy = [d[:34] for d in ORDINARY_DRAFTS if lint_message.lint(d, repo)]
        detail = []
        if missed:
            detail.append(f"rules that did not fire: {', '.join(missed)}")
        if noisy:
            for d in ORDINARY_DRAFTS:
                hits = lint_message.lint(d, repo)
                if hits:
                    detail.append(f"false positive on {d[:30]!r}: {[h[0] for h in hits]}")
        return not (missed or noisy), "; ".join(detail) or f"{len(RULE_DRAFTS)} rules fired, 0 false positives"


@case("C8", "the interview round-trips on the last slot specifically")
def c8():
    import interview
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        subprocess.run([PY, str(HERE / "interview.py"), "--handoff", "--repo", str(repo)],
                       capture_output=True, text=True)
        key = interview.QUESTIONS[-1][0]
        typed = "the questions all assumed I drive. I do not."
        text = (repo / "interview.md").read_text(encoding="utf-8")
        text = text.replace(interview.OPEN.format(key=key) + "\n\n",
                            interview.OPEN.format(key=key) + "\n" + typed + "\n", 1)
        (repo / "interview.md").write_text(text, encoding="utf-8")
        run = subprocess.run([PY, str(HERE / "interview.py"), "--ingest", "--repo", str(repo)],
                             capture_output=True, text=True)
        got = [l.split("\t", 1)[1] for l in run.stdout.splitlines() if l.startswith(key + "\t")]
        return got == [typed], f"got {got!r} for the last slot"


@case("C9", "the orphan check fires when a script leaves the routing document")
def c9():
    with tempfile.TemporaryDirectory() as tmp:
        repo = scaffold(Path(tmp) / "repo", routing_drop="shotcard.py")
        code, out = preflight(repo)
        # SKILL.md also routes scripts, so the fixture is checked against both.
        fired = "shotcard.py" in out and "unrouted" in out
        clean = preflight(scaffold(Path(tmp) / "whole"))[0] == 0
        return (fired or not clean) and clean, f"fired on removal: {fired}; clean repo passes: {clean}"


@case("C0a", "bootstrap stages the ignore rules before any file with content")
def c0a():
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "plan"
        run = subprocess.run(["sh", str(HERE / "bootstrap.sh"), str(dest)], capture_output=True, text=True)
        if run.returncode != 0:
            return False, f"exit {run.returncode}: {run.stderr.strip()[:120]}"
        tracked = subprocess.run(["git", "-C", str(dest), "ls-files"], capture_output=True, text=True).stdout.split()
        ignored = subprocess.run(["git", "-C", str(dest), "check-ignore", "-q", "seed.md"],
                                 capture_output=True, text=True).returncode == 0
        exists = (dest / "seed.md").is_file() and (dest / "planrc.json").is_file()
        ok = tracked == [".gitignore"] and ignored and exists
        return ok, f"tracked={tracked}, seed ignored={ignored}, templates present={exists}"


@case("C0b", "bootstrap refuses a destination that already holds files")
def c0b():
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "plan"
        dest.mkdir()
        (dest / "seed.md").write_text("something the user already wrote\n", encoding="utf-8")
        run = subprocess.run(["sh", str(HERE / "bootstrap.sh"), str(dest)], capture_output=True, text=True)
        kept = (dest / "seed.md").read_text(encoding="utf-8").startswith("something")
        inside = subprocess.run(["sh", str(HERE / "bootstrap.sh"), str(ROOT / "plan")],
                                capture_output=True, text=True)
        ok = run.returncode == 1 and kept and inside.returncode == 1
        return ok, f"non-empty exit {run.returncode}, seed untouched {kept}, inside-skill exit {inside.returncode}"


@case("A5", "every line of the shipped gitignore carries a reason")
def a5():
    lines = (ROOT / "templates" / "gitignore").read_text(encoding="utf-8").splitlines()
    blocks, current = [], []
    for line in lines:
        if line.startswith("#"):
            current.append(line)
        elif line.strip():
            blocks.append(bool(current))
        else:
            current = []
    return all(blocks) and len(blocks) > 8, f"{sum(blocks)}/{len(blocks)} entries have a stated reason"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    failed = 0
    width = max(len(label) for _, label, _ in CASES)
    for cid, label, fn in CASES:
        try:
            ok, detail = fn()
        except Exception as err:  # noqa: BLE001 — a crashing check is a failing check
            ok, detail = False, f"{type(err).__name__}: {err}"
        mark = "pass" if ok else "FAIL"
        failed += not ok
        line = f"{cid:<4} {label:<{width}}  {mark}"
        if args.verbose or not ok:
            line += f"\n       {detail}"
        print(line)
    print()
    if failed:
        print(f"{failed} of {len(CASES)} cases failed. Nothing ships while one stands.")
        return 1
    print(f"{len(CASES)} of {len(CASES)} cases behaved. Every guard was observed failing on injected input.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
