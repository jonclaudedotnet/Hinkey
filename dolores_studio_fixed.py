#!/usr/bin/env python3
"""
Dolores Studio - FIXED VERSION - Should display all responses
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Pango, Gdk
import json
import sqlite3
import threading
import time
from pathlib import Path
from datetime import datetime

class DoloresStudioFixed(Gtk.Window):
    def __init__(self):
        super().__init__(title="Dolores Studio - FIXED")
        self.set_default_size(1400, 900)
        self.maximize()
        
        # Initialize systems
        self.bridge_dir = Path("./claude_dolores_bridge")
        self.task_db = self.bridge_dir / "shared_tasks.db"
        
        # Track from current session
        self.session_start_id = self._get_latest_task_id()
        print(f"Studio starting - will show tasks after ID {self.session_start_id}")
        
        # Build interface
        self.setup_ui()
        
        # Start monitoring
        self.start_monitoring()
        
    def _get_latest_task_id(self):
        """Get the latest task ID to start fresh"""
        if not self.task_db.exists():
            return 0
            
        try:
            conn = sqlite3.connect(self.task_db)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM tasks")
            result = cursor.fetchone()[0]
            conn.close()
            return result or 0
        except:
            return 0
    
    def setup_ui(self):
        """Create the interface"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_box)
        
        # Header
        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.props.title = "🎙️ Dolores Studio - FIXED"
        header.props.subtitle = f"Monitoring from task #{self.session_start_id + 1}"
        self.set_titlebar(header)
        
        # Text area
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD)
        
        font_desc = Pango.FontDescription.from_string("Liberation Mono 11")
        self.textview.override_font(font_desc)
        
        self.buffer = self.textview.get_buffer()
        self.buffer.set_text("🎙️ DOLORES STUDIO FIXED - Waiting for responses...\n\n")
        
        scrolled.add(self.textview)
        main_box.pack_start(scrolled, True, True, 0)
        
        # Status bar
        self.statusbar = Gtk.Statusbar()
        context_id = self.statusbar.get_context_id("main")
        self.statusbar.push(context_id, f"Monitoring tasks after #{self.session_start_id}")
        main_box.pack_start(self.statusbar, False, False, 0)
    
    def get_new_tasks(self):
        """Get tasks newer than our session start"""
        if not self.task_db.exists():
            return []
            
        try:
            conn = sqlite3.connect(self.task_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, timestamp, requester, task_type, content, context, status, result, tokens_used
                FROM tasks 
                WHERE id > ?
                ORDER BY id ASC
            ''', (self.session_start_id,))
            
            tasks = []
            for row in cursor.fetchall():
                tasks.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'requester': row[2],
                    'task_type': row[3],
                    'content': row[4],
                    'context': row[5],
                    'status': row[6],
                    'result': row[7],
                    'tokens_used': row[8]
                })
            
            conn.close()
            return tasks
        except Exception as e:
            print(f"Database error: {e}")
            return []
    
    def update_display(self):
        """Update the display with new tasks"""
        tasks = self.get_new_tasks()
        
        if tasks:
            current_text = self.buffer.get_text(
                self.buffer.get_start_iter(),
                self.buffer.get_end_iter(),
                False
            )
            
            for task in tasks:
                task_marker = f"TASK #{task['id']}"
                if task_marker not in current_text:
                    # Add new task
                    task_display = f"\n{'='*80}\n"
                    task_display += f"{task_marker} - {task['timestamp']}\n"
                    task_display += f"Type: {task['task_type']} | Status: {task['status']}\n"
                    task_display += f"Context: {task.get('context', 'None')}\n"
                    task_display += "-" * 80 + "\n"
                    
                    if task['content']:
                        task_display += f"REQUEST:\n{task['content']}\n\n"
                    
                    if task['result']:
                        task_display += f"DOLORES RESPONDS:\n{task['result']}\n"
                        if task['tokens_used']:
                            task_display += f"\n🪙 DeepSeek tokens: {task['tokens_used']}\n"
                    else:
                        task_display += "⏳ Still processing...\n"
                    
                    task_display += "=" * 80 + "\n"
                    
                    current_text += task_display
                    print(f"Added task #{task['id']} to display")
            
            # Update buffer
            self.buffer.set_text(current_text)
            
            # Auto-scroll to bottom
            mark = self.buffer.get_insert()
            self.textview.scroll_mark_onscreen(mark)
            
            # Update status
            context_id = self.statusbar.get_context_id("main")
            self.statusbar.pop(context_id)
            self.statusbar.push(context_id, f"Showing {len(tasks)} conversations")
        
        return True  # Continue monitoring
    
    def start_monitoring(self):
        """Start monitoring for new tasks"""
        def monitor_loop():
            while True:
                GLib.idle_add(self.update_display)
                time.sleep(2)  # Check every 2 seconds
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()

def main():
    app = DoloresStudioFixed()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    
    print("🎙️ Dolores Studio FIXED - Now monitoring for responses")
    Gtk.main()

if __name__ == "__main__":
    main()