#!/usr/bin/env python3
"""
Dolores GTK Viewer - Native Linux desktop window for DeepSeek responses
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Pango
import json
import sqlite3
import threading
import time
from pathlib import Path

class DoloresViewer(Gtk.Window):
    def __init__(self):
        super().__init__(title="Dolores DeepSeek Response Viewer")
        self.set_default_size(1000, 700)
        
        # Database setup
        self.bridge_dir = Path("./claude_dolores_bridge")
        self.task_db = self.bridge_dir / "shared_tasks.db"
        self.last_seen_task = 0
        
        self.setup_ui()
        self.start_monitoring()
    
    def setup_ui(self):
        # Create main container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)
        
        # Header
        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.props.title = "Dolores Viewer"
        header.props.subtitle = "Real-time DeepSeek Response Monitor"
        self.set_titlebar(header)
        
        # Scrolled window for tasks
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        vbox.pack_start(scrolled, True, True, 0)
        
        # Text view with monospace font
        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD)
        
        # Set monospace font
        font_desc = Pango.FontDescription.from_string("Monospace 10")
        self.textview.override_font(font_desc)
        
        # Dark theme colors
        style_context = self.textview.get_style_context()
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
        textview {
            background-color: #1a1a1a;
            color: #00ff00;
        }
        """)
        style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        self.buffer = self.textview.get_buffer()
        scrolled.add(self.textview)
        
        # Status bar
        self.statusbar = Gtk.Statusbar()
        context_id = self.statusbar.get_context_id("status")
        self.statusbar.push(context_id, "Monitoring Dolores activity...")
        vbox.pack_start(self.statusbar, False, False, 0)
        
        # Initial text
        self.buffer.set_text("🔍 DOLORES VIEWER - Real-time DeepSeek Response Monitor\n" + "="*80 + "\nWaiting for Dolores activity...\n\n")
    
    def get_latest_tasks(self):
        """Get all tasks since last check"""
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
            ''', (self.last_seen_task,))
            
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
                
            if tasks:
                self.last_seen_task = tasks[-1]['id']
                
            conn.close()
            return tasks
        except Exception as e:
            print(f"Database error: {e}")
            return []
    
    def format_task_display(self, task):
        """Format a task for display"""
        lines = []
        lines.append("=" * 80)
        lines.append(f"TASK #{task['id']} - {task['timestamp']}")
        lines.append(f"Type: {task['task_type']} | Requester: {task['requester']} | Status: {task['status']}")
        lines.append("-" * 80)
        
        if task['context']:
            lines.append(f"Context: {task['context']}")
            lines.append("")
        
        lines.append("REQUEST:")
        lines.append(task['content'])
        lines.append("")
        
        if task['result']:
            lines.append("DOLORES'S DEEPSEEK RESPONSE:")
            lines.append(task['result'])
            lines.append("")
            
            if task['tokens_used']:
                lines.append(f"DeepSeek Tokens Used: {task['tokens_used']}")
        else:
            lines.append("Status: ⏳ Processing...")
            
        lines.append("=" * 80)
        lines.append("")
        
        return "\n".join(lines)
    
    def update_display(self):
        """Update the display with new tasks"""
        tasks = self.get_latest_tasks()
        
        if tasks:
            # Get current text
            start_iter = self.buffer.get_start_iter()
            end_iter = self.buffer.get_end_iter()
            current_text = self.buffer.get_text(start_iter, end_iter, False)
            
            # Append new tasks
            for task in tasks:
                task_text = self.format_task_display(task)
                current_text += task_text
                
                # Update status bar
                context_id = self.statusbar.get_context_id("status")
                self.statusbar.pop(context_id)
                status_msg = f"Latest: Task #{task['id']} ({task['status']})"
                if task['tokens_used']:
                    status_msg += f" - {task['tokens_used']} DeepSeek tokens"
                self.statusbar.push(context_id, status_msg)
            
            # Update buffer
            self.buffer.set_text(current_text)
            
            # Auto-scroll to bottom
            mark = self.buffer.get_insert()
            self.textview.scroll_mark_onscreen(mark)
        
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
    app = DoloresViewer()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    
    print("🖥️ Dolores GTK Viewer started")
    print("Close the window to exit")
    
    Gtk.main()

if __name__ == "__main__":
    main()