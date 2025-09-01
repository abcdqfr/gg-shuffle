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
        self.set_default_size(740, 320)
        self.connect("destroy", Gtk.main_quit)

        # Initialize cache
        init_cache()

        # Prefer dark theme + CSS styling
        settings = Gtk.Settings.get_default()
        if settings is not None:
            settings.set_property("gtk-application-prefer-dark-theme", True)
        self._apply_css()

        # DB
        self.conn = sqlite3.connect(str(DB_PATH)) if DB_PATH.exists() else None
        self.current_title: str = ""
        self.current_url: str = ""
        self.current_video_id: str = ""

        # Root layout
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        root.set_border_width(12)
        self.add(root)

        # Content row: thumbnail | details
        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        root.pack_start(content, True, True, 0)

        # Thumbnail
        self.thumb = Gtk.Image()
        thumb_frame = Gtk.Frame()
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
        root.pack_start(btns, False, False, 0)

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

        self.exit_btn = Gtk.Button.new_with_mnemonic("E_xit")
        self.exit_btn.connect("clicked", lambda _b: Gtk.main_quit())
        self.exit_btn.set_can_focus(True)
        btns.pack_end(self.exit_btn, False, False, 0)

        # Focus chain for arrow-key navigation
        btns.set_focus_chain([
            self.shuffle_btn,
            self.browser_btn,
            self.freetube_btn,
            self.copy_btn,
            self.exit_btn,
        ])

        # Keyboard shortcuts
        self.shuffle_btn.set_can_default(True)
        self.set_default(self.shuffle_btn)
        self.connect("key-press-event", self.on_key_press)

        # Initial load
        if self.conn is None:
            self.title_lbl.set_text(
                "Database not found. Run './gg.sh scrape' to create gamegrumps.db."
            )
            self.url_entry.set_text("")
            self.id_entry.set_text("")
            self.ft_entry.set_text("")
            self.disable_actions()
        else:
            self.enable_actions()
            self.load_random()

    def _apply_css(self) -> None:
        css = b"""
        window, .background { background-color: #1e1f22; }
        label { color: #e6e8eb; }
        entry { color: #e6e8eb; background: #2b2d31; border-radius: 6px; border: 1px solid #3a3d42; }
        button { background: #2b2d31; color: #e6e8eb; border: 1px solid #3a3d42; border-radius: 6px; padding: 6px 10px; }
        button:hover { background: #34373c; }
        .gg-title { font-weight: 600; font-size: 16px; }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    # Enable/disable buttons based on DB availability
    def disable_actions(self) -> None:
        for b in (self.shuffle_btn, self.browser_btn, self.freetube_btn, self.copy_btn):
            b.set_sensitive(False)

    def enable_actions(self) -> None:
        for b in (self.shuffle_btn, self.browser_btn, self.freetube_btn, self.copy_btn):
            b.set_sensitive(True)

    # Core actions
    def load_random(self) -> None:
        if not self.conn:
            return
        title, url = fetch_random(self.conn)
        self.current_title, self.current_url = title, url
        vid = extract_video_id(url)
        self.current_video_id = vid
        ft = f"freetube://{url}" if url else ""
        self.title_lbl.set_text(title or "(No title)")
        self.url_entry.set_text(url or "")
        self.id_entry.set_text(vid)
        self.ft_entry.set_text(ft)
        
        # Clear thumbnail first, then load async
        self.thumb.clear()
        load_thumbnail_async(vid, self._on_thumbnail_loaded)
        
        # Focus URL for quick copy
        self.url_entry.select_region(0, -1)
        self.url_entry.grab_focus()

    def _on_thumbnail_loaded(self, pixbuf: Optional[GdkPixbuf.Pixbuf]) -> None:
        """Callback when thumbnail is loaded (from cache or download)."""
        if pixbuf is not None:
            self.thumb.set_from_pixbuf(pixbuf)
        # If pixbuf is None, thumbnail stays cleared (no placeholder needed)

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
