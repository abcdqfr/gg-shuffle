# 🎮 Game Grumps Episode Randomizer

**Don't get stumped choosing a random Game Grumps episode again!**

![GG Shuffle GUI](Screenshot.png)

*Beautiful dark theme GTK interface with instant thumbnail loading and smooth navigation*

## 🌟 In Loving Memory of randomgrump.com

This project was inspired by and serves as a modern replacement for **randomgrump.com** - the beloved website that helped Game Grumps fans discover random episodes for years. While the original site is no longer available, we've created something else:

- **Native desktop app** - Beautiful GTK interface
- **Enhanced features** - Thumbnails, descriptions, view counts, and more
- **Cross-platform** - Works on Linux, macOS, and Windows (via WSL)

*Thank you to the creators of randomgrump.com for inspiring this project!* 🙏

## ✨ Features

- **🎲 Smart Randomization** - Never get stuck choosing what to watch
- **🔗 YouTube Integration** - Direct links for FreeTube compatibility  
- **🖼️ Thumbnail Previews** - See episode thumbnails instantly with smart caching
- **📊 Rich Metadata** - View counts, duration, upload dates, and descriptions
- **🌙 Beautiful Dark Theme** - Cursor-like aesthetic with smooth animations
- **⌨️ Keyboard Navigation** - Full arrow key and shortcut support
- **💾 Offline Database** - No internet needed for episode browsing
- **🔄 Previous Navigation** - Go back through up to 50 recent videos
- **⚡ Streaming Architecture** - Metadata loaded on-demand, no bloat
- **🚀 Production Ready** - Async loading, error handling, and performance optimized

## 🚀 Quick Start

### Linux & macOS
1. **Clone** - `git clone https://github.com/abcdqfr/gg-shuffle`
2. **Setup** - `cd gg-shuffle && pipx install yt-dlp`
3. **Launch** - `python3 gg-shuffle.py` (auto-builds database on first run)
4. **Shuffle** - Press Enter/Space for random episodes
5. **Enjoy** - Let the chaos decide your entertainment!

### Windows (WSL)
1. **Install WSL** - `wsl --install` (if not already installed)
2. **Open WSL** - Launch Ubuntu or your preferred Linux distribution
3. **Follow Linux steps** - Same as above, but within WSL
4. **Launch** - `python3 gg-shuffle.py` (works perfectly in WSL!)

*Note: WSL users get the full Linux experience with native performance!*

## 🏗️ Project Structure

```
gg-shuffle/
├── gg-shuffle.py                   # Pure Python app (GUI + CLI + Indexing)
├── gamegrumps.db                   # SQLite database of videos (9,206 episodes)
├── requirements.txt                # Python dependencies
├── setup.py                        # Simple package setup
└── README.md                       # This file
```

## 🎯 Roadmap

- [x] Beautiful GTK GUI with dark theme
- [x] Thumbnail previews with smart caching
- [x] Full keyboard navigation
- [x] YouTube video indexing via yt-dlp
- [x] FreeTube integration
- [x] Production-ready async processing
- [x] Rich metadata display (view counts, duration, descriptions)
- [x] Previous navigation with 50-video history
- [x] Streaming architecture (no database bloat)
- [x] Clean UI with expandable technical details
- [x] Cross-platform support (Linux, macOS, Windows WSL)

## 🛠️ Tech Stack

- **Python 3.8+** - Core language
- **GTK3 + PyGObject** - Beautiful, native GUI framework
- **SQLite** - Minimal episode database (id, title, url only)
- **yt-dlp** - YouTube video indexing and metadata streaming
- **Async Processing** - Non-blocking thumbnail and metadata loading
- **Streaming Architecture** - Metadata fetched on-demand, no database bloat
- **Modern Python** - Type hints, pathlib, and best practices

## ⚡ Streaming Architecture

Unlike traditional approaches that cache everything, GG Shuffle uses a **streaming architecture**:

- **Database**: Minimal (just video IDs, titles, URLs)
- **Thumbnails**: Cached locally, streamed on-demand
- **Metadata**: Streamed from YouTube when displayed (view counts, descriptions, etc.)
- **Benefits**: Fast indexing, no rate limiting, always fresh data, minimal storage

## 📦 Installation

```bash
# Clone repository
git clone https://github.com/abcdqfr/gg-shuffle
cd gg-shuffle

# Install dependencies (only need yt-dlp for Indexing)
pipx install yt-dlp

# Launch the GUI
python3 gg-shuffle.py
```

## 🚀 Development

```bash
# Build/refresh the video database
python3 gg-shuffle.py index

# Pick random videos from CLI
python3 gg-shuffle.py random

# Interactive TUI (if you prefer terminal)
python3 gg-shuffle.py tui
```

## 🎮 Usage

### GTK GUI (Recommended)
1. **Launch** - `python3 gg-shuffle.py`
2. **Navigate** - Use arrow keys to move between buttons
3. **Actions** - Previous (P), Shuffle (S), Open in browser (B), FreeTube (F), copy URL (C)
4. **Exit** - Press Q/Esc or click Exit button

### Keyboard Shortcuts
- **P** - Navigate back to previous video
- **S** - Shuffle to new random video
- **B** - Open current video in browser
- **F** - Open current video in FreeTube
- **C** - Copy video URL to clipboard
- **Q/Esc** - Exit application
- **Arrow Keys** - Navigate between buttons and fields

### CLI Mode
1. **Build database** - `python3 gg-shuffle.py index`
2. **Random pick** - `python3 gg-shuffle.py random` (opens in browser)
3. **Interactive** - `python3 gg-shuffle.py tui` (fuzzy search interface)

---

### Prereqs
- yt-dlp (`pipx install yt-dlp` recommended)
- sqlite3 (usually preinstalled)
- Optional TUI: fzf + xdg-open

### Pure Python CLI
All actions are via one Python script: `gg-shuffle.py`.

- index (build/refresh DB):
```sh
python3 gg-shuffle.py index                    # default channel, DB: gamegrumps.db
python3 gg-shuffle.py index --db my.db         # custom DB path
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
python3 gg-shuffle.py index    # Build/refresh database
python3 gg-shuffle.py random    # Pick random video
python3 gg-shuffle.py tui       # Interactive search
```

### Database
- File: `gamegrumps.db`
- Table: `videos(id TEXT PRIMARY KEY, title TEXT, url TEXT)`
- Refresh by re-running `python3 gg-shuffle.py index`.
