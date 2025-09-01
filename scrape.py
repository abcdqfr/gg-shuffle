#!/usr/bin/env python3
"""Scrape Game Grumps videos - WORKING VERSION"""

import yt_dlp
import sqlite3

def main():
    print("🚀 Scraping Game Grumps videos...")
    
    # Get videos (limit to 100 for now to avoid timeouts)
    ydl_opts = {
        "extract_flat": True,
        "quiet": True,
        "playlistend": 100
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info("https://www.youtube.com/@GameGrumps/videos", download=False)
    
    videos = info["entries"]
    print(f"🎯 Found {len(videos)} videos!")
    
    # Save to database
    conn = sqlite3.connect("gamegrumps.db")
    c = conn.cursor()
    
    c.execute("CREATE TABLE IF NOT EXISTS videos (id TEXT PRIMARY KEY, title TEXT, url TEXT)")
    
    added = 0
    for entry in videos:
        if entry:
            vid = entry["id"]
            title = entry["title"]
            url = f"https://www.youtube.com/watch?v={vid}"
            
            c.execute("INSERT OR IGNORE INTO videos VALUES (?, ?, ?)", (vid, title, url))
            added += 1
    
    conn.commit()
    
    # Show count
    c.execute("SELECT COUNT(*) FROM videos")
    total = c.fetchone()[0]
    
    print(f"💾 Added {added} videos to database!")
    print(f"📊 Total in database: {total}")
    
    conn.close()

if __name__ == "__main__":
    main()
