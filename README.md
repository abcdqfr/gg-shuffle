# 🎮 Game Grumps Episode Randomizer

**Your ultimate companion for navigating 9,300+ Game Grumps episodes!**

![GG Shuffle GUI](Screenshot%20from%202025-09-01%2001-03-47.png)

*Beautiful dark theme GTK interface with instant thumbnail loading and smooth navigation*

## ✨ Features

- **🎲 Smart Randomization** - Never get stuck choosing what to watch
- **🔗 YouTube Integration** - Direct links for FreeTube compatibility  
- **🖼️ Thumbnail Previews** - See episode thumbnails instantly with smart caching
- **🌙 Beautiful Dark Theme** - Cursor-like aesthetic with smooth animations
- **⌨️ Keyboard Navigation** - Full arrow key and shortcut support
- **💾 Offline Database** - No internet needed for episode browsing
- **🚀 Production Ready** - Async loading, error handling, and performance optimized

## 🚀 Quick Start

1. **Clone** - `git clone https://github.com/abcdqfr/gg-shuffle`
2. **Setup** - `cd gg-shuffle && pipx install yt-dlp`
3. **Launch** - `python3 gg-shuffle.py` (auto-builds database on first run)
4. **Shuffle** - Press Enter/Space for random episodes
5. **Enjoy** - Let the chaos decide your entertainment!

## 🏗️ Project Structure

```
gg-shuffle/
├── gg-shuffle.py                   # Pure Python app (GUI + CLI + scraping)
├── gamegrumps.db                   # SQLite database of videos (9,206 episodes)
├── requirements.txt                # Python dependencies
├── setup.py                        # Simple package setup
└── README.md                       # This file
```

## 🎯 Roadmap

- [x] Beautiful GTK GUI with dark theme
- [x] Thumbnail previews with smart caching
- [x] Full keyboard navigation
- [x] YouTube video scraping via yt-dlp
- [x] FreeTube integration
- [x] Production-ready async processing

## 🛠️ Tech Stack

- **Python 3.8+** - Core language
- **GTK3 + PyGObject** - Beautiful, native GUI framework
- **SQLite** - Episode database with yt-dlp integration
- **Async Processing** - Non-blocking thumbnail loading and caching
- **Modern Python** - Type hints, pathlib, and best practices

## 📦 Installation

```bash
# Clone repository
git clone https://github.com/abcdqfr/gg-shuffle
cd gg-shuffle

# Install dependencies (only need yt-dlp for scraping)
pipx install yt-dlp

# Build the video database
./gg.sh scrape

# Launch the GUI
python3 gg-shuffle.py
```

## 🚀 Development

```bash
# Launch the beautiful GTK GUI
python3 gg-shuffle.py

# Build/refresh the video database
python3 gg-shuffle.py scrape

# Pick random videos from CLI
python3 gg-shuffle.py random

# Interactive TUI (if you prefer terminal)
python3 gg-shuffle.py tui
```

## 🎮 Usage

### GTK GUI (Recommended)
1. **Launch** - `python3 gg-shuffle.py`
2. **Shuffle** - Press Enter/Space or click Shuffle button
3. **Navigate** - Use arrow keys to move between buttons
4. **Actions** - Open in browser (B), FreeTube (F), copy URL (C)
5. **Exit** - Press Q/Esc or click Exit button

### Keyboard Shortcuts
- **Enter/Space** - Shuffle to new random video
- **B** - Open current video in browser
- **F** - Open current video in FreeTube
- **C** - Copy video URL to clipboard
- **Q/Esc** - Exit application
- **Arrow Keys** - Navigate between buttons and fields

### CLI Mode
1. **Build database** - `python3 gg-shuffle.py scrape`
2. **Random pick** - `python3 gg-shuffle.py random` (opens in browser)
3. **Interactive** - `python3 gg-shuffle.py tui` (fuzzy search interface)

---

### Prereqs
- yt-dlp (`pipx install yt-dlp` recommended)
- sqlite3 (usually preinstalled)
- Optional TUI: fzf + xdg-open

### Pure Python CLI
All actions are via one Python script: `gg-shuffle.py`.

- Scrape (build/refresh DB):
```sh
python3 gg-shuffle.py scrape                    # default channel, DB: gamegrumps.db
python3 gg-shuffle.py scrape --db my.db         # custom DB path
```

- Random picks:
```sh
python3 gg-shuffle.py random                    # open 1 in browser
python3 gg-shuffle.py random -n 5               # pick 5 random videos
python3 gg-shuffle.py random --freetube         # open with FreeTube (freetube://)
python3 gg-shuffle.py random --db my.db         # use custom DB
```

- Interactive TUI (requires fzf):
```sh
python3 gg-shuffle.py tui                       # search, press Enter to open
python3 gg-shuffle.py tui --db my.db
```

### Direct Script Usage
```sh
python3 gg-shuffle.py scrape    # Build/refresh database
python3 gg-shuffle.py random    # Pick random video
python3 gg-shuffle.py tui       # Interactive search
```

### Database
- File: `gamegrumps.db`
- Table: `videos(id TEXT PRIMARY KEY, title TEXT, url TEXT)`
- Refresh by re-running `python3 gg-shuffle.py scrape`.
