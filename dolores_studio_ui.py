#!/usr/bin/env python3
"""
Dolores Studio UI - Professional two-panel interface for podcast production
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Pango, Gdk
import json
import sqlite3
import threading
import time
from pathlib import Path
from dolores_memory_v2 import DoloresMemoryV2

class DoloresStudioUI(Gtk.Window):
    def __init__(self):
        super().__init__(title="Dolores Studio - Podcast Control Center")
        self.set_default_size(1400, 900)
        self.maximize()  # Start maximized for studio mode
        
        # Initialize systems
        self.bridge_dir = Path("./claude_dolores_bridge")
        self.task_db = self.bridge_dir / "shared_tasks.db"
        self.memory = DoloresMemoryV2()
        self.last_seen_task = 0
        self.current_segment = 0
        
        # Load dark studio theme
        self.setup_dark_theme()
        
        # Build the interface
        self.setup_ui()
        
        # Start monitoring
        self.start_monitoring()
        
        # Keyboard shortcuts
        self.setup_shortcuts()
    
    def setup_dark_theme(self):
        """Set up dark theme for studio environment"""
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
        window {
            background-color: #0a0a0a;
            color: #00ff88;
        }
        
        .studio-header {
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            color: #00ff88;
            font-weight: bold;
            padding: 10px;
            border-radius: 8px;
            margin: 5px;
            box-shadow: 0 2px 10px rgba(0,255,136,0.2);
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
            animation: pulse 2s infinite;
        }
        
        .segment-current {
            background-color: #003366;
            color: #66aaff;
            font-weight: bold;
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
            box-shadow: 0 2px 8px rgba(74,144,226,0.3);
        }
        
        @keyframes pulse {
            0% { opacity: 1.0; }
            50% { opacity: 0.7; }
            100% { opacity: 1.0; }
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
        header.props.subtitle = "AI Podcast Production Center"
        header.get_style_context().add_class("studio-header")
        self.set_titlebar(header)
        
        # Control buttons in header
        self.add_header_controls(header)
        
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
    
    def add_header_controls(self, header):
        """Add control buttons to header"""
        # Next segment button
        next_btn = Gtk.Button(label="Next Segment")
        next_btn.connect("clicked", self.next_segment)
        header.pack_start(next_btn)
        
        # Clear responses button
        clear_btn = Gtk.Button(label="Clear Responses")
        clear_btn.connect("clicked", self.clear_responses)
        header.pack_start(clear_btn)
        
        # Memory stats button
        stats_btn = Gtk.Button(label="Memory Stats")
        stats_btn.connect("clicked", self.show_memory_stats)
        header.pack_end(stats_btn)
    
    def setup_response_panel(self, parent):
        """Set up the DeepSeek responses panel"""
        response_frame = Gtk.Frame(label="🤖 Dolores's DeepSeek Responses")
        response_frame.get_style_context().add_class("response-panel")
        
        response_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        response_frame.add(response_box)
        
        # Status indicator
        self.response_status = Gtk.Label(label="⏳ Waiting for activity...")
        self.response_status.set_halign(Gtk.Align.START)
        response_box.pack_start(self.response_status, False, False, 5)
        
        # Scrolled text area
        scrolled_responses = Gtk.ScrolledWindow()
        scrolled_responses.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_responses.set_min_content_height(400)
        
        self.response_textview = Gtk.TextView()
        self.response_textview.set_editable(False)
        self.response_textview.set_cursor_visible(False)
        self.response_textview.set_wrap_mode(Gtk.WrapMode.WORD)
        
        # Set monospace font for responses
        font_desc = Pango.FontDescription.from_string("Liberation Mono 11")
        self.response_textview.override_font(font_desc)
        
        self.response_buffer = self.response_textview.get_buffer()
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
        self.segment_label = Gtk.Label(label="Segment 1: Introduction")
        self.segment_label.set_halign(Gtk.Align.START)
        self.segment_label.get_style_context().add_class("segment-current")
        script_box.pack_start(self.segment_label, False, False, 5)
        
        # Script text area
        scrolled_script = Gtk.ScrolledWindow()
        scrolled_script.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.script_textview = Gtk.TextView()
        self.script_textview.set_wrap_mode(Gtk.WrapMode.WORD)
        
        # Larger font for script readability
        font_desc = Pango.FontDescription.from_string("Liberation Sans 13")
        self.script_textview.override_font(font_desc)
        
        self.script_buffer = self.script_textview.get_buffer()
        scrolled_script.add(self.script_textview)
        script_box.pack_start(scrolled_script, True, True, 0)
        
        # Script controls
        script_controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        add_segment_btn = Gtk.Button(label="Add Segment")
        add_segment_btn.connect("clicked", self.add_script_segment)
        script_controls.pack_start(add_segment_btn, False, False, 0)
        
        save_script_btn = Gtk.Button(label="Save Script")
        save_script_btn.connect("clicked", self.save_current_script)
        script_controls.pack_start(save_script_btn, False, False, 0)
        
        script_box.pack_start(script_controls, False, False, 5)
        
        # Load initial script
        self.load_script_segments()
        
        parent.pack2(script_frame, False, False)
    
    def setup_status_bar(self, parent):
        """Set up the bottom status bar"""
        self.statusbar = Gtk.Statusbar()
        self.statusbar.get_style_context().add_class("studio-header")
        
        context_id = self.statusbar.get_context_id("main")
        self.statusbar.push(context_id, "🎙️ Studio ready - Monitoring Dolores activity")
        
        parent.pack_start(self.statusbar, False, False, 0)
    
    def setup_shortcuts(self):
        """Set up keyboard shortcuts"""
        accel_group = Gtk.AccelGroup()
        self.add_accel_group(accel_group)
        
        # Meta+S for next segment
        key, mod = Gtk.accelerator_parse("<Primary>Right")
        accel_group.connect(key, mod, 0, self.next_segment)
        
        # Meta+C for clear
        key, mod = Gtk.accelerator_parse("<Primary>l")
        accel_group.connect(key, mod, 0, self.clear_responses)
    
    def get_latest_tasks(self):
        """Get ALL tasks from bridge for display"""
        if not self.task_db.exists():
            return []
            
        try:
            conn = sqlite3.connect(self.task_db)
            cursor = conn.cursor()
            
            # Get ALL tasks, not just new ones
            cursor.execute('''
                SELECT id, timestamp, requester, task_type, content, context, status, result, tokens_used
                FROM tasks 
                ORDER BY id DESC
                LIMIT 20
            ''')
            
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
                
            # Reverse to show oldest first in display
            tasks.reverse()
                
            conn.close()
            return tasks
        except Exception as e:
            print(f"Database error: {e}")
            return []
    
    def update_response_display(self):
        """Update the response panel with new tasks"""
        tasks = self.get_latest_tasks()
        
        if tasks:
            # Clear and rebuild display
            current_text = ""
            
            for task in tasks:
                # Format task display
                task_display = f"""
