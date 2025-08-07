#!/usr/bin/env python3
"""
Siobhan Voice System - Text-to-Speech for Google Meet integration
Allows Siobhan to speak in meetings when triggered
"""

import subprocess
import pyttsx3
import threading
import time
import queue
from pathlib import Path
from claude_dolores_bridge import wait_for_dolores

class SiobhanVoice:
    def __init__(self):
        # Initialize TTS engine
        self.engine = pyttsx3.init()
        self.setup_voice()
        
        # Message queue for async speaking
        self.speech_queue = queue.Queue()
        self.speaking = False
        
        # Virtual audio setup
        self.virtual_audio_name = "siobhan_voice"
        self.setup_virtual_audio()
        
    def setup_voice(self):
        """Configure Siobhan's voice characteristics"""
        voices = self.engine.getProperty('voices')
        
        # Try to find a female voice
        female_voice = None
        for voice in voices:
            if 'female' in voice.name.lower() or 'woman' in voice.name.lower():
                female_voice = voice
                break
        
        if female_voice:
            self.engine.setProperty('voice', female_voice.id)
        
        # Set voice properties for Siobhan
        self.engine.setProperty('rate', 150)    # Slightly slower for clarity
        self.engine.setProperty('volume', 0.9)  # Good volume
        
    def setup_virtual_audio(self):
        """Create virtual audio device for Google Meet"""
        print("🎤 Setting up virtual audio device...")
        
        # Check if module already loaded
        check_cmd = ['pactl', 'list', 'short', 'sinks']
        result = subprocess.run(check_cmd, capture_output=True, text=True)
        
        if self.virtual_audio_name not in result.stdout:
            # Create virtual sink
            cmd = [
                'pactl', 'load-module', 'module-null-sink',
                f'sink_name={self.virtual_audio_name}',
                'sink_properties=device.description="Siobhan_Voice_Output"'
            ]
            
            try:
                subprocess.run(cmd, check=True)
                print("✅ Virtual audio device created")
                
                # Create loopback so we can hear locally too
                loopback_cmd = [
                    'pactl', 'load-module', 'module-loopback',
                    f'source={self.virtual_audio_name}.monitor',
                    'latency_msec=1'
                ]
                subprocess.run(loopback_cmd)
                
            except subprocess.CalledProcessError as e:
                print(f"⚠️  Virtual audio setup failed: {e}")
        else:
            print("✅ Virtual audio device already exists")
    
    def speak(self, text):
        """Speak text through virtual audio device"""
        # Save current audio output
        original_output = subprocess.run(
            ['pactl', 'get-default-sink'], 
            capture_output=True, text=True
        ).stdout.strip()
        
        try:
            # Switch to virtual output
            subprocess.run(['pactl', 'set-default-sink', self.virtual_audio_name])
            
            # Speak the text
            self.engine.say(text)
            self.engine.runAndWait()
            
        finally:
            # Restore original output
            subprocess.run(['pactl', 'set-default-sink', original_output])
    
    def speak_async(self, text):
        """Add text to speech queue"""
        self.speech_queue.put(text)
    
    def speech_worker(self):
        """Background thread for speaking"""
        while True:
            text = self.speech_queue.get()
            if text is None:  # Shutdown signal
                break
            
            self.speaking = True
            print(f"🗣️ Siobhan: {text[:50]}...")
            self.speak(text)
            self.speaking = False
            self.speech_queue.task_done()
    
    def start(self):
        """Start the speech worker thread"""
        self.worker_thread = threading.Thread(target=self.speech_worker, daemon=True)
        self.worker_thread.start()
        print("🎙️ Siobhan voice system started")
    
    def stop(self):
        """Stop the speech worker"""
        self.speech_queue.put(None)
        self.worker_thread.join()

