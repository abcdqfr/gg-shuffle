#!/usr/bin/env python3
"""Minimal GTK GUI to shuffle and open Game Grumps videos (K.I.S.S.)."""

import hashlib
import sqlite3
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


def fetch_random(conn: sqlite3.Connection) -> Tuple[str, str]:
    cur = conn.cursor()
    cur.execute("SELECT title, url FROM videos ORDER BY RANDOM() LIMIT 1")
    row = cur.fetchone()
    return (row[0], row[1]) if row else ("", "")


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
        print("DEBUG: _build_main_ui called!")  # Debug log
        try:
            # Clean up any existing main UI to prevent duplicate stack children
            existing_main = self.content_stack.get_child_by_name("main")
            if existing_main:
                print("DEBUG: Removing existing main UI")  # Debug log
                self.content_stack.remove(existing_main)
            
            print("DEBUG: Setting up database connection...")  # Debug log
            # Ensure we have a fresh database connection
            if self.conn:
                self.conn.close()
            self.conn = sqlite3.connect(str(DB_PATH))
            # Test the connection
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM videos")
            count = cursor.fetchone()[0]
            print(f"DEBUG: Database has {count} videos")  # Debug log
            self._set_status(f"Connected - {count:,} videos available")
        except sqlite3.Error as e:
            print(f"DEBUG: Database error: {e}")  # Debug log
            self._set_status(f"Database error: {e}")
            return
        except Exception as e:
            print(f"DEBUG: Unexpected error in database setup: {e}")  # Debug log
            self._set_status(f"Setup error: {e}")
            return
        
        print("DEBUG: Creating main UI components...")  # Debug log
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

        # Title label (selectable, wrapped)
        self.title_lbl = Gtk.Label()
        self.title_lbl.set_xalign(0.0)
        self.title_lbl.set_line_wrap(True)
        self.title_lbl.set_selectable(True)
        self.title_lbl.get_style_context().add_class("gg-title")
        details.pack_start(self.title_lbl, False, False, 0)

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

        print("DEBUG: Adding main UI to stack...")  # Debug log
        # Add to stack
        self.content_stack.add_named(main_box, "main")
        self.content_stack.set_visible_child_name("main")
        print("DEBUG: Main UI added to stack successfully")  # Debug log
        
        # Force UI refresh
        print("DEBUG: Forcing UI refresh...")  # Debug log
        self.content_stack.show_all()
        self.show_all()
        print(f"DEBUG: Current visible child: {self.content_stack.get_visible_child_name()}")  # Debug log

        print("DEBUG: Setting up keyboard shortcuts...")  # Debug log
        # Keyboard shortcuts
        self.shuffle_btn.set_can_default(True)
        self.set_default(self.shuffle_btn)
        self.connect("key-press-event", self.on_key_press)

        print("DEBUG: Loading initial random video...")  # Debug log
        # Initial load
        self.enable_actions()
        self.load_random()
        print("DEBUG: _build_main_ui completed successfully!")  # Debug log

    def _apply_css(self) -> None:
        css = b"""
        window, .background { background-color: #1e1f22; }
        label { color: #e6e8eb; }
        entry { color: #e6e8eb; background: #2b2d31; border-radius: 6px; border: 1px solid #3a3d42; }
        button { background: #2b2d31; color: #e6e8eb; border: 1px solid #3a3d42; border-radius: 6px; padding: 6px 10px; }
        button:hover { background: #34373c; }
        .suggested-action { background: #007acc; border-color: #007acc; }
        .suggested-action:hover { background: #0085d1; }
        .gg-title { font-weight: 600; font-size: 16px; }
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
        self.welcome_progress.set_text("Starting database build...")
        self._set_status("Building database - this may take a few minutes...")
        
        def build_worker():
            try:
                import subprocess
                
                # Run gg.sh scrape
                script_path = Path(__file__).parent / "gg.sh"
                if not script_path.exists():
                    GLib.idle_add(self._on_build_error, "gg.sh script not found")
                    return
                
                # Update progress
                GLib.idle_add(self.welcome_progress.set_text, "Downloading video list...")
                GLib.idle_add(self.welcome_progress.pulse)
                
                result = subprocess.run(
                    [str(script_path), "scrape"],
                    cwd=str(script_path.parent),
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode == 0:
                    GLib.idle_add(self._on_build_complete)
                else:
                    GLib.idle_add(self._on_build_error, f"Build failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                GLib.idle_add(self._on_build_error, "Build timed out after 5 minutes")
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
        self._set_status("Database build complete - ready to continue!")
        
        # Transform the build button into a continue button
        self.build_db_button.set_label("✅ READY!")
        self.build_db_button.set_sensitive(True)
        
        # Disconnect the old build handler and connect the continue handler
        self.build_db_button.disconnect_by_func(self._on_build_database)
        self.build_db_button.connect("clicked", self._on_continue_to_app)
        
        self.build_db_button.get_style_context().add_class("suggested-action")
        self.build_db_button.set_can_default(True)
        self.set_default(self.build_db_button)
        
        # Make button larger
        self.build_db_button.set_size_request(200, 50)
        
        # Auto-switch after 5 seconds
        GLib.timeout_add_seconds(5, self._auto_continue_to_app)
        
        # Reconnect to database for when we switch
        try:
            self.conn = sqlite3.connect(str(DB_PATH))
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM videos")
            count = cursor.fetchone()[0]
            self._set_status(f"Ready - {count:,} videos in database")
            
        except sqlite3.Error as e:
            self._on_build_error(f"Database connection error: {e}")

    def _on_continue_to_app(self, _widget: Gtk.Widget) -> None:
        """Manually continue to main app."""
        print("DEBUG: _on_continue_to_app called!")  # Debug log
        self._set_status("Switching to main app...")
        
        # TEMPORARY: Skip database and just test UI switching
        print("DEBUG: TEMPORARY - Skipping database, testing UI switch only")
        self._test_ui_switch()

    def _test_ui_switch(self) -> None:
        """TEMPORARY: Test UI switching without database."""
        print("DEBUG: _test_ui_switch called")
        
        # Clean up any existing main UI
        existing_main = self.content_stack.get_child_by_name("main")
        if existing_main:
            print("DEBUG: Removing existing main UI")
            self.content_stack.remove(existing_main)
        
        # Create a simple test main UI
        print("DEBUG: Creating simple test main UI")
        test_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        test_box.set_halign(Gtk.Align.CENTER)
        test_box.set_valign(Gtk.Align.CENTER)
        
        # Add a test label
        test_label = Gtk.Label()
        test_label.set_markup("<big><b>MAIN UI TEST</b></big>")
        test_label.get_style_context().add_class("gg-title")
        test_box.pack_start(test_label, False, False, 0)
        
        # Add a test button
        test_btn = Gtk.Button.new_with_mnemonic("_Test Button")
        test_btn.connect("clicked", lambda _w: print("DEBUG: Test button clicked!"))
        test_box.pack_start(test_btn, False, False, 0)
        
        # Add to stack
        print("DEBUG: Adding test UI to stack")
        self.content_stack.add_named(test_box, "main")
        
        # Try different switching methods
        print("DEBUG: Attempting stack switch...")
        self.content_stack.set_visible_child_name("main")
        print(f"DEBUG: After set_visible_child_name: {self.content_stack.get_visible_child_name()}")
        
        # Force refresh
        print("DEBUG: Forcing UI refresh")
        self.content_stack.show_all()
        self.show_all()
        
        # Try direct child switching
        print("DEBUG: Trying direct child switching...")
        self.content_stack.set_visible_child(test_box)
        print(f"DEBUG: After set_visible_child: {self.content_stack.get_visible_child_name()}")
        
        print("DEBUG: _test_ui_switch completed")
        
        # Additional debugging - check stack properties
        print(f"DEBUG: Stack has {len(self.content_stack.get_children())} children")
        for i, child in enumerate(self.content_stack.get_children()):
            name = self.content_stack.child_get_property(child, "name")
            print(f"DEBUG: Child {i}: name='{name}'")
        
        # Try to force the window to update
        print("DEBUG: Forcing window update...")
        self.queue_draw()
        GLib.idle_add(self.queue_draw)

    def _auto_continue_to_app(self) -> bool:
        """Auto-continue to main app after delay."""
        if self.content_stack.get_visible_child_name() == "welcome":
            self._test_ui_switch()  # Use test function instead
        return False  # Don't repeat

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
                import subprocess
                script_path = Path(__file__).parent / "gg.sh"
                
                result = subprocess.run(
                    [str(script_path), "scrape"],
                    cwd=str(script_path.parent),
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    GLib.idle_add(self._on_update_complete)
                else:
                    GLib.idle_add(self._on_update_error, f"Update failed: {result.stderr}")
                    
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
        for b in (self.shuffle_btn, self.browser_btn, self.freetube_btn, self.copy_btn):
            b.set_sensitive(True)

    # Core actions
    def load_random(self) -> None:
        print("DEBUG: load_random called")  # Debug log
        if not self.conn:
            print("DEBUG: No database connection")  # Debug log
            return
        try:
            print("DEBUG: Fetching random video...")  # Debug log
            title, url = fetch_random(self.conn)
            print(f"DEBUG: Got video - Title: {title[:50]}...")  # Debug log
            self.current_url = url
            vid = extract_video_id(url)
            ft = f"freetube://{url}" if url else ""
            self.title_lbl.set_text(title or "(No title)")
            self.url_entry.set_text(url or "")
            self.id_entry.set_text(vid)
            self.ft_entry.set_text(ft)
            
            print("DEBUG: Setting loading placeholder...")  # Debug log
            # Show loading placeholder while loading thumbnail async
            self._set_loading_placeholder()
            load_thumbnail_async(vid, self._on_thumbnail_loaded)
            
            # Focus URL for quick copy
            self.url_entry.select_region(0, -1)
            self.url_entry.grab_focus()
            print("DEBUG: load_random completed successfully")  # Debug log
        except Exception as e:
            print(f"DEBUG: Error in load_random: {e}")  # Debug log
            import traceback
            traceback.print_exc()

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


def main() -> None:
    win = GGWindow()
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
