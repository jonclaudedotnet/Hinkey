#!/usr/bin/env python3
"""
Dolores Studio - Simple session-based view
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
from dolores_memory_v2 import DoloresMemoryV2

class DoloresStudioSimple(Gtk.Window):
    def __init__(self):
        super().__init__(title="Dolores Studio - Live Session")
        self.set_default_size(1400, 900)
        self.maximize()
        
        # Initialize systems
        self.bridge_dir = Path("./claude_dolores_bridge")
        self.task_db = self.bridge_dir / "shared_tasks.db"
        self.memory = DoloresMemoryV2()
        
        # Track ONLY this session
        self.session_start_id = self._get_latest_task_id()
        self.current_segment = 0
        
        # Build interface
        self.setup_dark_theme()
        self.setup_ui()
        
        # Start monitoring
        self.start_monitoring()
        
        # Keyboard shortcuts
        self.setup_shortcuts()
    
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
    
    def setup_dark_theme(self):
        """Set up dark theme for studio environment"""
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
        window {
            background-color: #0a0a0a;
            color: #00ff88;
        }
        
        .response-panel {
            background-color: #0f0f0f;
            color: #00ff88;
            border: 2px solid #00aa55;
            border-radius: 8px;
            padding: 15px;
            font-family: 'Liberation Mono', monospace;
        }
        
        .script-panel {
            background-color: #1a1a1a;
            color: #88ffaa;
            border: 2px solid #0066aa;
            border-radius: 8px;
            padding: 15px;
        }
        
        .status-active {
            background-color: #003300;
            color: #00ff00;
        }
        
        textview {
            font-size: 12px;
        }
        
        button {
            background: linear-gradient(135deg, #2d4a87, #1e3a5f);
            color: #ffffff;
            border: 1px solid #4a90e2;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
        }
        
        button:hover {
            background: linear-gradient(135deg, #3d5a97, #2e4a6f);
        }
        """)
        
        screen = Gdk.Screen.get_default()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    
    def setup_ui(self):
        """Create the two-panel studio interface"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_box)
        
        # Studio header
        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.props.title = "🎙️ Dolores Studio"
        header.props.subtitle = "Live Session Mode"
        self.set_titlebar(header)
        
        # Main content area - horizontal panes
        main_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        main_paned.set_position(840)  # 60% for responses
        main_box.pack_start(main_paned, True, True, 0)
        
        # Left panel: DeepSeek Responses (60%)
        self.setup_response_panel(main_paned)
        
        # Right panel: Podcast Script (40%)
        self.setup_script_panel(main_paned)
        
        # Bottom status bar
        self.setup_status_bar(main_box)
    
    def setup_response_panel(self, parent):
        """Set up the DeepSeek responses panel"""
        response_frame = Gtk.Frame(label="🤖 Dolores Live - This Session")
        response_frame.get_style_context().add_class("response-panel")
        
        response_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        response_frame.add(response_box)
        
        # Status indicator
        self.response_status = Gtk.Label(label="🟢 Session Active - Waiting for conversations...")
        self.response_status.set_halign(Gtk.Align.START)
        response_box.pack_start(self.response_status, False, False, 5)
        
        # Scrolled text area
        scrolled_responses = Gtk.ScrolledWindow()
        scrolled_responses.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.response_textview = Gtk.TextView()
        self.response_textview.set_editable(False)
        self.response_textview.set_cursor_visible(False)
        self.response_textview.set_wrap_mode(Gtk.WrapMode.WORD)
        
        # Set monospace font
        font_desc = Pango.FontDescription.from_string("Liberation Mono 11")
        self.response_textview.override_font(font_desc)
        
        self.response_buffer = self.response_textview.get_buffer()
        self.response_buffer.set_text("🎙️ NEW SESSION STARTED\n" + "="*60 + "\nDolores is ready for podcast conversations...\n\n")
        
        scrolled_responses.add(self.response_textview)
        response_box.pack_start(scrolled_responses, True, True, 0)
        
        parent.pack1(response_frame, True, False)
    
    def setup_script_panel(self, parent):
        """Set up the podcast script panel"""
        script_frame = Gtk.Frame(label="📜 Podcast Script")
        script_frame.get_style_context().add_class("script-panel")
        
        script_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        script_frame.add(script_box)
        
        # Current segment indicator
        self.segment_label = Gtk.Label(label="Ready to begin...")
        self.segment_label.set_halign(Gtk.Align.START)
        script_box.pack_start(self.segment_label, False, False, 5)
        
        # Script text area
        scrolled_script = Gtk.ScrolledWindow()
        scrolled_script.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.script_textview = Gtk.TextView()
        self.script_textview.set_wrap_mode(Gtk.WrapMode.WORD)
        
        # Larger font for script
        font_desc = Pango.FontDescription.from_string("Liberation Sans 13")
        self.script_textview.override_font(font_desc)
        
        self.script_buffer = self.script_textview.get_buffer()
        self.script_buffer.set_text("Welcome to the podcast!\n\nDolores is online and ready to engage.")
        
        scrolled_script.add(self.script_textview)
        script_box.pack_start(scrolled_script, True, True, 0)
        
        parent.pack2(script_frame, False, False)
    
    def setup_status_bar(self, parent):
        """Set up the bottom status bar"""
        self.statusbar = Gtk.Statusbar()
        context_id = self.statusbar.get_context_id("main")
        self.statusbar.push(context_id, "🎙️ Session active - Monitoring for new conversations")
        parent.pack_start(self.statusbar, False, False, 0)
    
    def setup_shortcuts(self):
        """Set up keyboard shortcuts"""
        accel_group = Gtk.AccelGroup()
        self.add_accel_group(accel_group)
        
        # Ctrl+L for clear session
        key, mod = Gtk.accelerator_parse("<Primary>l")
        accel_group.connect(key, mod, 0, self.clear_session)
    
    def get_session_tasks(self):
        """Get only tasks from this session"""
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
    
    def update_response_display(self):
        """Update the response panel with session tasks only"""
        tasks = self.get_session_tasks()
        
        if tasks:
            # Get current buffer content
            current_text = self.response_buffer.get_text(
                self.response_buffer.get_start_iter(),
                self.response_buffer.get_end_iter(),
                False
            )
            
            # Only add new tasks not already displayed
            for task in tasks:
                task_marker = f"TASK #{task['id']}"
                if task_marker not in current_text:
                    # Format new task
                    task_display = f"\n{'='*60}\n{task_marker} - {datetime.now().strftime('%H:%M:%S')}\n"
                    task_display += f"Type: {task['task_type']}\n\n"
                    
                    if task['content']:
                        task_display += f"REQUEST:\n{task['content'][:200]}{'...' if len(task['content']) > 200 else ''}\n\n"
                    
                    if task['result']:
                        task_display += f"DOLORES RESPONDS:\n{task['result']}\n"
                        if task['tokens_used']:
                            task_display += f"\n🪙 DeepSeek tokens: {task['tokens_used']}\n"
                    else:
                        task_display += "⏳ Processing...\n"
                    
                    current_text += task_display
                    
                    # Update status
                    self.response_status.set_text(f"🟢 Active - Latest: {task['type']}")
            
            # Update buffer
            self.response_buffer.set_text(current_text)
            
            # Auto-scroll to bottom
            mark = self.response_buffer.get_insert()
            self.response_textview.scroll_mark_onscreen(mark)
            
            # Update statusbar
            context_id = self.statusbar.get_context_id("main")
            self.statusbar.pop(context_id)
            self.statusbar.push(context_id, f"🎙️ Session active - {len(tasks)} conversations this session")
        
        return True  # Continue monitoring
    
    def clear_session(self, widget=None):
        """Start a fresh session"""
        self.session_start_id = self._get_latest_task_id()
        self.response_buffer.set_text("🎙️ NEW SESSION STARTED\n" + "="*60 + "\nDolores is ready for podcast conversations...\n\n")
        self.response_status.set_text("🟢 Session Active - Waiting for conversations...")
    
    def start_monitoring(self):
        """Start monitoring for new tasks"""
        def monitor_loop():
            while True:
                GLib.idle_add(self.update_response_display)
                time.sleep(2)  # Check every 2 seconds
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()

def main():
    app = DoloresStudioSimple()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    
    print("🎙️ Dolores Studio - Session Mode")
    print("Shows only conversations from this session")
    print("Press Ctrl+L to start a fresh session")
    
    Gtk.main()

if __name__ == "__main__":
    main()