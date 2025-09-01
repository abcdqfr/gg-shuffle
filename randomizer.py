#!/usr/bin/env python3
"""Random Game Grumps video picker - WORKING VERSION"""

import sqlite3
import webbrowser

def main():
    # Connect to database
    conn = sqlite3.connect("gamegrumps.db")
    c = conn.cursor()
    
    # Get total count
    c.execute("SELECT COUNT(*) FROM videos")
    total = c.fetchone()[0]
    
    if total == 0:
        print("❌ No videos in database! Run scrape.py first!")
        return
    
    print(f"🎲 Game Grumps Randomizer ({total} videos)")
    print("=" * 40)
    
    while True:
        # Pick random video
        c.execute("SELECT title, url FROM videos ORDER BY RANDOM() LIMIT 1")
        result = c.fetchone()
        
        if result:
            title, url = result
            print(f"\n🎯 Picked: {title}")
            print(f"🔗 {url}")
            
            # Ask what to do
            choice = input("\n[O]pen in browser, [N]ew pick, [Q]uit? ").lower()
            
            if choice == 'o':
                webbrowser.open(url)
            elif choice == 'q':
                break
            elif choice == 'n':
                continue
            else:
                print("Invalid choice!")
        else:
            print("❌ No video found!")
            break
    
    conn.close()
    print("\n👋 Bye!")

if __name__ == "__main__":
    main()
