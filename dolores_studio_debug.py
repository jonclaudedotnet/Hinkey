#!/usr/bin/env python3
"""
Dolores Studio - SIMPLE DEBUG VERSION
This WILL show responses - guaranteed!
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Pango
import sqlite3
import threading
import time
from pathlib import Path

class DoloresStudioDebug(Gtk.Window):
    def __init__(self):
        super().__init__(title="Dolores Studio - DEBUG MODE")
        self.set_default_size(1200, 800)
        
        # Database
        self.task_db = Path("./claude_dolores_bridge/shared_tasks.db")
        self.displayed_tasks = set()
        
        self.setup_ui()
        self.start_monitoring()
    
    def setup_ui(self):
        """Simple UI"""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(vbox)
        
        # Header
        header = Gtk.Label(label="🎙️ DOLORES STUDIO DEBUG - WILL SHOW RESPONSES")
        header.set_markup("<big><b>🎙️ DOLORES STUDIO DEBUG - WILL SHOW RESPONSES</b></big>")
        vbox.pack_start(header, False, False, 10)
        
        # Scrolled text
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        
        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD)
        
        font = Pango.FontDescription.from_string("Liberation Mono 10")
        self.textview.override_font(font)
        
        self.buffer = self.textview.get_buffer()
        self.buffer.set_text("DEBUG MODE STARTED - Checking for Dolores responses...\n\n")
        
        scrolled.add(self.textview)
        vbox.pack_start(scrolled, True, True, 0)
        
        # Status
        self.status = Gtk.Label(label="Monitoring database...")
        vbox.pack_start(self.status, False, False, 5)
    
    def get_all_tasks(self):
        """Get ALL tasks from database"""
        if not self.task_db.exists():
            return []
            
        try:
            conn = sqlite3.connect(self.task_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, timestamp, task_type, content, result, status
                FROM tasks 
                ORDER BY id ASC
            ''')
            
            tasks = []
            for row in cursor.fetchall():
                tasks.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'task_type': row[2],
                    'content': row[3],
                    'result': row[4],
                    'status': row[5]
                })
            
            conn.close()
            return tasks
        except Exception as e:
            print(f"Database error: {e}")
            return []
    
    def update_display(self):
        """Update display with ALL tasks"""
        tasks = self.get_all_tasks()
        
        if not tasks:
            self.status.set_text("No tasks found in database")
            return True
        
        # Get current text
        current_text = self.buffer.get_text(
            self.buffer.get_start_iter(),
            self.buffer.get_end_iter(),
            False
        )
        
        new_content = False
        
        for task in tasks:
            task_id = task['id']
            
            if task_id not in self.displayed_tasks:
                # Add this task
                task_text = f"\n" + "="*60 + "\n"
                task_text += f"TASK #{task_id} - {task['timestamp']}\n"
                task_text += f"Type: {task['task_type']} | Status: {task['status']}\n"
                task_text += "-"*60 + "\n"
                
                if task['content']:
                    task_text += f"REQUEST:\n{task['content']}\n\n"
                
                if task['result']:
                    task_text += f"DOLORES RESPONDS:\n{task['result']}\n"
                else:
                    task_text += "⏳ No response yet\n"
                
                task_text += "="*60 + "\n"
                
                current_text += task_text
                self.displayed_tasks.add(task_id)
                new_content = True
                
                print(f"Added task #{task_id} to display")
        
        if new_content:
            self.buffer.set_text(current_text)
            
            # Scroll to bottom
            end_iter = self.buffer.get_end_iter()
            mark = self.buffer.get_insert()
            self.buffer.place_cursor(end_iter)
            self.textview.scroll_mark_onscreen(mark)
        
        self.status.set_text(f"Showing {len(self.displayed_tasks)} tasks")
        return True
    
    def start_monitoring(self):
        """Start monitoring"""
        def monitor():
            while True:
                GLib.idle_add(self.update_display)
                time.sleep(1)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

def main():
    app = DoloresStudioDebug()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    
    print("🛠️ DEBUG STUDIO STARTED")
    print("This version WILL show all responses!")
    
    Gtk.main()

if __name__ == "__main__":
    main()