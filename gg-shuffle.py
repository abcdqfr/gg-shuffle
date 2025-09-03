#!/usr/bin/env python3
"""Minimal GTK GUI to shuffle and open Game Grumps videos (K.I.S.S.)."""

import argparse
import hashlib
import sqlite3
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path
from typing import Tuple, Optional

import gi  # type: ignore

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib  # type: ignore

DB_PATH = Path(__file__).parent / "gamegrumps.db"
CACHE_DIR = Path.home() / ".cache" / "gg-shuffle" / "thumbs"
CACHE_MAX_AGE_DAYS = 30


def scrape_videos(channel_url: str = "https://www.youtube.com/@GameGrumps/videos", db_path: str = "gamegrumps.db") -> None:
    """Scrape Game Grumps videos using yt-dlp and store in SQLite database."""
    try:
        import yt_dlp  # type: ignore
    except ImportError:
        print("yt-dlp is required. Install with: pipx install yt-dlp or pip install yt-dlp")
        sys.exit(1)
    
    print(f"Scraping: {channel_url}")
    
    # First pass: get video list (fast)
    ydl_opts_flat = {
        "extract_flat": True,
        "quiet": True,
        "ignoreerrors": True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts_flat) as ydl:
        info = ydl.extract_info(channel_url, download=False)
    
    entries = [e for e in (info.get("entries") or []) if e and e.get("id")]
    print(f"Found {len(entries)} videos")
    
    # Setup database with enhanced schema
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY, 
            title TEXT, 
            url TEXT,
            description TEXT,
            view_count INTEGER,
            duration INTEGER,
            upload_date TEXT
        )
    """)
    
    # Second pass: get detailed info for each video (slower but more data)
    ydl_opts_detailed = {
        "quiet": True,
        "ignoreerrors": True,
        "no_warnings": True,
    }
    
    added = 0
    for i, e in enumerate(entries):
        vid = e["id"]
        title = e.get("title", "Unknown")
        url = f"https://www.youtube.com/watch?v={vid}"
        
        # Try to get detailed info
        description = ""
        view_count = 0
        duration = 0
        upload_date = ""
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts_detailed) as ydl:
                detailed_info = ydl.extract_info(url, download=False)
                if detailed_info:
                    description = detailed_info.get("description", "")[:500]  # Limit description length
                    view_count = detailed_info.get("view_count", 0) or 0
                    duration = detailed_info.get("duration", 0) or 0
                    upload_date = detailed_info.get("upload_date", "")
        except Exception:
            # If detailed extraction fails, continue with basic info
            pass
        
        c.execute("""
            INSERT OR REPLACE INTO videos 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (vid, title, url, description, view_count, duration, upload_date))
        added += 1
        
        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1}/{len(entries)} videos...")
    
    conn.commit()
    c.execute("SELECT COUNT(*) FROM videos")
    total = c.fetchone()[0]
    conn.close()
    
    print(f"Added {added} videos. Total in DB: {total}")


def fetch_random(conn: sqlite3.Connection) -> Tuple[str, str, str, int, int, str]:
    """Fetch random video with enhanced metadata."""
    cur = conn.cursor()
    cur.execute("SELECT title, url, description, view_count, duration, upload_date FROM videos ORDER BY RANDOM() LIMIT 1")
    row = cur.fetchone()
    if row:
        return (row[0], row[1], row[2] or "", row[3] or 0, row[4] or 0, row[5] or "")
    return ("Unknown", "", "", 0, 0, "")


def extract_video_id(url: str) -> str:
    if "watch?v=" in url:
        return url.split("watch?v=")[-1].split("&")[0]
    return ""


def thumbnail_url(video_id: str) -> str:
    return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg" if video_id else ""


