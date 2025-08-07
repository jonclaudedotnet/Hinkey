#!/usr/bin/env python3
"""
Dolores Learning Display with Push-to-Talk Audio Recording
Hold RIGHT CTRL to record voice input
"""

import gi
import sqlite3
import threading
import time
import subprocess
import os
from datetime import datetime
from pathlib import Path
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango

class DoloresLearningWithAudio(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="🎙️ Dolores Learning [Audio Ready]")
        self.set_default_size(900, 700)
        
        # Database setup
        self.db_path = "./claude_dolores_bridge/shared_tasks.db"
        self.last_task_id = 0
        
        # Audio recording setup
        self.recording = False
        self.recording_process = None
        self.audio_dir = Path("./audio_captures")
        self.audio_dir.mkdir(exist_ok=True)
        self.audio_device = "hw:3,0"  # USB MIC Device
        
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
        
        # Status bar for recording info
        self.status_bar = Gtk.Label()
        self.status_bar.set_markup("<b>Ready</b> - Hold RIGHT CTRL to record (up to 5 minutes)")
        self.status_bar.set_margin_top(10)
        self.status_bar.set_margin_bottom(10)
        self.main_box.pack_end(self.status_bar, False, False, 0)
        
        # Set up styling
        self.set_style()
        
        # Initial display
        buffer = self.text_view.get_buffer()
        buffer.set_text("🎙️ Dolores is ready to learn...\n\nWaiting for your first message.\n\n[Hold RIGHT CTRL to record audio]")
        
        # Connect key events
        self.connect("key-press-event", self.on_key_press)
        self.connect("key-release-event", self.on_key_release)
        
        # Start monitoring
        self.monitor_thread = threading.Thread(target=self.monitor_database)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.connect("destroy", self.cleanup_and_quit)
    
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
    
    def on_key_press(self, widget, event):
        """Handle key press events"""
        # Check if RIGHT CTRL is pressed
        if event.keyval == Gdk.KEY_Control_R and not self.recording:
            self.start_recording()
    
    def on_key_release(self, widget, event):
        """Handle key release events"""
        # Check if RIGHT CTRL is released
        if event.keyval == Gdk.KEY_Control_R and self.recording:
            self.stop_recording()
    
    def start_recording(self):
        """Start audio recording"""
        if not self.recording:
            self.recording = True
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            self.current_audio_file = self.audio_dir / f"voice_{timestamp}.wav"
            
            # Update status
            self.status_bar.set_markup("<b style='color: red;'>🔴 RECORDING...</b> Release RIGHT CTRL to stop")
            
            # Start recording with arecord
            cmd = [
                'arecord',
                '-D', self.audio_device,
                '-f', 'cd',  # CD quality
                '-t', 'wav',
                str(self.current_audio_file)
            ]
            
            self.recording_process = subprocess.Popen(cmd, 
                                                    stdout=subprocess.DEVNULL, 
                                                    stderr=subprocess.DEVNULL)
            
            # Also show in main display
            buffer = self.text_view.get_buffer()
            current_text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
            buffer.set_text(current_text + "\n\n🎤 Recording audio...")
    
    def stop_recording(self):
        """Stop recording and process audio"""
        if self.recording and self.recording_process:
            self.recording = False
            self.recording_process.terminate()
            self.recording_process.wait()
            
            # Update status
            self.status_bar.set_markup("<b style='color: green;'>✅ Recording saved!</b> Hold RIGHT CTRL to record again")
            
            # Get file info
            if self.current_audio_file.exists():
                size_kb = self.current_audio_file.stat().st_size / 1024
                
                # Update display
                buffer = self.text_view.get_buffer()
                current_text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
                buffer.set_text(current_text + f"\n✅ Audio captured: {self.current_audio_file.name} ({size_kb:.1f} KB)")
                
                # Here we would send to transcription service
                # For now, just note it's ready
                buffer.set_text(buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True) + 
                              "\n📝 Ready for transcription...")
                
                # Reset status after 3 seconds
                GLib.timeout_add_seconds(3, self.reset_status)
    
    def reset_status(self):
        """Reset status bar to ready state"""
        self.status_bar.set_markup("<b>Ready</b> - Hold RIGHT CTRL to record (up to 5 minutes)")
        return False  # Don't repeat
    
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
        buffer.set_text(text + "\n\n[Hold RIGHT CTRL to record audio]")
    
    def monitor_database(self):
        """Monitor for new responses"""
        while True:
            task_id, new_response = self.get_latest_response()
            
            if task_id and task_id > self.last_task_id and new_response:
                self.last_task_id = task_id
                GLib.idle_add(self.update_display, new_response)
            
            time.sleep(1)  # Check every second
    
    def cleanup_and_quit(self, widget):
        """Clean up resources before quitting"""
        if self.recording and self.recording_process:
            self.recording_process.terminate()
        Gtk.main_quit()

if __name__ == "__main__":
    app = DoloresLearningWithAudio()
    app.show_all()
    
    print("🎙️ Dolores Learning Display with Audio started")
    print("- Hold RIGHT CTRL to record voice input")
    print("- Audio files saved to ./audio_captures/")
    print("- Up to 5 minutes continuous recording")
    
    Gtk.main()