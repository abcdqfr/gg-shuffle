#!/usr/bin/env bash
# gg-scrape.sh - Build exhaustive Game Grumps video database using yt-dlp + sqlite3
set -euo pipefail

CHANNEL_URL="${1:-https://www.youtube.com/@GameGrumps/videos}"
DB_PATH="${2:-gamegrumps.db}"

# Use embedded Python for reliability and JSON handling
python3 - <<'PY' "$CHANNEL_URL" "$DB_PATH"
import sys
import sqlite3

try:
    import yt_dlp  # type: ignore
except Exception as ex:
    print("yt-dlp is required. Install with: pipx install yt-dlp or pip install yt-dlp", file=sys.stderr)
    raise

CHANNEL_URL = sys.argv[1]
DB_PATH = sys.argv[2]

print(f"Scraping: {CHANNEL_URL}")

ydl_opts = {
    "extract_flat": True,
    "quiet": True,
    "ignoreerrors": True,
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(CHANNEL_URL, download=False)

entries = [e for e in (info.get("entries") or []) if e and e.get("id")]
print(f"Found {len(entries)} videos")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS videos (id TEXT PRIMARY KEY, title TEXT, url TEXT)")

added = 0
for e in entries:
    vid = e["id"]
    title = e.get("title", "Unknown")
    url = f"https://www.youtube.com/watch?v={vid}"
    c.execute("INSERT OR IGNORE INTO videos VALUES (?, ?, ?)", (vid, title, url))
    added += 1

conn.commit()
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM videos")
total = cur.fetchone()[0]
conn.close()

print(f"Added {added} videos. Total in DB: {total}")
PY
