#!/usr/bin/env bash
# gg-tui.sh - Minimal TUI for searching/picking Game Grumps videos
set -euo pipefail

DB_PATH="${1:-gamegrumps.db}"

if ! command -v fzf >/dev/null 2>&1; then
  echo "fzf is required for the TUI. Install it and retry." >&2
  exit 1
fi

# Query: title|url lines, pipe to fzf, open selection
python3 - <<'PY' "$DB_PATH" | fzf --with-nth=1 --delimiter='|' --prompt="Search: " --height=90% --border --ansi | awk -F'|' '{print $2}' | xargs -r xdg-open >/dev/null 2>&1 || true
import sys
import sqlite3

DB_PATH = sys.argv[1]
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("SELECT title, url FROM videos ORDER BY title ASC")
for title, url in c.fetchall():
    # Print as title|url for easy parsing
    safe_title = (title or "").replace("|", "-")
    print(f"{safe_title}|{url}")
conn.close()
PY
