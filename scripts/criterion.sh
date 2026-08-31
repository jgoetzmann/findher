#!/usr/bin/env sh
# The acceptance criterion. A shell command, not a document.
#
#   sh scripts/criterion.sh [repo]
#
# Exit 0 once the ledger holds at least one dated row. Exit 1 otherwise,
# including on day one when no log file exists — the old version of this used
# `grep -c` and exited 2 on a fresh install, which is neither pass nor fail and
# broke every caller that checked for 0 or 1.
set -u
repo="${1:-.}"
log="$repo/log.tsv"

if [ ! -f "$log" ]; then
    echo "no log yet: $log. Nothing has happened. Go to the room." >&2
    exit 1
fi

rows=$(awk -F'\t' 'NR > 1 && $1 ~ /^[0-9]{4}-[0-9]{2}-[0-9]{2}$/ { n++ } END { print n + 0 }' "$log")

if [ "$rows" -ge 1 ]; then
    echo "$rows dated row(s) in $log"
    exit 0
fi

echo "log exists and holds no dated rows: $log" >&2
exit 1
