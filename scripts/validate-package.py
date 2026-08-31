#!/usr/bin/env python3
"""Check the findher package without external dependencies.

Two kinds of check live here. The first kind is packaging: one SKILL.md, one
version, manifests that agree. The second kind is the acceptance criteria that
can be checked by reading files rather than by running them — nothing personal
ships, every script is routed, no script has a send path, and every line of the
shipped gitignore carries a reason. The criteria that need a run live in
`scripts/selftest.py`, which CI runs next.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SELF = Path(__file__).resolve()
sys.path.insert(0, str(SELF.parent))

import guards  # noqa: E402

SKILL_PATH = ROOT / "SKILL.md"
SCRIPTS = ROOT / "scripts"
TEMPLATES = ROOT / "templates"
DEPLOY_SKILL = ROOT / "web" / "SKILL.md"
WALK_SKIP = {".git", ".vercel", "__pycache__", "node_modules"}

STEPS = list(range(1, 10))
MAX_SKILL_LINES = 350
# Scripts the human never runs directly. Everything else must be routed from
# SKILL.md, because a tool nothing tells the human to run is a silent tool.
ROUTING_EXEMPT = {"guards.py", "selftest.py", "validate-package.py"}
# The selftest is the evidence for these. A criterion with no case is a
# criterion nobody ran.
REQUIRED_CASES = ("A5", "C0a", "C0b", "B1", "B2", "B3", "B4", "B5a", "B5b", "B6a", "B6b",
                  "B6c", "B6d", "B6e", "C1", "C2", "C3", "C4", "C5", "C6",
                  "C7", "C8", "C9")

STEP_ROW = re.compile(r"^\|[ \t]*([1-9])[ \t]*\|([^|\n]*)\|([^|\n]*)\|[ \t]*$", re.MULTILINE)
FENCE_LINE = re.compile(r"[ \t]{0,3}(`{3,}|~{3,})")
EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b", re.I)
PHONE = re.compile(r"(?<!\d)(?:\+?\d{1,2}[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?!\d)")
RESERVED_EMAIL = re.compile(r"@(?:[\w-]+\.)*(?:example\.(?:com|org|net)|invalid|test|localhost)$", re.I)
RESERVED_PHONE = re.compile(r"555[ .-]01\d{2}$")
# Real place names that must never reach the package. A worked example gets
# written against a real city more often than not, and the place name is what
# survives into shipped copy. This file is exempt from its own check, which is
# why it can name them.
REAL_PLACES = ("hyde park", "uchicago", "chicago,")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read(path: Path) -> str:
    if not path.is_file():
        raise SystemExit(f"{rel(path)} is missing. Create it before cutting a release.")
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> dict:
    try:
        return json.loads(read(path))
    except json.JSONDecodeError as err:
        raise SystemExit(f"{rel(path)} is not valid JSON ({err}). Fix the syntax.") from err


def require(match: re.Match[str] | None, message: str) -> re.Match[str]:
    if match is None:
        raise SystemExit(message)
    return match


def split_fences(text: str) -> str:
    """Return the prose with fenced blocks blanked, so an example never counts."""
    kept, fence = [], ""
    for line in text.split("\n"):
        hit = FENCE_LINE.match(line)
        if not fence:
            if hit:
                fence = hit.group(1)
            kept.append("" if hit else line)
        elif hit and hit.group(1)[0] == fence[0] and len(hit.group(1)) >= len(fence):
            fence = ""
            kept.append("")
        else:
            kept.append("")
    return "\n".join(kept)


def package_files() -> list[Path]:
    return [p for p in sorted(ROOT.rglob("*"))
            if p.is_file() and not WALK_SKIP.intersection(p.relative_to(ROOT).parts)]


def step_table(text: str, where: str) -> dict[int, str]:
    rows = STEP_ROW.findall(split_fences(text))
    if not rows:
        raise SystemExit(
            f"{where} has no step table. Every row must read `| 1 | what | output |`: three "
            f"cells, the step number, what happens, and what it produces. A fourth cell stops "
            f"the row parsing. A table inside a code fence is an example, so it does not count.")
    seen = [int(n) for n, _, _ in rows]
    if seen != STEPS:
        raise SystemExit(
            f"{where} step table lists steps {seen}. Give it one row per step, {STEPS}, in run "
            f"order: the table is the reader's map of the run.")
    return {int(n): " ".join(out.split()) for n, _, out in rows}


SKILL = read(SKILL_PATH)
README = read(ROOT / "README.md")
AGENTS = read(ROOT / "AGENTS.md")
PLUGIN = load_json(ROOT / ".claude-plugin" / "plugin.json")
MARKETPLACE = load_json(ROOT / ".claude-plugin" / "marketplace.json")

# 1. SKILL.md opens with YAML metadata.
front = require(re.match(r"---\n(.*?)\n---\n", SKILL, re.DOTALL),
                "SKILL.md must open with YAML metadata fenced by `---` lines.").group(1)

# 2. No unsupported frontmatter fields.
unsupported = [f for f in ("compatibility", "allowed-tools") if re.search(rf"^[ \t]*{f}[ \t]*:", front, re.M)]
if unsupported:
    raise SystemExit(f"SKILL.md frontmatter uses unsupported field(s): {', '.join(unsupported)}. "
                     f"Delete them; skill loaders ignore them and some reject the file.")

# 3. One version, in three places.
meta_at = require(re.search(r"^metadata:[ \t]*$", front, re.M),
                  "SKILL.md frontmatter needs a `metadata:` block.").end()
skill_version = require(re.search(r'^[ \t]+version:[ \t]*"?(\d+\.\d+\.\d+)"?', front[meta_at:], re.M),
                        'SKILL.md needs `version: "X.Y.Z"` indented under `metadata:`.').group(1)
readme_version = require(re.search(r"^- \*\*(\d+\.\d+\.\d+)\*\*", split_fences(README), re.M),
                         "README.md has no version history entry shaped `- **X.Y.Z** — what changed.`").group(1)
if len({skill_version, readme_version, PLUGIN.get("version", "")}) > 1:
    raise SystemExit(f"Version disagreement: SKILL.md={skill_version}, README.md={readme_version}, "
                     f"plugin.json={PLUGIN.get('version')}. Set all three to the same number.")

# 4. Exactly one real SKILL.md, at the root.
if SKILL_PATH.is_symlink():
    raise SystemExit("SKILL.md at the repo root is a symlink. Packagers do not follow links.")
extra = sorted(rel(p) for p in ROOT.rglob("SKILL.md")
               if p not in (SKILL_PATH, DEPLOY_SKILL) and not WALK_SKIP.intersection(p.relative_to(ROOT).parts))
if extra:
    raise SystemExit(f"Extra SKILL.md copies: {', '.join(extra)}. Ship exactly one, at the root. "
                     f"Only {rel(DEPLOY_SKILL)}, the generated deploy copy, is exempt.")

# 5. plugin.json points at the root.
if PLUGIN.get("skills") != ["./"]:
    raise SystemExit(f'plugin.json `skills` is {PLUGIN.get("skills")!r}. Set it to ["./"].')

# 6. marketplace.json mirrors plugin.json.
entries = MARKETPLACE.get("plugins") or []
if len(entries) != 1:
    raise SystemExit(f"marketplace.json lists {len(entries)} plugins. It must list exactly one.")
drift = [k for k in ("name", "description", "license", "keywords") if entries[0].get(k) != PLUGIN.get(k)]
if drift:
    raise SystemExit(f"marketplace.json disagrees with plugin.json on: {', '.join(drift)}.")

# 7. SKILL.md stays readable in one sitting.
if (n := len(SKILL.splitlines())) > MAX_SKILL_LINES:
    raise SystemExit(f"SKILL.md is {n} lines, over the {MAX_SKILL_LINES}-line limit. Cut "
                     f"{n - MAX_SKILL_LINES} lines, or move the detail into docs/.")

# 8. One heading per step, in order.
headings = [int(x) for x in re.findall(r"^## Step (\d+) — ", split_fences(SKILL), re.M)]
if headings != STEPS:
    raise SystemExit(f"SKILL.md step headings are {headings}. Write one per step, {STEPS} in order, "
                     f"shaped `## Step N` then an em dash (U+2014) then the title.")

# 9 and 10. The two step tables agree.
skill_steps, readme_steps = step_table(SKILL, "SKILL.md"), step_table(README, "README.md")
if mismatch := [s for s in STEPS if readme_steps[s] != skill_steps[s]]:
    detail = ", ".join(f"step {s}: SKILL.md={skill_steps[s]!r} README.md={readme_steps[s]!r}" for s in mismatch)
    raise SystemExit(f"README.md step table disagrees with SKILL.md on {detail}. These drifted apart "
                     f"once already; copy the SKILL.md values across.")

# 11. Every shipped script is routed from SKILL.md. A tool nothing tells the
#     human to run is silent, which is the subtle half of a dangling link.
for script in sorted(SCRIPTS.glob("*")):
    if not script.is_file() or script.suffix not in (".py", ".sh") or script.name in ROUTING_EXEMPT:
        continue
    if script.name not in SKILL:
        raise SystemExit(f"scripts/{script.name} is named nowhere in SKILL.md. Route it, or delete it. "
                         f"It works, and nobody will ever run it.")

# 12. Every guard document the linter cites exists.
for cited in sorted(set(re.findall(r"docs/[A-Z][\w-]+\.md", read(SCRIPTS / "lint_message.py") + SKILL))):
    if not (ROOT / cited).is_file():
        raise SystemExit(f"{cited} is cited but does not exist. The last surviving stale copy is "
                         f"reliably the one they open.")

# 13. Every acceptance criterion has a registered selftest case.
cases = set(re.findall(r'@case\("([\w]+)"', read(SCRIPTS / "selftest.py")))
if missing := [c for c in REQUIRED_CASES if c not in cases]:
    raise SystemExit(f"scripts/selftest.py registers no case for: {', '.join(missing)}. A guard you "
                     f"have never seen fail is a guard you are asserting, not testing.")

# 14. No denylist has been gutted.
if problems := guards.check_denylists():
    raise SystemExit("\n".join(str(p) for p in problems))

# 15. No script has a send path.
if hits := guards.check_no_send_path(SCRIPTS.glob("*.py")):
    raise SystemExit("\n".join(str(h) for h in hits))

# 16. Every line of the shipped gitignore carries its reason.
lines = read(TEMPLATES / "gitignore").splitlines()
comment, unexplained = [], []
for line in lines:
    if line.startswith("#"):
        comment.append(line)
    elif line.strip():
        if not comment:
            unexplained.append(line.strip())
    else:
        comment = []
if unexplained:
    raise SystemExit(f"templates/gitignore has entries with no stated reason: {', '.join(unexplained)}. "
                     f"A rule nobody can justify is a rule somebody deletes.")

# 17. Nothing personal ships, and REPLACE_ME survives only where a human is
#     meant to replace it.
# Three files are allowed to name the placeholder token: this one, the denylist
# that detects it, and the conventions file that states the rule.
PLACEHOLDER_SKIP = {SELF, SCRIPTS / "guards.py", ROOT / "AGENTS.md"}

for path in package_files():
    if path in PLACEHOLDER_SKIP:
        continue
    try:
        body = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        continue
    where = rel(path)
    if "REPLACE_ME" in body and not where.startswith("templates/"):
        raise SystemExit(f"{where} contains REPLACE_ME. Only templates/ may carry placeholders, "
                         f"because only templates/ is filled in by a human later.")
    # RFC 2606 example domains and the reserved 555-01xx range exist so that
    # test fixtures can hold a well-formed address that reaches nobody.
    for label, pattern, reserved in (("an email address", EMAIL, RESERVED_EMAIL),
                                     ("a phone number", PHONE, RESERVED_PHONE)):
        for hit in pattern.finditer(body):
            if reserved.search(hit.group(0)):
                continue
            raise SystemExit(f"{where} contains {label}: {hit.group(0)!r}. Nothing personal ships. "
                             f"Test fixtures must use an RFC 2606 example domain or a 555-01xx number.")
    for place in REAL_PLACES:
        if place in body.lower():
            raise SystemExit(f"{where} names a real place ({place!r}). Nothing tied to one "
                             f"real location ships. Remove it.")

# 18. Every file the scaffold step copies is present. CI checks out tracked
#     files only, so an over-broad .gitignore fails here rather than shipping a
#     package whose first step cannot run. An unanchored `seed.md` rule matches
#     `templates/seed.md` as well, which is exactly how that happens.
SCAFFOLD = ("gitignore", "planrc.json", "seed.md", "plan.md", "rooms.md", "profile.md", "photos.md")
if absent := [f for f in SCAFFOLD if not (TEMPLATES / f).is_file()]:
    raise SystemExit(f"templates/ is missing {', '.join(absent)}. Step 1 copies these into the plan "
                     f"repo, so a missing one means the skill cannot start. Check .gitignore is not "
                     f"matching them.")

# 19. Every script parses and declares its usage, so `--help` is never a lie.
for script in sorted(SCRIPTS.glob("*.py")):
    tree = ast.parse(read(script), filename=str(script))
    if not ast.get_docstring(tree):
        raise SystemExit(f"scripts/{script.name} has no module docstring. Every script says what it "
                         f"does and what it refuses, at the top, in plain language.")

print(f"findher package v{skill_version} is valid — "
      f"{len(package_files())} files, {len(REQUIRED_CASES)} criteria with a selftest case")
