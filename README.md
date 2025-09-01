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

## �� Quick Start

1. **Install** - `pip install -r requirements.txt`
2. **Populate** - `make populate-sample` (adds 100 sample episodes)
3. **Run** - `make run` or `python run.py`
4. **Shuffle** - Hit the big button for random episode selection
5. **Preview** - Read synopsis and episode details
6. **Launch** - Open directly in FreeTube with one click
7. **Enjoy** - Let the chaos decide your entertainment!

## 🏗️ Project Structure

```
game-grumps-randomizer/
├── src/
│   └── game_grumps_randomizer/     # Main package (no __init__.py)
│       ├── models/                  # Data models
│       │   └── episode.py          # Episode data class
│       ├── database/                # Database management
│       │   └── episode_database.py # SQLite database
│       ├── randomizer/              # Core randomization logic
│       │   └── episode_randomizer.py
│       ├── ui/                     # User interface
│       │   └── main_window.py      # Main application window
│       ├── scraper/                 # Web scraping
│       │   └── youtube_scraper.py  # YouTube data collection
│       ├── utils/                   # Utility functions
│       │   └── data_populator.py   # Sample data generation
│       └── main.py                 # Application entry point
├── tests/                          # Test suite
├── data/                           # Database storage
├── run.py                          # Simple entry point
├── pyproject.toml                  # Modern Python packaging
├── requirements.txt                 # Core dependencies
├── requirements-dev.txt             # Development dependencies
└── Makefile                        # Development tasks
```

## 🎯 Roadmap

- [x] Project structure setup (modern Python standards)
- [x] Episode data models and database
- [x] Core randomizer engine
- [x] Simple GUI interface
- [x] FreeTube integration

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

# Install dependencies
pipx install -r requirements.txt

# Run with sample data
#???? README WILDLY OUT OF DATE, REFACTOR!
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
