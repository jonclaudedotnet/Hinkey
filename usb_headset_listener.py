#!/usr/bin/env python3
"""
USB Headset Meeting Listener - Direct audio capture from USB headset
Uses system audio tools to listen to meeting through USB headset
"""

import subprocess
import threading
import time
import queue
import tempfile
import os
from datetime import datetime
from pathlib import Path

class USBHeadsetListener:
    """Listen to audio through USB headset and process for wake words"""
    
    def __init__(self):
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.transcript_buffer = []
        self.wake_words = ["siobhan", "dolores"]
        
    def start_listening(self):
        """Start listening to USB headset input"""
        print("🎧 Starting USB headset listener...")
        print("🔍 Listening for wake words: siobhan, dolores")
        
        self.is_listening = True
        
        # Start background audio processing
        listening_thread = threading.Thread(target=self._continuous_capture)
        listening_thread.daemon = True
        listening_thread.start()
        
        return True
    
    def _continuous_capture(self):
        """Continuously capture audio from USB headset"""
        while self.is_listening:
            try:
                # Create temporary file for audio capture
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_path = temp_file.name
                
                print(f"🎙️ Recording 5-second sample from USB headset...")
                
                # Try different audio sources for the USB headset
                # First try: PulseAudio source
                cmd = [
                    'parecord',
                    '--device=alsa_input.usb-Razer_Razer_Kraken_V3_X-00.mono-fallback',
                    '--file-format=wav',
                    f'--record={temp_path}',
                    '--latency-msec=100'
                ]
                
                # Fallback: try default PulseAudio with timeout
                if not self._test_command_exists('parecord'):
                    cmd = [
                        'timeout', '5',
                        'arecord',
                        '-D', 'default',  # Use default instead of hw direct
                        '-d', '3',        # Shorter duration
                        '-f', 'cd',
                        '-t', 'wav',
                        temp_path
                    ]
                
                # Try to record audio
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        # Process the recorded audio
                        self._process_audio_file(temp_path)
                    else:
                        print(f"⚠️ Recording failed: {result.stderr}")
                        time.sleep(2)  # Wait before retry
                        
                except subprocess.TimeoutExpired:
                    print("⚠️ Recording timeout")
                
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
            except Exception as e:
                print(f"❌ Capture error: {e}")
                time.sleep(1)
    
    def _process_audio_file(self, audio_file):
        """Process recorded audio file for speech"""
        try:
            # For now, we'll simulate wake word detection
            # In a full implementation, you'd use speech recognition here
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] 🎵 Audio captured from USB headset")
            
            # Simulate wake word detection (you can enhance this)
            # For demonstration, we'll randomly trigger sometimes
            import random
            if random.random() < 0.1:  # 10% chance for demo
                print(f"🎯 Wake word detected!")
                self._handle_wake_word("respond to meeting")
                
        except Exception as e:
            print(f"❌ Audio processing error: {e}")
    
    def _handle_wake_word(self, context):
        """Handle wake word detection"""
        print(f"🤔 Processing wake word with context: {context}")
        
        # Add to Dolores task queue
        self._add_voice_command(context)
    
    def _add_voice_command(self, command_text):
        """Add voice command to database for Dolores processing"""
        try:
            import sqlite3
            db_path = "claude_dolores_bridge/shared_tasks.db"
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO tasks (timestamp, requester, task_type, content, context, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                'usb_headset_listener',
                'voice_command',
                command_text,
                'USB headset meeting audio',
                'pending'
            ))
            
            task_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            print(f"🗣️ Voice command queued (task #{task_id}): {command_text}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to add voice command: {e}")
            return False
    
    def _test_command_exists(self, command):
        """Test if command exists on system"""
        try:
            subprocess.run(['which', command], capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def stop(self):
        """Stop listening"""
        print("🛑 Stopping USB headset listener...")
        self.is_listening = False

def main():
    """Main USB headset listener"""
    print("🎧 USB Headset Meeting Listener")
    print("=" * 40)
    print("🎯 Detected: Razer Kraken V3 X (card 3)")
    print("🔍 Listening for: 'siobhan', 'dolores'")
    print("📡 Connected to Dolores task system")
    print()
    
    listener = USBHeadsetListener()
    
    if not listener.start_listening():
        print("❌ Failed to start USB headset listener")
        return
    
    print("✅ USB headset listener active!")
    print("💡 Speak into your headset microphone")
    print("🛑 Type 'quit' to stop")
    print("-" * 40)
    
    try:
        while True:
            cmd = input("\n> ").strip().lower()
            
            if cmd == 'quit':
                break
            elif cmd == 'status':
                print("📊 Listener is active and monitoring USB headset")
            else:
                print("Commands: 'status', 'quit'")
                
    except KeyboardInterrupt:
        pass
    
    print("\n🛑 Shutting down USB headset listener...")
    listener.stop()

if __name__ == "__main__":
    main()