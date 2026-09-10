#!/bin/sh
# Waits, in the FOREGROUND, for today's digest to land on origin/main after
# fetch-digest.yml has been dispatched, then pulls it.
#   exit 0  digests/<today>.md is on origin/main and pulled
#   exit 1  still missing after ~100 s: dispatch the workflow again and re-run this
# Run it with a plain Bash call. Never in the background, never via Monitor or
# ScheduleWakeup: nothing reliably wakes a headless routine (see BRIEFING_INSTRUCTIONS.md §1).
# ponytail: ~100 s so it fits the default 120 s Bash timeout; the caller loops.
set -u
cd "$(dirname "$0")"
DATE=${DIGEST_DATE:-$(TZ=America/New_York date +%F)}
FILE="digests/$DATE.md"
i=0
until git fetch -q origin main && git cat-file -e "origin/main:$FILE" 2>/dev/null; do
  i=$((i + 1))
  if [ "$i" -ge 7 ]; then
    echo "$FILE is not on origin/main yet: dispatch fetch-digest.yml again and re-run this."
    exit 1
  fi
  sleep 15
done
git checkout -q main 2>/dev/null || true
git pull -q --ff-only origin main
echo "$FILE ready: $(grep -c '^- ' "$FILE") items"
