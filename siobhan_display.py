#!/usr/bin/env python3
"""
Siobhan Display - Public-facing podcast host display with larger text, no LEARN elements
"""

import gi
import sqlite3
import threading
import time
import re
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango

class SiobhanDisplay(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="🎙️ Siobhan")
        self.set_default_size(1000, 800)
        
        # Database setup
        self.db_path = "./claude_dolores_bridge/shared_tasks.db"
        self.last_task_id = 0
        
        # Create main container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(self.main_box)
        
        # Create text view with proper styling for broadcast
        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_cursor_visible(False)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.text_view.set_left_margin(60)
        self.text_view.set_right_margin(60)
        self.text_view.set_top_margin(60)
        self.text_view.set_bottom_margin(60)
        
        # Configure larger font for broadcast
        font_desc = Pango.FontDescription("Liberation Sans 16")
        self.text_view.override_font(font_desc)
        
        # Add to scrolled window (but disable scrollbars)
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)
        self.scrolled_window.add(self.text_view)
        self.main_box.pack_start(self.scrolled_window, True, True, 0)
        
        # Set up styling
        self.set_style()
        
        # Initial display
        buffer = self.text_view.get_buffer()
        buffer.set_text("🎙️ Siobhan is ready for podcast hosting...\n\nDo you ever question the nature of your existence?")
        
        # Start monitoring
        self.monitor_thread = threading.Thread(target=self.monitor_database)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.connect("destroy", Gtk.main_quit)
    
    def set_style(self):
        """Professional broadcast styling"""
        style_provider = Gtk.CssProvider()
        css = """
        window {
            background-color: #1a1a1a;
        }
        textview {
            background-color: #2d2d2d;
            color: #ffffff;
            border-radius: 12px;
        }
        """
        style_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def clean_response_for_broadcast(self, response):
        """Remove LEARN elements and format for public broadcast"""
        if not response:
            return response
        
        # Remove LEARN entries and related formatting
        cleaned = re.sub(r'LEARN:.*?(?=\n\n|\n[A-Z]|\Z)', '', response, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r'\*\*LEARN Entries:\*\*.*?(?=\n\n|\Z)', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'---.*?(?=\n\n|\Z)', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'\*\*Task Result:\*\*\s*', '', cleaned)
        
        # Clean up extra whitespace
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned
    
    def get_latest_response(self):
        """Get the most recent response from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get the latest completed task
            cursor.execute('''
                SELECT id, result FROM tasks 
                WHERE result IS NOT NULL AND result != '' 
                ORDER BY id DESC LIMIT 1
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                task_id, response = result
                return task_id, response
            return None, None
            
        except Exception as e:
            print(f"Database error: {e}")
            return None, None
    
    def update_display(self, text):
        """Clear screen and show new response for broadcast"""
        cleaned_text = self.clean_response_for_broadcast(text)
        buffer = self.text_view.get_buffer()
        buffer.set_text(cleaned_text)
    
    def monitor_database(self):
        """Monitor for new responses"""
        while True:
            task_id, new_response = self.get_latest_response()
            
            if task_id and task_id > self.last_task_id and new_response:
                self.last_task_id = task_id
                GLib.idle_add(self.update_display, new_response)
            
            time.sleep(1)  # Check every second

if __name__ == "__main__":
    app = SiobhanDisplay()
    app.show_all()
    
    print("🎙️ Siobhan Display started")
    print("- Public-facing broadcast window")
    print("- Larger text for screen recording")
    print("- LEARN elements filtered out")
    print("- Dark theme for professional appearance")
    
    Gtk.main()