┌─ TASK #{task['id']} ─ {task['timestamp']} ─────────────────────────────────────
│ Type: {task['task_type']} | Status: {task['status']}
├─────────────────────────────────────────────────────────────────────────────
│ REQUEST: {task['content'][:200]}{'...' if len(task['content']) > 200 else ''}
│
"""
                
                if task['result']:
                    task_display += f"│ DOLORES RESPONDS:\n│ {task['result']}\n│\n"
                    if task['tokens_used']:
                        task_display += f"│ 🪙 DeepSeek tokens: {task['tokens_used']}\n"
                else:
                    task_display += "│ ⏳ Processing...\n"
                
                task_display += "└─────────────────────────────────────────────────────────────────────────────\n\n"
                
                current_text += task_display
                
                # Update status
                self.response_status.set_text(f"🟢 Active - Last: Task #{task['id']}")
                if task['status'] == 'completed':
                    self.response_status.get_style_context().add_class("status-active")
            
            self.response_buffer.set_text(current_text)
            
            # Auto-scroll to bottom
            mark = self.response_buffer.get_insert()
            self.response_textview.scroll_mark_onscreen(mark)
            
            # Update status bar
            context_id = self.statusbar.get_context_id("main")
            self.statusbar.pop(context_id)
            self.statusbar.push(context_id, f"🎙️ Processed {len(tasks)} new responses - Studio active")
        
        return True  # Continue monitoring
    
    def load_script_segments(self):
        """Load podcast script segments"""
        segments = self.memory.get_podcast_segments()
        
        if not segments:
            # Add default segments
            self.memory.add_podcast_segment("Introduction", "Welcome to the podcast! Today we're discussing...")
            self.memory.add_podcast_segment("Main Topic", "Let's dive into the main topic...")
            self.memory.add_podcast_segment("Conclusion", "Thanks for listening! We'll see you next time...")
            segments = self.memory.get_podcast_segments()
        
        if segments and self.current_segment < len(segments):
            current = segments[self.current_segment]
            self.segment_label.set_text(f"Segment {current['order']}: {current['title']}")
            self.script_buffer.set_text(current['content'])
    
    def next_segment(self, widget=None):
        """Move to next script segment"""
        segments = self.memory.get_podcast_segments()
        self.current_segment = (self.current_segment + 1) % len(segments)
        self.load_script_segments()
    
    def clear_responses(self, widget=None):
        """Clear the response panel"""
        self.response_buffer.set_text("🔄 Responses cleared - Monitoring for new activity...\n\n")
        self.response_status.set_text("⏳ Waiting for activity...")
        self.response_status.get_style_context().remove_class("status-active")
    
    def add_script_segment(self, widget):
        """Add a new script segment"""
        dialog = Gtk.Dialog(title="Add Script Segment", parent=self)
        dialog.set_default_size(400, 200)
        
        content_area = dialog.get_content_area()
        
        # Title entry
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        title_box.pack_start(Gtk.Label(label="Title:"), False, False, 0)
        title_entry = Gtk.Entry()
        title_box.pack_start(title_entry, True, True, 0)
        content_area.pack_start(title_box, False, False, 5)
        
        # Content text
        content_area.pack_start(Gtk.Label(label="Content:"), False, False, 0)
        text_view = Gtk.TextView()
        text_buffer = text_view.get_buffer()
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(text_view)
        scrolled.set_size_request(-1, 100)
        content_area.pack_start(scrolled, True, True, 5)
        
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Add", Gtk.ResponseType.OK)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            title = title_entry.get_text()
            content = text_buffer.get_text(
                text_buffer.get_start_iter(),
                text_buffer.get_end_iter(),
                False
            )
            if title and content:
                self.memory.add_podcast_segment(title, content)
                self.load_script_segments()
        
        dialog.destroy()
    
    def save_current_script(self, widget):
        """Save the current script segment"""
        segments = self.memory.get_podcast_segments()
        if segments and self.current_segment < len(segments):
            # Update current segment content
            new_content = self.script_buffer.get_text(
                self.script_buffer.get_start_iter(),
                self.script_buffer.get_end_iter(),
                False
            )
            # Note: In a full implementation, you'd update the database here
            print(f"Saved segment content: {new_content[:50]}...")
    
    def show_memory_stats(self, widget):
        """Show Dolores's memory statistics"""
        stats = self.memory.get_memory_stats()
        
        stats_text = f"""📊 DOLORES MEMORY STATISTICS
        
Total Memories: {stats['total_memories']}
Categories: {stats['categories']}
Family Relationships: {stats['total_relationships']}
Script Segments: {stats['script_segments']}
Top Topics: {stats['top_topics']}
Vector Documents: {stats['vector_documents']}
Storage Used: {stats['storage_used_mb']:.1f} MB

🧠 Dolores is learning and growing!"""
        
        dialog = Gtk.MessageDialog(
            parent=self,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Dolores Memory Stats"
        )
        dialog.format_secondary_text(stats_text)
        dialog.run()
        dialog.destroy()
    
    def start_monitoring(self):
        """Start monitoring for new tasks"""
        def monitor_loop():
            while True:
                GLib.idle_add(self.update_response_display)
                time.sleep(3)  # Check every 3 seconds
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()

def main():
    app = DoloresStudioUI()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    
    print("🎙️ Dolores Studio UI launched")
    print("Keyboard shortcuts:")
    print("  Ctrl+Right: Next segment")
    print("  Ctrl+L: Clear responses")
    
    Gtk.main()

if __name__ == "__main__":
    main()