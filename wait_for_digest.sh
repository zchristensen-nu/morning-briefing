#!/bin/sh
# Waits, in the FOREGROUND, for today's digest to land on origin/main after
# fetch-digest.yml has been dispatched, then pulls it.
#   exit 0  digests/<today>.md is on origin/main and pulled
#   exit 1  still missing after ~100 s and no fetch in flight: dispatch the workflow again and re-run this
#   exit 2  still missing, but a fetch run is queued or running: re-run this WITHOUT dispatching
# Run it with a plain Bash call. Never in the background, never via Monitor or
# ScheduleWakeup: nothing reliably wakes a headless routine (see BRIEFING_INSTRUCTIONS.md §1).
# ponytail: ~100 s so it fits the default 120 s Bash timeout; the caller loops.
set -u
cd "$(dirname "$0")"
DATE=${DIGEST_DATE:-$(TZ=America/New_York date +%F)}
# DIGEST_NAME waits for a sweep digest instead, e.g. DIGEST_NAME=2026-10-09-sweep-11
FILE="digests/${DIGEST_NAME:-$DATE}.md"
i=0
until git fetch -q origin main && git cat-file -e "origin/main:$FILE" 2>/dev/null; do
  i=$((i + 1))
  if [ "$i" -ge 7 ]; then
    # A dispatched run can sit queued for minutes; dispatching again only races it (2026-10-26).
    if command -v gh >/dev/null && [ "$(gh api 'repos/zchristensen-nu/morning-briefing/actions/workflows/fetch-digest.yml/runs?per_page=10' \
         --jq '[.workflow_runs[] | select(.status != "completed")] | length' 2>/dev/null)" -gt 0 ] 2>/dev/null; then
      echo "$FILE is not on origin/main yet, but a fetch is queued or running: re-run this without dispatching."
      exit 2
    fi
    echo "$FILE is not on origin/main yet: dispatch fetch-digest.yml again and re-run this."
    exit 1
  fi
  sleep 15
done
git checkout -q main 2>/dev/null || true
git pull -q --ff-only origin main
echo "$FILE ready: $(grep -c '^- ' "$FILE") items"
