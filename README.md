# 🎮 Game Grumps Episode Randomizer

**Your ultimate companion for navigating 9,300+ Game Grumps episodes!**

## ✨ Features

- **🎲 Smart Randomization** - Never get stuck choosing what to watch
- **🔗 YouTube Integration** - Direct links for FreeTube compatibility
- **📝 Episode Synopses** - Know what you're getting into before watching
- **🎯 Series Filtering** - Binge specific games or eras
- **🧠 Quiz Mode** - Test your Grumps knowledge
- **💾 Offline Database** - No internet needed for episode browsing

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
- [ ] Quiz mode
- [ ] Series filtering
- [ ] Personal watch history
- [ ] YouTube scraping for real episodes

## 🛠️ Tech Stack

- **Python 3.8+** - Core language
- **Modern Packaging** - pyproject.toml, no __init__.py files
- **SQLite** - Episode database
- **tkinter** - GUI framework
- **requests/beautifulsoup** - Web scraping
- **pytest** - Testing framework

## 🚀 Development

```bash
# Setup development environment
make dev-setup

# Run tests
make test

# Format code
make format

# Lint code
make lint

# Run with sample data
make demo

# Build package
make build
```

## 📦 Installation

```bash
# Clone repository
git clone <your-repo-url>
cd game-grumps-randomizer

# Install dependencies
pip install -r requirements.txt

# Run with sample data
make quick-start
```

## 🎮 Usage

1. **Launch the app** - `python run.py`
2. **Set filters** - Choose game series, episode type, etc.
3. **Hit SHUFFLE** - Get a random episode
4. **Read synopsis** - Learn about the episode
5. **Open in FreeTube** - Watch the episode
6. **Rate & track** - Mark as watched with rating

---

*"I'm not gonna sugarcoat it, this is gonna be a rough one." - Arin Hanson*

*"But we're gonna get through it together!" - Dan Avidan*

## Game Grumps Randomizer (KISS)

Minimal, shell-first tool to index Game Grumps videos and shuffle them.

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
