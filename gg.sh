#!/usr/bin/env bash
# gg.sh - Monolithic CLI for Game Grumps scraping and randomizing
set -euo pipefail

COMMAND="${1:-}"
shift || true

DB_PATH="gamegrumps.db"
COUNT=1
OPEN_MODE="browser" # browser|freetube|none
CHANNEL_URL="https://www.youtube.com/@GameGrumps/videos"

usage() {
  cat <<USAGE
Usage: $0 <command> [options]

Commands:
  scrape                 Build/refresh exhaustive DB via yt-dlp
  random                 Pick random video(s) from DB
  tui                    Interactive fzf picker (optional)

Common options:
  --db PATH              SQLite DB path (default gamegrumps.db)

random options:
  -n NUM                 Number of random picks (default 1)
  --freetube             Open with FreeTube (freetube://)
  --browser              Open with default browser (default)
  --print                Print only, do not open

scrape options:
  --channel URL          Channel videos URL (default Game Grumps)
USAGE
}

ensure_deps_tui() {
  if ! command -v fzf >/dev/null 2>&1; then
    echo "fzf is required for tui. Install it and retry." >&2
    exit 1
  fi
}

cmd_scrape() {
  # Parse scrape-specific flags
  local args=()
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --db) DB_PATH="$2"; shift 2;;
      --channel) CHANNEL_URL="$2"; shift 2;;
      -h|--help) usage; exit 0;;
      *) args+=("$1"); shift;;
    esac
  done
  python3 - <<'PY' "$CHANNEL_URL" "$DB_PATH"
import sys, sqlite3
try:
    import yt_dlp  # type: ignore
except Exception:
    print("yt-dlp is required. Install with pipx install yt-dlp", file=sys.stderr)
    raise
channel, db = sys.argv[1], sys.argv[2]
print(f"Scraping: {channel}")
opts = {"extract_flat": True, "quiet": True, "ignoreerrors": True}
with yt_dlp.YoutubeDL(opts) as ydl:
    info = ydl.extract_info(channel, download=False)
entries = [e for e in (info.get("entries") or []) if e and e.get("id")]
print(f"Found {len(entries)} videos")
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS videos (id TEXT PRIMARY KEY, title TEXT, url TEXT)")
for e in entries:
    vid = e["id"]
    title = e.get("title", "Unknown")
    url = f"https://www.youtube.com/watch?v={vid}"
    c.execute("INSERT OR IGNORE INTO videos VALUES (?, ?, ?)", (vid, title, url))
conn.commit()
c.execute("SELECT COUNT(*) FROM videos")
print(f"Total in DB: {c.fetchone()[0]}")
conn.close()
PY
}

cmd_random() {
  # Parse random-specific flags
  local args=()
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --db) DB_PATH="$2"; shift 2;;
      -n) COUNT="$2"; shift 2;;
      --freetube) OPEN_MODE="freetube"; shift;;
      --browser) OPEN_MODE="browser"; shift;;
      --print) OPEN_MODE="none"; shift;;
      -h|--help) usage; exit 0;;
      *) args+=("$1"); shift;;
    esac
  done
  python3 - <<'PY' "$DB_PATH" "$COUNT" "$OPEN_MODE"
import sys, sqlite3, webbrowser
DB, count, mode = sys.argv[1], int(sys.argv[2]), sys.argv[3]
conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM videos")
if c.fetchone()[0] == 0:
    print("No videos in database. Run 'gg.sh scrape' first.")
    sys.exit(1)
c.execute(f"SELECT title, url FROM videos ORDER BY RANDOM() LIMIT {count}")
rows = c.fetchall(); conn.close()
for i, (title, url) in enumerate(rows, 1):
    print(f"{i}. {title}\n{url}")
    try:
        if mode == "freetube":
            webbrowser.open(f"freetube://{url}")
        elif mode == "browser":
            webbrowser.open(url)
    except Exception:
        pass
PY
}

cmd_tui() {
  ensure_deps_tui
  # Parse TUI flags
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --db) DB_PATH="$2"; shift 2;;
      -h|--help) usage; exit 0;;
      *) shift;;
    esac
  done
  # Query and pipe to fzf
  python3 - <<'PY' "$DB_PATH" | fzf --with-nth=1 --delimiter='|' --prompt="Search: " --height=90% --border --ansi | awk -F'|' '{print $2}' | xargs -r xdg-open >/dev/null 2>&1 || true
import sys, sqlite3
DB = sys.argv[1]
conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute("SELECT title, url FROM videos ORDER BY title ASC")
for title, url in c.fetchall():
    safe_title = (title or "").replace("|", "-")
    print(f"{safe_title}|{url}")
conn.close()
PY
}

case "$COMMAND" in
  scrape) cmd_scrape "$@";;
  random) cmd_random "$@";;
  tui)    cmd_tui "$@";;
  -h|--help|*) usage;;
 esac
