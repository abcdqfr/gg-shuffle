#!/usr/bin/env bash
# gg-random.sh - Pick random Game Grumps videos from the database
set -euo pipefail

DB_PATH="gamegrumps.db"
COUNT=1
OPEN_MODE="browser"   # browser|freetube|none

usage() {
  echo "Usage: $0 [-n NUM] [--freetube|--browser|--print] [DB_PATH]"
  echo "  -n NUM       Number of random videos (default 1)"
  echo "  --freetube   Open with FreeTube (freetube:// URL scheme)"
  echo "  --browser    Open with default browser (default)"
  echo "  --print      Do not open, just print results"
  echo "  DB_PATH      SQLite DB path (default gamegrumps.db)"
}

# Parse args
ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -n)
      COUNT="$2"; shift 2;;
    --freetube)
      OPEN_MODE="freetube"; shift;;
    --browser)
      OPEN_MODE="browser"; shift;;
    --print)
      OPEN_MODE="none"; shift;;
    -h|--help)
      usage; exit 0;;
    *)
      ARGS+=("$1"); shift;;
  esac
done
if [[ ${#ARGS[@]} -gt 0 ]]; then
  DB_PATH="${ARGS[0]}"
fi

python3 - <<'PY' "$DB_PATH" "$COUNT" "$OPEN_MODE"
import sys
import sqlite3
import webbrowser

DB_PATH, COUNT, OPEN_MODE = sys.argv[1], int(sys.argv[2]), sys.argv[3]

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM videos")
count = c.fetchone()[0]
if count == 0:
    print("No videos in database. Run gg-scrape.sh first.")
    sys.exit(1)

c.execute(f"SELECT title, url FROM videos ORDER BY RANDOM() LIMIT {COUNT}")
rows = c.fetchall()
conn.close()

for idx, (title, url) in enumerate(rows, 1):
    print(f"{idx}. {title}\n{url}")
    if OPEN_MODE == "freetube":
        ft_url = f"freetube://{url}"
        try:
            webbrowser.open(ft_url)
        except Exception:
            pass
    elif OPEN_MODE == "browser":
        try:
            webbrowser.open(url)
        except Exception:
            pass
PY
