#!/usr/bin/env python3
"""
Clean Dolores Display - Clear screen per message, proper margins, no scrollbars
"""

import gi
import sqlite3
import threading
import time
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango

class DoloresCleanDisplay(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="🎙️ Dolores Learning")
        self.set_default_size(900, 700)
        
        # Database setup
        self.db_path = "./claude_dolores_bridge/shared_tasks.db"
        self.last_task_id = 0
        
        # Create main container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(self.main_box)
        
        # Create text view with proper styling
        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_cursor_visible(False)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.text_view.set_left_margin(50)
        self.text_view.set_right_margin(50)
        self.text_view.set_top_margin(50)
        self.text_view.set_bottom_margin(50)
        
        # Configure font
        font_desc = Pango.FontDescription("Liberation Sans 13")
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
        buffer.set_text("🎙️ Dolores is ready to learn...\n\nWaiting for your first message.")
        
        # Start monitoring
        self.monitor_thread = threading.Thread(target=self.monitor_database)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.connect("destroy", Gtk.main_quit)
    
    def set_style(self):
        """Professional styling"""
        style_provider = Gtk.CssProvider()
        css = """
        window {
            background-color:  #f5f5f5;
        }
        textview {
            background-color: #ffffff;
            color: #2c2c2c;
            border-radius: 8px;
        }
        """
        style_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
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
        """Clear screen and show new response"""
        buffer = self.text_view.get_buffer()
        buffer.set_text(text)
    
    def monitor_database(self):
        """Monitor for new responses"""
        while True:
            task_id, new_response = self.get_latest_response()
            
            if task_id and task_id > self.last_task_id and new_response:
                self.last_task_id = task_id
                GLib.idle_add(self.update_display, new_response)
            
            time.sleep(1)  # Check every second

if __name__ == "__main__":
    app = DoloresCleanDisplay()
    app.show_all()
    
    print("🎙️ Clean Dolores Display started")
    print("- Clears screen with each new message")
    print("- No scroll bars")  
    print("- Proper margins and typography")
    
    Gtk.main()