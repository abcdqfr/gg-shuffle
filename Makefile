# Game Grumps Episode Randomizer Makefile

.PHONY: help install install-dev test test-cov lint format clean run demo populate-sample

help:  ## Show this help message
	@echo "Game Grumps Episode Randomizer - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install core dependencies
	pip install -r requirements.txt

install-dev:  ## Install development dependencies
	pip install -r requirements-dev.txt

test:  ## Run tests
	python3 -m pytest tests/ -v

test-cov:  ## Run tests with coverage
	python3 -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

lint:  ## Run linting checks
	ruff check src/ tests/
	ruff format --check src/ tests/

format:  ## Format code
	ruff format src/ tests/
	ruff check --fix src/ tests/

clean:  ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf build/ dist/ htmlcov/ .coverage

run:  ## Run the application
	python3 run.py

demo:  ## Run with sample data populated
	python3 scripts/populate_demo.py

populate-sample:  ## Populate database with sample episodes
	python3 scripts/populate_sample.py

build:  ## Build the application
	python3 -m build

dist:  ## Create distribution packages
	python3 -m build --wheel --sdist

check:  ## Run all checks (lint, test, format)
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) format

dev-setup:  ## Setup development environment
	$(MAKE) install-dev
	$(MAKE) populate-sample
	pre-commit install

# Database operations
db-init:  ## Initialize database
	python3 scripts/init_db.py

db-stats:  ## Show database statistics
	python3 scripts/db_stats.py

# Quick start
quick-start:  ## Quick start with sample data
	$(MAKE) install
	$(MAKE) populate-sample
	$(MAKE) run

# Scraping operations
scrape-real:  ## Scrape real Game Grumps episodes from YouTube
	python3 scripts/scrape_real_episodes.py

scrape-all:  ## BRUTE FORCE: Get ALL Game Grumps videos ever uploaded!
	python3 scripts/scrape_all_videos.py

scrape-ytdlp:  ## yt-dlp: Get ALL Game Grumps videos via yt-dlp!
	python3 scripts/yt_dlp_scraper.py

# Simple monolithic CLI
scrape:  ## Build/refresh exhaustive DB via yt-dlp
	./gg.sh scrape

random:  ## Pick/open a random video from DB
	./gg.sh random

tui:  ## Interactive picker (fzf)
	./gg.sh tui

gui:  ## GTK GUI with thumbnails and caching
	python3 gg_gui.py
