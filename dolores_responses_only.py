#!/usr/bin/env python3
"""
Dolores Response Stream - Shows ONLY her responses, nothing else
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Pango
import sqlite3
import threading
import time
from pathlib import Path

class DoloresResponseStream(Gtk.Window):
    def __init__(self):
        super().__init__(title="🎙️ Dolores Learning Stream")
        self.set_default_size(800, 600)
        
        # Database and tracking
        self.db_path = Path("./claude_dolores_bridge/shared_tasks.db")
        self.last_seen_id = 0
        
        # Setup UI
        self.setup_ui()
        
        # Start monitoring
        self.start_monitoring()
    
    def setup_ui(self):
        """Simple scrolling text window"""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(vbox)
        
        # Header
        header = Gtk.Label()
        header.set_markup("<big><b>🎙️ Dolores Learning Stream</b></big>")
        vbox.pack_start(header, False, False, 10)
        
        # Scrolled text area
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD)
        self.textview.set_cursor_visible(False)
        
        # Font and styling
        font = Pango.FontDescription.from_string("Liberation Sans 11")
        self.textview.override_font(font)
        
        self.buffer = self.textview.get_buffer()
        self.buffer.set_text("🎙️ Dolores is learning...\n\n")
        
        scrolled.add(self.textview)
        vbox.pack_start(scrolled, True, True, 0)
        
        # Status
        self.status = Gtk.Label(label="Monitoring for responses...")
        vbox.pack_start(self.status, False, False, 5)
    
    def get_new_responses(self):
        """Get only new responses from database"""
        if not self.db_path.exists():
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, result FROM tasks 
                WHERE id > ? AND result IS NOT NULL AND result != ''
                ORDER BY id ASC
            ''', (self.last_seen_id,))
            
            responses = cursor.fetchall()
            conn.close()
            
            if responses:
                self.last_seen_id = responses[-1][0]
            
            return responses
            
        except Exception as e:
            print(f"Database error: {e}")
            return []
    
    def add_response(self, response_text):
        """Add a new response to the stream"""
        current_text = self.buffer.get_text(
            self.buffer.get_start_iter(),
            self.buffer.get_end_iter(),
            False
        )
        
        # Add separator and response
        new_text = current_text + "-" * 60 + "\n"
        new_text += response_text + "\n\n"
        
        self.buffer.set_text(new_text)
        
        # Auto-scroll to bottom
        end_iter = self.buffer.get_end_iter()
        mark = self.buffer.get_insert()
        self.buffer.place_cursor(end_iter)
        self.textview.scroll_mark_onscreen(mark)
    
    def update_display(self):
        """Check for new responses and display them"""
        responses = self.get_new_responses()
        
        for response_id, response_text in responses:
            if response_text:
                self.add_response(response_text)
                print(f"Added response #{response_id}")
        
        if responses:
            self.status.set_text(f"Latest response: #{responses[-1][0]}")
        
        return True  # Continue monitoring
    
    def start_monitoring(self):
        """Start monitoring for new responses"""
        # Update every 2 seconds
        GLib.timeout_add(2000, self.update_display)

def main():
    app = DoloresResponseStream()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    
    print("🎙️ Dolores Response Stream started")
    print("Showing ONLY her responses as she learns")
    
    Gtk.main()

if __name__ == "__main__":
    main()