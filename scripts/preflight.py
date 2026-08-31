#!/usr/bin/env python3
"""Run every guard over a plan repo. Exit 0 only when all of them pass.

Usage:
    python3 scripts/preflight.py [--repo DIR] [--list]

There is no `--force`, and there is no path through this file that prints a
green line without having read the files it claims to have checked. A missing
config, an empty denylist, a renamed column and a routing document that points
at nothing are all failures with a reason.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import guards  # noqa: E402
from guards import Finding  # noqa: E402

SKILL_ROOT = Path(__file__).resolve().parent.parent

# Documents that route the human. Every script must be named in one of them.
ROUTING_DOCS = ("plan.md",)
# Scripts the human never runs directly are exempt from the orphan check.
ORPHAN_EXEMPT = {"guards.py", "preflight.py", "selftest.py", "validate-package.py",
                 # Runs before the plan repo exists, so plan.md cannot route it.
                 # SKILL.md does, and validate-package.py checks that it does.
                 "bootstrap.sh"}

CHECKS: list[str] = [
    "denylists", "config", "seed", "age", "rooms", "two-rooms",
    "send", "photos", "routing", "orphans",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def run(repo: Path) -> list[Finding]:
    findings: list[Finding] = []

    # 1. Fail closed before anything else: the guards themselves must be armed.
    findings += guards.check_denylists()

    # 2. Config. Place and time are asked and restated, never inferred.
    config: dict = {}
    try:
        config = guards.load_config(repo / "planrc.json")
    except ValueError as err:
        findings.append(Finding("config", "unusable", str(err),
                                "Every dated artifact downstream is wrong if these two are wrong."))

    # 3. Seed.
    seed_path = repo / "seed.md"
    seed = _read(seed_path)
    body = "\n".join(l for l in seed.splitlines() if not l.lstrip().startswith(("#", ">")))
    if not body.strip():
        findings.append(Finding("seed", "empty", "seed.md is empty or holds only its instructions",
                                "With no source material the model writes plausible sentences, "
                                "and plausible is the failure mode."))
    else:
        findings += guards.check_seed(body)

    # 4. Age floor, in two files, agreeing.
    findings += guards.check_age_floor(config, _read(repo / "plan.md"))

    # 5. Rooms. Schema first, then the justification of each row.
    rooms_text = _read(repo / "rooms.md")
    rows: list[dict] = []
    try:
        rows = guards.parse_table(rooms_text, "## Rooms", ("room", "kind", "when", "why", "status"))
    except ValueError as err:
        findings.append(Finding("rooms", "schema", f"rooms.md: {err}",
                                "A renamed column empties the table quietly, and an empty table "
                                "passes every row check."))
    else:
        findings += guards.check_room_rows(rows)
        unverified = [r["room"] for r in rows if r["status"].strip().upper() not in ("VERIFIED", "UNVERIFIED")]
        if unverified:
            findings.append(Finding("rooms", "unmarked",
                                    f"rows with no VERIFIED/UNVERIFIED mark: {', '.join(unverified)}",
                                    "An unmarked fact reads as checked. Half of them have already changed."))

    # 6. Two rooms. One for density, one for survivability.
    if rows:
        picked = [r for r in rows if r.get("kind", "").strip().lower() in ("density", "survivability")]
        kinds = {r["kind"].strip().lower() for r in picked}
        if kinds != {"density", "survivability"}:
            findings.append(Finding("two-rooms", "not-two",
                                    f"kinds picked: {sorted(kinds) or 'none'}; need exactly density and survivability",
                                    "Being visible in eight places is being invisible in eight places. "
                                    "The metric is the fourth visit to the same room."))
        if len(picked) > 2:
            findings.append(Finding("two-rooms", "too-many",
                                    f"{len(picked)} rooms picked, not 2",
                                    "Refuse the third and the fourth."))

    # 7. No send path, anywhere in the shipped scripts.
    findings += guards.check_no_send_path(SKILL_ROOT.joinpath("scripts").glob("*.py"))

    # 8. Photos table, if there is one. Schema drift errors rather than
    #    printing a card with blank fields.
    photos_text = _read(repo / "photos.md")
    if photos_text.strip():
        try:
            guards.parse_table(photos_text, "## Photos", ("slot", "shows", "status"))
        except ValueError as err:
            findings.append(Finding("photos", "schema", f"photos.md: {err}",
                                    "A partial card looks finished."))

    # 9. Routing documents exist, and every link in them resolves.
    routing_text = ""
    for name in ROUTING_DOCS:
        path = repo / name
        if not path.is_file():
            findings.append(Finding("routing", "missing", f"{name} does not exist",
                                    "The last surviving stale copy is reliably the one they open."))
            continue
        routing_text += _read(path)
        for target in _links(_read(path)):
            if not (repo / target).exists() and not (SKILL_ROOT / target).exists():
                findings.append(Finding("routing", "dangling", f"{name} points at {target}, which does not exist",
                                        "A document pointing at a missing file is loud. Fix it while it still is."))

    # 10. Orphaned tools. A tool that works and that nothing tells the human to
    #     run is silent, which is the subtle half of the same bug.
    for script in sorted(SKILL_ROOT.joinpath("scripts").glob("*")):
        if not script.is_file() or script.suffix not in (".py", ".sh"):
            continue
        if script.name in ORPHAN_EXEMPT or script.name.startswith("."):
            continue
        if script.name not in routing_text:
            findings.append(Finding("orphans", "unrouted", f"scripts/{script.name} is named in no routing document",
                                    "It works, and nobody will ever run it."))
    return findings


def _links(text: str) -> list[str]:
    import re
    out = []
    for target in re.findall(r"\]\(([^)]+)\)", text) + re.findall(r"`(scripts/[\w./-]+)`", text):
        target = target.split("#")[0].strip()
        if target and not target.startswith(("http", "mailto:")):
            out.append(target)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", type=Path, help="the plan repo to check (default: .)")
    ap.add_argument("--list", action="store_true", help="list the checks and exit")
    args = ap.parse_args()

    if args.list:
        print("\n".join(CHECKS))
        return 0

    repo = args.repo.resolve()
    if not repo.is_dir():
        print(f"preflight: {repo} is not a directory", file=sys.stderr)
        return 1

    findings = run(repo)
    if findings:
        print(f"preflight FAILED — {len(findings)} problem(s) in {repo}\n", file=sys.stderr)
        for n, f in enumerate(findings, 1):
            print(f"{n:2}. {f}\n", file=sys.stderr)
        print("Nothing is generated while any of these stand.", file=sys.stderr)
        return 1

    print(f"preflight ok — {len(CHECKS)} checks passed on {repo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
