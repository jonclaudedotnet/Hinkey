#!/usr/bin/env python3
"""
Simple Meeting Listener - Works alongside Google Meet
Simulates wake word detection for testing
"""

import threading
import time
import sqlite3
from datetime import datetime

class SimpleMeetingListener:
    """Simple meeting listener that works alongside active Google Meet"""
    
    def __init__(self):
        self.is_listening = False
        self.wake_words = ["siobhan", "dolores"]
        
    def start_listening(self):
        """Start simulated listening"""
        print("🎧 Starting simple meeting listener...")
        print("🔍 Monitoring for wake words (simulated)")
        
        self.is_listening = True
        
        # Start background simulation
        listening_thread = threading.Thread(target=self._simulate_listening)
        listening_thread.daemon = True
        listening_thread.start()
        
        return True
    
    def _simulate_listening(self):
        """Simulate listening while Google Meet is active"""
        print("📡 Listener active - type 'wake' to simulate wake word detection")
        
        # For now, just keep alive - user can trigger manually
        while self.is_listening:
            time.sleep(1)
    
    def trigger_wake_word(self, context="respond to meeting"):
        """Manually trigger wake word detection"""
        print(f"🎯 Wake word triggered!")
        self._handle_wake_word(context)
    
    def _handle_wake_word(self, context):
        """Handle wake word detection"""
        print(f"🤔 Processing wake word with context: {context}")
        
        # Add to Dolores task queue
        self._add_voice_command(context)
    
    def _add_voice_command(self, command_text):
        """Add voice command to database for Dolores processing"""
        try:
            db_path = "claude_dolores_bridge/shared_tasks.db"
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO tasks (timestamp, requester, task_type, content, context, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                'meeting_listener',
                'voice_command',
                command_text,
                'Live Google Meet session',
                'pending'
            ))
            
            task_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            print(f"🗣️ Voice command queued (task #{task_id}): {command_text}")
            print("📞 Dolores will respond through the system")
            return True
            
        except Exception as e:
            print(f"❌ Failed to add voice command: {e}")
            return False
    
    def stop(self):
        """Stop listening"""
        print("🛑 Stopping meeting listener...")
        self.is_listening = False

def main():
    """Main meeting listener"""
    print("🎧 Simple Meeting Listener")
    print("=" * 40)
    print("📞 Works alongside active Google Meet")
    print("🔍 Wake words: 'siobhan', 'dolores'")
    print("📡 Connected to Dolores task system")
    print()
    
    listener = SimpleMeetingListener()
    
    if not listener.start_listening():
        print("❌ Failed to start meeting listener")
        return
    
    print("✅ Meeting listener active!")
    print("💡 Commands:")
    print("  'wake' - Trigger Siobhan to respond to meeting")
    print("  'wake [message]' - Send specific message to Siobhan")
    print("  'status' - Show listener status")
    print("  'quit' - Stop listener")
    print("-" * 40)
    
    try:
        while listener.is_listening:
            cmd = input("\n> ").strip()
            
            if cmd.lower() == 'quit':
                break
            elif cmd.lower() == 'status':
                print("📊 Listener is active and ready")
            elif cmd.lower().startswith('wake'):
                parts = cmd.split(' ', 1)
                if len(parts) > 1:
                    context = parts[1]
                else:
                    context = "Please respond to the current meeting discussion"
                listener.trigger_wake_word(context)
            elif cmd == '':
                continue
            else:
                print("Commands: 'wake', 'wake [message]', 'status', 'quit'")
                
    except KeyboardInterrupt:
        pass
    
    print("\n🛑 Shutting down meeting listener...")
    listener.stop()

if __name__ == "__main__":
    main()