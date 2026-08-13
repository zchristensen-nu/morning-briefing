#!/bin/sh
# Render a briefing markdown file to house-format HTML and create an Outlook draft.
# Usage: sh draft_email.sh briefings/YYYY-MM-DD.md
# The draft has NO recipients — the team reviews, sets From to media@northeastern.edu,
# adds the bcc list, and sends.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
MD="$1"
SUBJECT="$(head -1 "$MD" | sed 's/\*//g')"
HTML="$(python3 "$DIR/render_email.py" "$MD")"
osascript -e '
on run argv
  tell application "Microsoft Outlook"
    set d to make new outgoing message with properties {subject:(item 1 of argv), content:(item 2 of argv)}
    return "Outlook draft created: " & (item 1 of argv)
  end tell
end run' "$SUBJECT" "$HTML"
