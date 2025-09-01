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
2. **Setup** - `cd game-grumps-randomizer && pipx install yt-dlp`
3. **Build DB** - `make scrape` (scrapes all Game Grumps videos)
4. **Launch GUI** - `make gui` or `python3 gg_gui.py`
5. **Shuffle** - Press Enter/Space for random episodes
6. **Enjoy** - Let the chaos decide your entertainment!

## 🏗️ Project Structure

```
game-grumps-randomizer/
├── gg_gui.py                       # Beautiful GTK GUI with thumbnails
├── gg.sh                           # Monolithic CLI script (scrape/random/tui)
├── Makefile                        # Development shortcuts
├── gamegrumps.db                  # SQLite database of videos
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

## 🚀 Development

```bash
# Launch the beautiful GTK GUI
make gui

# Or run directly
python3 gg_gui.py

# Build/refresh the video database
make scrape

# Pick random videos from CLI
make random

# Interactive TUI (if you prefer terminal)
make tui
```

## 📦 Installation

```bash
# Clone repository
git clone https://github.com/abcdqfr/gg-shuffle
cd game-grumps-randomizer

# Install dependencies (only need yt-dlp for scraping)
pipx install yt-dlp

# Build the video database
make scrape

# Launch the GUI
make gui
```

## 🎮 Usage

### GTK GUI (Recommended)
1. **Launch** - `make gui` or `python3 gg_gui.py`
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
1. **Build database** - `make scrape`
2. **Random pick** - `make random` (opens in browser)
3. **Interactive** - `make tui` (fuzzy search interface)

---

### Prereqs
- yt-dlp (`pipx install yt-dlp` recommended)
- sqlite3 (usually preinstalled)
- Optional TUI: fzf + xdg-open

### Monolithic CLI
All actions are via one script: `gg.sh`.

- Scrape (build/refresh DB):
```sh
./gg.sh scrape                    # default channel, DB: gamegrumps.db
./gg.sh scrape --db my.db         # custom DB path
./gg.sh scrape --channel URL      # custom channel URL
```

- Random picks:
```sh
./gg.sh random                    # open 1 in browser
./gg.sh random -n 5 --print       # print 5 random picks
./gg.sh random --freetube         # open with FreeTube (freetube://)
./gg.sh random --db my.db         # use custom DB
```

- Interactive TUI (requires fzf):
```sh
./gg.sh tui                       # search, press Enter to open
./gg.sh tui --db my.db
```

### Makefile shortcuts
```sh
make scrape    # ./gg.sh scrape
make random    # ./gg.sh random
make tui       # ./gg.sh tui
```

### Database
- File: `gamegrumps.db`
- Table: `videos(id TEXT PRIMARY KEY, title TEXT, url TEXT)`
- Refresh by re-running `./gg.sh scrape`.