def init_cache() -> None:
    """Initialize thumbnail cache directory."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def cache_path_for_video_id(video_id: str) -> Path:
    """Get cache file path for a video ID."""
    # Use hash to avoid filesystem issues with special chars
    safe_name = hashlib.md5(video_id.encode()).hexdigest()
    return CACHE_DIR / f"{safe_name}.jpg"


def is_cache_valid(cache_file: Path) -> bool:
    """Check if cached thumbnail is still valid (not expired)."""
    if not cache_file.exists():
        return False
    age_seconds = time.time() - cache_file.stat().st_mtime
    age_days = age_seconds / (24 * 3600)
    return age_days < CACHE_MAX_AGE_DAYS


def load_pixbuf_from_cache(video_id: str) -> Optional[GdkPixbuf.Pixbuf]:
    """Load thumbnail from cache if available and valid."""
    if not video_id:
        return None
    cache_file = cache_path_for_video_id(video_id)
    if is_cache_valid(cache_file):
        try:
            return GdkPixbuf.Pixbuf.new_from_file_at_scale(
                str(cache_file), 320, 180, True
            )
        except Exception:
            # Cache file corrupted, remove it
            cache_file.unlink(missing_ok=True)
    return None


def download_and_cache_thumbnail(video_id: str, url: str, timeout: float = 5.0) -> Optional[GdkPixbuf.Pixbuf]:
    """Download thumbnail and save to cache."""
    if not url or not video_id:
        return None
    
    cache_file = cache_path_for_video_id(video_id)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = resp.read()
        
        # Save to cache
        cache_file.write_bytes(data)
        
        # Load as pixbuf
        loader = GdkPixbuf.PixbufLoader()
        loader.write(data)
        loader.close()
        pixbuf = loader.get_pixbuf()
        if pixbuf and (pixbuf.get_width() > 320 or pixbuf.get_height() > 180):
            return pixbuf.scale_simple(320, 180, GdkPixbuf.InterpType.BILINEAR)
        return pixbuf
    except Exception:
        # Clean up partial cache file on error
        cache_file.unlink(missing_ok=True)
        return None


def load_thumbnail_async(video_id: str, callback) -> None:
    """Load thumbnail with cache support in background thread."""
    def worker():
        # Try cache first
        pixbuf = load_pixbuf_from_cache(video_id)
        if pixbuf is not None:
            GLib.idle_add(callback, pixbuf)
            return
        
        # Download and cache
        url = thumbnail_url(video_id)
        pixbuf = download_and_cache_thumbnail(video_id, url)
        GLib.idle_add(callback, pixbuf)
    
    if video_id:
        threading.Thread(target=worker, daemon=True).start()
    else:
        GLib.idle_add(callback, None)


class GGWindow(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(title="GG Shuffle")
        self.set_default_size(740, 380)  # Taller for status bar
        self.connect("destroy", Gtk.main_quit)

        # Initialize cache
        init_cache()

        # Prefer dark theme + CSS styling
        settings = Gtk.Settings.get_default()
        if settings is not None:
            settings.set_property("gtk-application-prefer-dark-theme", True)
        self._apply_css()

        # State tracking
        self.current_url: str = ""
        self.current_title: str = ""
        self.current_video_id: str = ""
        self.previous_video_ids: list = []  # Stack of previous video IDs (max 50)
        self.db_update_thread: Optional[threading.Thread] = None
        self.is_updating_db: bool = False

        # Root layout
        self.root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.root.set_border_width(12)
        self.add(self.root)

        # Status bar (always present)
        self.status_bar = Gtk.Statusbar()
        self.status_context_id = self.status_bar.get_context_id("main")
        self.status_bar.get_style_context().add_class("gg-status")
        
        # Main content area (will be switched between welcome and main)
        self.content_stack = Gtk.Stack()
        self.content_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.root.pack_start(self.content_stack, True, True, 0)
        
        # Add status bar at bottom
        self.root.pack_start(self.status_bar, False, False, 0)

        # Check DB state and show appropriate UI (now that status bar exists)
        self.conn = None
        self._check_database_state()
        self._build_ui()

    def _check_database_state(self) -> None:
        """Check database existence and video count."""
        if not DB_PATH.exists():
            self._set_status("Database not found - welcome screen will be shown")
            return
        
        try:
            self.conn = sqlite3.connect(str(DB_PATH))
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM videos")
            count = cursor.fetchone()[0]
            
            if count == 0:
                self._set_status("Database is empty - welcome screen will be shown")
                self.conn.close()
                self.conn = None
            else:
                self._set_status(f"Ready - {count:,} videos in database")
        except sqlite3.Error as e:
            self._set_status(f"Database error: {e}")
            if self.conn:
                self.conn.close()
            self.conn = None

    def _build_ui(self) -> None:
        """Build appropriate UI based on database state."""
        if self.conn is None:
            self._build_welcome_ui()
        else:
            self._build_main_ui()

    def _build_welcome_ui(self) -> None:
        """Build welcome screen for first-time setup."""
        welcome_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        welcome_box.set_halign(Gtk.Align.CENTER)
        welcome_box.set_valign(Gtk.Align.CENTER)
        
        # Welcome message
        title = Gtk.Label()
        title.set_markup("<big><b>Welcome to GG Shuffle!</b></big>")
        title.get_style_context().add_class("gg-title")
        welcome_box.pack_start(title, False, False, 0)
        
        subtitle = Gtk.Label(label="Let's build your Game Grumps video database first.")
        welcome_box.pack_start(subtitle, False, False, 0)
        
        # Progress bar for database building
        self.welcome_progress = Gtk.ProgressBar()
        self.welcome_progress.set_show_text(True)
        self.welcome_progress.set_text("Ready to start...")
        welcome_box.pack_start(self.welcome_progress, False, False, 0)
        
        # Buttons
        button_box = Gtk.Box(spacing=10)
        button_box.set_halign(Gtk.Align.CENTER)
        
        self.build_db_button = Gtk.Button.new_with_mnemonic("_Build Database")
        self.build_db_button.connect("clicked", self._on_build_database)
        self.build_db_button.get_style_context().add_class("suggested-action")
        button_box.pack_start(self.build_db_button, False, False, 0)
        

        
        welcome_box.pack_start(button_box, False, False, 0)
        
        self.content_stack.add_named(welcome_box, "welcome")
        self.content_stack.set_visible_child_name("welcome")

    def _build_main_ui(self) -> None:
        """Build main shuffler UI.""" 
        try:
            # Clean up any existing main UI to prevent duplicate stack children
            existing_main = self.content_stack.get_child_by_name("main")
            if existing_main:
                self.content_stack.remove(existing_main)
            
            # Ensure we have a fresh database connection
            if self.conn:
                self.conn.close()
            self.conn = sqlite3.connect(str(DB_PATH))
            # Test the connection
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM videos")
            count = cursor.fetchone()[0]
            self._set_status(f"Connected - {count:,} videos available")
        except sqlite3.Error as e:
            self._set_status(f"Database error: {e}")
            return
        except Exception as e:
            self._set_status(f"Setup error: {e}")
            return
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        # Content row: thumbnail | details
        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        main_box.pack_start(content, True, True, 0)

        # Thumbnail with fixed size to prevent layout jumping
        self.thumb = Gtk.Image()
        self.thumb.set_size_request(320, 180)  # Reserve space
        self.thumb.set_halign(Gtk.Align.CENTER)
        self.thumb.set_valign(Gtk.Align.CENTER)
        thumb_frame = Gtk.Frame()
        thumb_frame.set_size_request(320, 180)  # Fixed frame size
        thumb_frame.add(self.thumb)
        content.pack_start(thumb_frame, False, False, 0)

        # Details column
        details = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        content.pack_start(details, True, True, 0)

        # Title label (larger, marquee scrolling, no wrap)
        self.title_lbl = Gtk.Label()
        self.title_lbl.set_xalign(0.0)
        self.title_lbl.set_line_wrap(False)  # No wrapping - use marquee instead
        self.title_lbl.set_ellipsize(3)  # Pango.EllipsizeMode.END
        self.title_lbl.set_selectable(True)
        self.title_lbl.get_style_context().add_class("gg-title")
        details.pack_start(self.title_lbl, False, False, 0)
        
        # Description label (smaller, wrapped)
        self.desc_lbl = Gtk.Label()
        self.desc_lbl.set_xalign(0.0)
        self.desc_lbl.set_line_wrap(True)
        self.desc_lbl.set_selectable(True)
        self.desc_lbl.get_style_context().add_class("gg-description")
        details.pack_start(self.desc_lbl, False, False, 0)
        
        # Stats row (view count, duration, upload date)
        self.stats_lbl = Gtk.Label()
        self.stats_lbl.set_xalign(0.0)
        self.stats_lbl.get_style_context().add_class("gg-stats")
        details.pack_start(self.stats_lbl, False, False, 0)

        # URL entry (read-only, selectable)
        self.url_entry = Gtk.Entry()
        self.url_entry.set_editable(False)
        self.url_entry.set_can_focus(True)
        details.pack_start(self.url_entry, False, False, 0)

        # ID + FreeTube rows
        id_row = Gtk.Box(spacing=6)
        details.pack_start(id_row, False, False, 0)
        id_row.pack_start(Gtk.Label(label="ID:"), False, False, 0)
        self.id_entry = Gtk.Entry()
        self.id_entry.set_editable(False)
        self.id_entry.set_can_focus(True)
        id_row.pack_start(self.id_entry, True, True, 0)

        ft_row = Gtk.Box(spacing=6)
        details.pack_start(ft_row, False, False, 0)
        ft_row.pack_start(Gtk.Label(label="FreeTube:"), False, False, 0)
        self.ft_entry = Gtk.Entry()
        self.ft_entry.set_editable(False)
        self.ft_entry.set_can_focus(True)
        ft_row.pack_start(self.ft_entry, True, True, 0)

        # Buttons row
        btns = Gtk.Box(spacing=8)
        main_box.pack_start(btns, False, False, 0)

        self.prev_btn = Gtk.Button.new_with_mnemonic("_Previous")
        self.prev_btn.connect("clicked", self.on_previous)
        self.prev_btn.set_can_focus(True)
        self.prev_btn.set_sensitive(False)  # Disabled initially
        btns.pack_start(self.prev_btn, False, False, 0)

        self.shuffle_btn = Gtk.Button.new_with_mnemonic("_Shuffle")
        self.shuffle_btn.connect("clicked", self.on_shuffle)
        self.shuffle_btn.set_can_focus(True)
        btns.pack_start(self.shuffle_btn, False, False, 0)

        self.browser_btn = Gtk.Button.new_with_mnemonic("Open in _Browser")
        self.browser_btn.connect("clicked", self.on_open_browser)
        self.browser_btn.set_can_focus(True)
        btns.pack_start(self.browser_btn, False, False, 0)

        self.freetube_btn = Gtk.Button.new_with_mnemonic("Open in _FreeTube")
        self.freetube_btn.connect("clicked", self.on_open_freetube)
        self.freetube_btn.set_can_focus(True)
        btns.pack_start(self.freetube_btn, False, False, 0)

        self.copy_btn = Gtk.Button.new_with_mnemonic("_Copy URL")
        self.copy_btn.connect("clicked", self.on_copy_url)
        self.copy_btn.set_can_focus(True)
        btns.pack_start(self.copy_btn, False, False, 0)

        # Update database button
        self.update_btn = Gtk.Button.new_with_mnemonic("_Update DB")
        self.update_btn.connect("clicked", self._on_update_database)
        self.update_btn.set_can_focus(True)
        btns.pack_start(self.update_btn, False, False, 0)

        self.exit_btn = Gtk.Button.new_with_mnemonic("E_xit")
        self.exit_btn.connect("clicked", lambda _b: Gtk.main_quit())
        self.exit_btn.set_can_focus(True)
        btns.pack_end(self.exit_btn, False, False, 0)

        # Add to stack
        self.content_stack.add_named(main_box, "main")
        self.content_stack.set_visible_child_name("main")
        
        # Force UI refresh
        self.content_stack.show_all()
        self.show_all()

        # Keyboard shortcuts
        self.shuffle_btn.set_can_default(True)
        self.set_default(self.shuffle_btn)
        self.connect("key-press-event", self.on_key_press)

        # Initial load
        self.enable_actions()
        self.load_random()

    def _apply_css(self) -> None:
        css = b"""
        window, .background { background-color: #1e1f22; }
        label { color: #e6e8eb; }
        entry { color: #e6e8eb; background: #2b2d31; border-radius: 6px; border: 1px solid #3a3d42; }
        button { background: #2b2d31; color: #e6e8eb; border: 1px solid #3a3d42; border-radius: 6px; padding: 6px 10px; }
        button:hover { background: #34373c; }
        .suggested-action { background: #007acc; border-color: #007acc; }
        .suggested-action:hover { background: #0085d1; }
        .gg-title { font-weight: 600; font-size: 20px; color: #ffffff; }
        .gg-description { font-size: 14px; color: #b9bbbe; margin-top: 8px; }
        .gg-stats { font-size: 12px; color: #8e9297; margin-top: 4px; }
        .gg-status { background: #2b2d31; color: #e6e8eb; border-top: 1px solid #3a3d42; }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _set_status(self, message: str) -> None:
        """Update status bar message."""
        self.status_bar.remove_all(self.status_context_id)
        self.status_bar.push(self.status_context_id, message)

    def _on_build_database(self, _widget: Gtk.Widget) -> None:
        """Start building database in background thread."""
        if self.is_updating_db:
            return
            
        self.is_updating_db = True
        self.build_db_button.set_sensitive(False)
        self.build_db_button.set_label("Building Database...")
        self.welcome_progress.set_text("Starting database build...")
        self._set_status("Building database - this may take a few minutes...")
        
        def build_worker():
            try:
                # Update progress
                GLib.idle_add(self.welcome_progress.set_text, "Downloading video list...")
                GLib.idle_add(self.welcome_progress.pulse)
                
                # Use pure Python scraping
                scrape_videos(db_path=str(DB_PATH))
                
                GLib.idle_add(self._on_build_complete)
                    
            except Exception as e:
                GLib.idle_add(self._on_build_error, f"Build error: {e}")
        
        self.db_update_thread = threading.Thread(target=build_worker, daemon=True)
        self.db_update_thread.start()
        
        # Start progress pulse
        GLib.timeout_add(100, self._pulse_progress)

    def _pulse_progress(self) -> bool:
        """Pulse progress bar while building."""
        if not self.is_updating_db:
            return False
        self.welcome_progress.pulse()
        return True

    def _on_build_complete(self) -> None:
        """Handle successful database build."""
        self.is_updating_db = False
        self.welcome_progress.set_text("Database build complete!")
        self.welcome_progress.set_fraction(1.0)
        self._set_status("Database build complete - please restart the app")
        
        # Reconnect to database to verify it's ready
        try:
            self.conn = sqlite3.connect(str(DB_PATH))
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM videos")
            count = cursor.fetchone()[0]
            self._set_status(f"Database ready - {count:,} videos available - please restart the app")
            
            # Hide the button and show restart message
            self.build_db_button.hide()
            
            # Add restart message
            restart_label = Gtk.Label()
            restart_label.set_markup("<big><b>✅ Database Ready!</b></big>\n\nPlease restart the app to continue.")
            restart_label.set_halign(Gtk.Align.CENTER)
            restart_label.set_valign(Gtk.Align.CENTER)
            restart_label.get_style_context().add_class("gg-title")
            
            # Add to the welcome box
            welcome_box = self.content_stack.get_child_by_name("welcome")
            if welcome_box:
                welcome_box.pack_start(restart_label, False, False, 0)
                welcome_box.show_all()
            
        except sqlite3.Error as e:
            self._on_build_error(f"Database connection error: {e}")

    def _switch_to_main_ui(self) -> bool:
        """Switch from welcome screen to main UI."""
        self._build_main_ui()
        return False  # Don't repeat

    def _on_continue_to_app(self, _widget: Gtk.Widget) -> None:
        """Continue to main app after database build."""
        self._set_status("Switching to main app...")
        
        # Build the main UI directly
        self._build_main_ui()

    def _on_build_error(self, error_msg: str) -> None:
        """Handle database build error."""
        self.is_updating_db = False
        self.build_db_button.set_sensitive(True)
        self.welcome_progress.set_text(f"Error: {error_msg}")
        self.welcome_progress.set_fraction(0.0)
        self._set_status(f"Build failed: {error_msg}")



    def _on_update_database(self, _widget: Gtk.Widget) -> None:
        """Update database in background."""
        if self.is_updating_db:
            return
            
        self.is_updating_db = True
        self.update_btn.set_sensitive(False)
        self._set_status("Updating database...")
        
        def update_worker():
            try:
                # Use pure Python scraping
                scrape_videos(db_path=str(DB_PATH))
                GLib.idle_add(self._on_update_complete)
                    
            except Exception as e:
                GLib.idle_add(self._on_update_error, f"Update error: {e}")
        
        threading.Thread(target=update_worker, daemon=True).start()

    def _on_update_complete(self) -> None:
        """Handle successful database update."""
        self.is_updating_db = False
        self.update_btn.set_sensitive(True)
        
        # Refresh database connection
        if self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM videos")
            count = cursor.fetchone()[0]
            self._set_status(f"Database updated - {count:,} videos available")
        else:
            self._set_status("Database update complete")

    def _on_update_error(self, error_msg: str) -> None:
        """Handle database update error."""
        self.is_updating_db = False
        self.update_btn.set_sensitive(True)
        self._set_status(f"Update failed: {error_msg}")

    # Enable/disable buttons based on DB availability

    def enable_actions(self) -> None:
        for b in (self.prev_btn, self.shuffle_btn, self.browser_btn, self.freetube_btn, self.copy_btn):
            b.set_sensitive(True)

    # Core actions
    def load_random(self) -> None:
        if not self.conn:
            return
        try:
            title, url, description, view_count, duration, upload_date = fetch_random(self.conn)
            vid = extract_video_id(url)
            
            # Add current video to previous stack before updating
            if self.current_video_id:
                self.previous_video_ids.append(self.current_video_id)
                # Limit to 50 videos to prevent memory issues
                if len(self.previous_video_ids) > 50:
                    self.previous_video_ids = self.previous_video_ids[-50:]
            
            # Update current video info
            self.current_title = title
            self.current_url = url
            self.current_video_id = vid
            
            ft = f"freetube://{url}" if url else ""
            self.title_lbl.set_text(title or "(No title)")
            self.url_entry.set_text(url or "")
            self.id_entry.set_text(vid)
            self.ft_entry.set_text(ft)
            
            # Update description
            desc_text = description or "No description available"
            self.desc_lbl.set_text(desc_text)
            
            # Update stats
            stats_parts = []
            if view_count > 0:
                if view_count >= 1000000:
                    stats_parts.append(f"{view_count/1000000:.1f}M views")
                elif view_count >= 1000:
                    stats_parts.append(f"{view_count/1000:.1f}K views")
                else:
                    stats_parts.append(f"{view_count:,} views")
            
            if duration > 0:
                hours = duration // 3600
                minutes = (duration % 3600) // 60
                if hours > 0:
                    stats_parts.append(f"{hours}h {minutes}m")
                else:
                    stats_parts.append(f"{minutes}m")
            
            if upload_date:
                try:
                    # Format YYYYMMDD to readable date
                    year = upload_date[:4]
                    month = upload_date[4:6]
                    day = upload_date[6:8]
                    stats_parts.append(f"{year}-{month}-{day}")
                except:
                    pass
            
            stats_text = " • ".join(stats_parts) if stats_parts else "No stats available"
            self.stats_lbl.set_text(stats_text)
            
            # Show loading placeholder while loading thumbnail async
            self._set_loading_placeholder()
            load_thumbnail_async(vid, self._on_thumbnail_loaded)
            
            # Focus URL for quick copy
            self.url_entry.select_region(0, -1)
            self.url_entry.grab_focus()
            
            # Update previous button state
            self.prev_btn.set_sensitive(len(self.previous_video_ids) > 0)
        except Exception as e:
            self._set_status(f"Error loading video: {e}")

    def on_previous(self, _btn: Gtk.Button) -> None:
        """Go back to previous video."""
        if not self.previous_video_ids or not self.conn:
            return
            
        try:
            # Get the most recent previous video ID
            previous_video_id = self.previous_video_ids.pop()
            
            # Look up the previous video in the database
            cursor = self.conn.cursor()
            cursor.execute("SELECT title, url, description, view_count, duration, upload_date FROM videos WHERE id = ?", (previous_video_id,))
            result = cursor.fetchone()
            
            if result:
                title, url, description, view_count, duration, upload_date = result
                
                # Update current video info
                self.current_title = title
                self.current_url = url
                self.current_video_id = previous_video_id
                
                ft = f"freetube://{url}" if url else ""
                self.title_lbl.set_text(title or "(No title)")
                self.url_entry.set_text(url or "")
                self.id_entry.set_text(previous_video_id)
                self.ft_entry.set_text(ft)
                
                # Update description
                desc_text = description or "No description available"
                self.desc_lbl.set_text(desc_text)
                
                # Update stats
                stats_parts = []
                if view_count > 0:
                    if view_count >= 1000000:
                        stats_parts.append(f"{view_count/1000000:.1f}M views")
                    elif view_count >= 1000:
                        stats_parts.append(f"{view_count/1000:.1f}K views")
                    else:
                        stats_parts.append(f"{view_count:,} views")
                
                if duration > 0:
                    hours = duration // 3600
                    minutes = (duration % 3600) // 60
                    if hours > 0:
                        stats_parts.append(f"{hours}h {minutes}m")
                    else:
                        stats_parts.append(f"{minutes}m")
                
                if upload_date:
                    try:
                        # Format YYYYMMDD to readable date
                        year = upload_date[:4]
                        month = upload_date[4:6]
                        day = upload_date[6:8]
                        stats_parts.append(f"{year}-{month}-{day}")
                    except:
                        pass
                
                stats_text = " • ".join(stats_parts) if stats_parts else "No stats available"
                self.stats_lbl.set_text(stats_text)
                
                # Show loading placeholder while loading thumbnail async
                self._set_loading_placeholder()
                load_thumbnail_async(previous_video_id, self._on_thumbnail_loaded)
                
                # Focus URL for quick copy
                self.url_entry.select_region(0, -1)
                self.url_entry.grab_focus()
                
                # Update previous button state
                self.prev_btn.set_sensitive(len(self.previous_video_ids) > 0)
                
        except Exception as e:
            self._set_status(f"Error loading previous video: {e}")

    def _set_loading_placeholder(self) -> None:
        """Set a subtle loading placeholder that maintains layout."""
        # Create a simple gray placeholder at 320x180
        placeholder = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 320, 180)
        placeholder.fill(0x2b2d31ff)  # Dark gray matching our theme
        self.thumb.set_from_pixbuf(placeholder)

    def _on_thumbnail_loaded(self, pixbuf: Optional[GdkPixbuf.Pixbuf]) -> None:
        """Callback when thumbnail is loaded (from cache or download)."""
        if pixbuf is not None:
            self.thumb.set_from_pixbuf(pixbuf)
        else:
            # Keep placeholder if no thumbnail available
            self._set_loading_placeholder()

    def on_shuffle(self, _btn: Gtk.Button) -> None:
        self.load_random()

    def on_open_browser(self, _btn: Gtk.Button) -> None:
        if self.current_url:
            try:
                webbrowser.open(self.current_url)
            except Exception:
                pass

    def on_open_freetube(self, _btn: Gtk.Button) -> None:
        if self.current_url:
            try:
                webbrowser.open(f"freetube://{self.current_url}")
            except Exception:
                pass

    def on_copy_url(self, _btn: Gtk.Button) -> None:
        clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clip.set_text(self.current_url or "", -1)

    # Keyboard shortcuts
    def on_key_press(self, _w: Gtk.Widget, event: Gdk.EventKey) -> bool:  # type: ignore[name-defined]
        key = Gdk.keyval_name(event.keyval)
        if key in ("space", "Return", "KP_Enter"):
            self.load_random()
            return True
        elif key in ("Left", "Right", "Up", "Down", "Tab", "ISO_Left_Tab"):  # let GTK handle focus movement
            return False
        elif key in ("p", "P"):
            self.on_previous(self.prev_btn)
            return True
        elif key in ("b", "B"):
            self.on_open_browser(self.browser_btn)
            return True
        elif key in ("f", "F"):
            self.on_open_freetube(self.freetube_btn)
            return True
        elif key in ("c", "C"):
            self.on_copy_url(self.copy_btn)
            return True
        elif key in ("q", "Q", "Escape"):
            Gtk.main_quit()
            return True
        return False


def cli_random(db_path: str = "gamegrumps.db", count: int = 1, mode: str = "browser") -> None:
    """CLI random video picker."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM videos")
    if c.fetchone()[0] == 0:
        print("No videos in database. Run 'python3 gg-shuffle.py scrape' first.")
        sys.exit(1)
    
    c.execute(f"SELECT title, url FROM videos ORDER BY RANDOM() LIMIT {count}")
    rows = c.fetchall()
    conn.close()
    
    for i, (title, url) in enumerate(rows, 1):
        print(f"{i}. {title}\n{url}")
        try:
            if mode == "freetube":
                webbrowser.open(f"freetube://{url}")
            elif mode == "browser":
                webbrowser.open(url)
        except Exception:
            pass


def cli_tui(db_path: str = "gamegrumps.db", mode: str = "browser") -> None:
    """CLI TUI using fzf."""
    import subprocess
    
    if not subprocess.run(["which", "fzf"], capture_output=True).returncode == 0:
        print("fzf is required for TUI. Install it (e.g., sudo apt-get install -y fzf)")
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT title, url FROM videos ORDER BY title ASC")
    
    for title, url in c.fetchall():
        safe_title = (title or "").replace("|", "-")
        print(f"{safe_title}|{url}")
    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Game Grumps Episode Randomizer")
    parser.add_argument("command", nargs="?", choices=["scrape", "random", "tui"], 
                       help="Command to run (default: GUI)")
    parser.add_argument("--db", default="gamegrumps.db", help="Database path")
    parser.add_argument("-n", type=int, default=1, help="Number of random videos")
    parser.add_argument("--freetube", action="store_true", help="Open with FreeTube")
    parser.add_argument("--browser", action="store_true", help="Open with browser")
    
    args = parser.parse_args()
    
    if args.command == "scrape":
        scrape_videos(db_path=args.db)
    elif args.command == "random":
        mode = "freetube" if args.freetube else "browser"
        cli_random(args.db, args.n, mode)
    elif args.command == "tui":
        mode = "freetube" if args.freetube else "browser"
        cli_tui(args.db, mode)
    else:
        # GUI mode
        win = GGWindow()
        win.show_all()
        Gtk.main()


if __name__ == "__main__":
    main()