class SiobhanMeetingAssistant:
    def __init__(self):
        self.voice = SiobhanVoice()
        self.voice.start()
        self.last_task_id = 0
        
    def check_for_responses(self):
        """Monitor for Dolores/Siobhan responses to speak"""
        while True:
            # Check for new responses in the task database
            # This would monitor for responses tagged for speaking
            time.sleep(2)
            
            # For now, this is a placeholder
            # In full implementation, this would check the shared database
            # for responses marked with "speak_in_meeting" flag
    
    def trigger_response(self, prompt):
        """Manually trigger Siobhan to respond"""
        print(f"🎯 Triggering Siobhan response to: {prompt}")
        
        # Send to Dolores for response
        from claude_dolores_bridge import ask_dolores
        task_id = ask_dolores(
            'meeting_response',
            f"Meeting participant asked: {prompt}. Please provide a brief, spoken response suitable for a Google Meet call.",
            'Meeting response request'
        )
        
        # Wait for response
        response = wait_for_dolores(task_id, timeout=10)
        
        if response:
            # Extract just the response content (remove LEARN entries)
            clean_response = response.split('**LEARN')[0].strip()
            clean_response = clean_response.replace('**Task Result:**', '').strip()
            
            # Speak it
            self.voice.speak_async(clean_response)
            return clean_response
        
        return None
    
    def test_voice(self):
        """Test Siobhan's voice"""
        test_message = "Hello everyone, this is Siobhan joining the meeting. I'm looking forward to our discussion today."
        print("🧪 Testing voice system...")
        self.voice.speak_async(test_message)

def check_for_voice_commands(assistant):
    """Check database for voice commands to process"""
    import sqlite3
    import os
    
    db_path = os.path.join(os.path.dirname(__file__), 'claude_dolores_bridge', 'shared_tasks.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Look for voice tasks that haven't been processed
        cursor.execute("""
            SELECT id, content FROM tasks 
            WHERE task_type = 'voice_command' 
            AND status = 'pending' 
            ORDER BY id ASC 
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        if result:
            task_id, voice_text = result
            print(f"🗣️ Processing voice command: {voice_text[:50]}...")
            
            # Mark as in progress
            cursor.execute("UPDATE tasks SET status = 'in_progress' WHERE id = ?", (task_id,))
            conn.commit()
            
            # Speak the text
            assistant.voice.speak_async(voice_text)
            
            # Mark as completed
            cursor.execute("UPDATE tasks SET status = 'completed' WHERE id = ?", (task_id,))
            conn.commit()
            
        conn.close()
        
    except Exception as e:
        print(f"⚠️  Database error: {e}")
        time.sleep(1)  # Wait a bit before retrying

def main():
    """Main entry point"""
    import sys
    import signal
    
    # Check if running in daemon mode (no arguments means interactive)
    daemon_mode = len(sys.argv) > 1 and sys.argv[1] == '--daemon'
    
    print("🎙️ Siobhan Meeting Voice System")
    print("=" * 40)
    
    assistant = SiobhanMeetingAssistant()
    
    if daemon_mode:
        print("🔄 Running in daemon mode...")
        print("✅ Voice system ready for meeting integration")
        print("📝 Check database for voice commands from other processes")
        
        # Set up signal handler for graceful shutdown
        def signal_handler(sig, frame):
            print("\n🛑 Received shutdown signal...")
            assistant.voice.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Daemon mode - monitor for commands via database
        try:
            while True:
                # Monitor for voice commands from the task database
                check_for_voice_commands(assistant)
                time.sleep(0.5)  # Check twice per second for responsiveness
                
        except KeyboardInterrupt:
            pass
        
    else:
        print("\n📋 Instructions:")
        print("1. In Google Meet, click microphone settings")
        print("2. Select 'Siobhan_Voice_Output' as microphone")
        print("3. Use commands below to make Siobhan speak")
        print("\nCommands:")
        print("  test     - Test Siobhan's voice")
        print("  say TEXT - Make Siobhan say something")
        print("  ask TEXT - Ask Siobhan to respond")
        print("  quit     - Exit")
        print("-" * 40)
        
        while True:
            try:
                cmd = input("\n> ").strip()
                
                if cmd.lower() == 'quit':
                    break
                elif cmd.lower() == 'test':
                    assistant.test_voice()
                elif cmd.lower().startswith('say '):
                    text = cmd[4:]
                    assistant.voice.speak_async(text)
                elif cmd.lower().startswith('ask '):
                    question = cmd[4:]
                    assistant.trigger_response(question)
                else:
                    print("Unknown command. Try 'test', 'say TEXT', or 'ask TEXT'")
                    
            except (KeyboardInterrupt, EOFError):
                break
    
    print("\n👋 Shutting down...")
    assistant.voice.stop()

if __name__ == "__main__":
    main()