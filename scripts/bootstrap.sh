#!/usr/bin/env sh
# Scaffold a plan repo, gitignore first.
#
#   sh scripts/bootstrap.sh PATH
#
# The plan repo is a separate directory with its own git history. Nothing
# personal ever lands inside this package, and the ignore rules are staged
# before any file with content in it exists. A rule added after the file exists
# does not un-track it, so writing content first lets a repo document its
# sensitive files as ignored while `git ls-files` still returns them.
#
# Refuses a destination that already holds files. Overwriting somebody's seed
# is not a recoverable mistake.
set -eu

skill_dir=$(cd "$(dirname "$0")/.." && pwd)
dest="${1:-}"

if [ -z "$dest" ]; then
    echo "usage: sh scripts/bootstrap.sh PATH" >&2
    echo "  PATH is where the plan repo goes. Keep it outside this one." >&2
    exit 1
fi

if [ -e "$dest" ] && [ -n "$(ls -A "$dest" 2>/dev/null)" ]; then
    echo "$dest already holds files. Pick an empty path." >&2
    echo "Nothing here overwrites a seed you already wrote." >&2
    exit 1
fi

case "$(cd "$dest" 2>/dev/null && pwd || echo "$dest")" in
    "$skill_dir"|"$skill_dir"/*)
        echo "$dest is inside the skill repo. The plan repo must be its own directory" >&2
        echo "with its own history, so that none of it can be pushed with the package." >&2
        exit 1 ;;
esac

mkdir -p "$dest"

# 1. The ignore rules, alone, first.
cp "$skill_dir/templates/gitignore" "$dest/.gitignore"
if command -v git >/dev/null 2>&1; then
    git -C "$dest" init -q
    git -C "$dest" add .gitignore
    git -C "$dest" -c user.email=you@example.invalid -c user.name=you \
        commit -qm "ignore rules, before anything with content in it exists" 2>/dev/null || true
fi

# 2. Then the files that will hold content.
for f in planrc.json seed.md plan.md rooms.md profile.md photos.md; do
    cp "$skill_dir/templates/$f" "$dest/$f"
done
mkdir -p "$dest/outreach" "$dest/photos"
cp "$skill_dir/templates/outreach/draft.md" "$dest/outreach/draft.md"

echo "scaffolded $dest"
echo
echo "Tracked so far:"
if command -v git >/dev/null 2>&1; then
    git -C "$dest" ls-files | sed 's/^/  /'
    echo "  (seed.md, log.tsv, likeness-*.md and the photos are ignored, each for a stated reason)"
fi
echo
echo "Next, and none of it is inferred:"
echo "  1. set place and tz in $dest/planrc.json"
echo "  2. write the seed in $dest/seed.md — a type, not a person"
echo "  3. python3 $skill_dir/scripts/preflight.py --repo $dest"
echo
echo "The preflight fails until those are done. That is the point of it."
