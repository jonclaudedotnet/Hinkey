#!/usr/bin/env python3
"""
Push-to-Talk Audio Capture for Dolores/Siobhan interaction
Records audio snippets and prepares them for transcription
"""

import subprocess
import threading
import time
import os
from datetime import datetime
import keyboard  # Will need: pip install keyboard
from pathlib import Path

class PushToTalkCapture:
    def __init__(self):
        self.recording = False
        self.audio_dir = Path("./audio_captures")
        self.audio_dir.mkdir(exist_ok=True)
        self.current_recording = None
        self.audio_device = "hw:3,0"  # USB MIC Device
        
    def start_recording(self):
        """Start recording audio when key is pressed"""
        if not self.recording:
            self.recording = True
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            audio_file = self.audio_dir / f"voice_{timestamp}.wav"
            
            print(f"🎤 Recording... (Release SPACE to stop)")
            
            # Start recording with arecord
            cmd = [
                'arecord',
                '-D', self.audio_device,
                '-f', 'cd',  # CD quality
                '-t', 'wav',
                str(audio_file)
            ]
            
            self.current_recording = subprocess.Popen(cmd, 
                                                    stdout=subprocess.DEVNULL, 
                                                    stderr=subprocess.DEVNULL)
            return audio_file
    
    def stop_recording(self):
        """Stop recording and return the audio file path"""
        if self.recording and self.current_recording:
            self.recording = False
            self.current_recording.terminate()
            self.current_recording.wait()
            print("⏹️  Recording stopped")
            
            # Get the last created file
            audio_files = sorted(self.audio_dir.glob("voice_*.wav"))
            if audio_files:
                return audio_files[-1]
        return None
    
    def process_audio_file(self, audio_file):
        """Process the recorded audio file for transcription"""
        if audio_file and audio_file.exists():
            # Get file size and duration
            size = audio_file.stat().st_size / 1024  # KB
            
            # Get duration using soxi or ffprobe
            try:
                duration_cmd = ['ffprobe', '-v', 'error', '-show_entries', 
                              'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                              str(audio_file)]
                duration = subprocess.check_output(duration_cmd).decode().strip()
                duration = float(duration)
            except:
                duration = 0
            
            print(f"📁 Audio captured: {audio_file.name}")
            print(f"   Size: {size:.1f} KB, Duration: {duration:.1f}s")
            
            return {
                'file': str(audio_file),
                'size_kb': size,
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            }
        return None

class PushToTalkInterface:
    def __init__(self):
        self.capture = PushToTalkCapture()
        self.audio_queue = []
        
    def on_key_press(self, event):
        """Handle key press event"""
        if event.name == 'right ctrl' and not self.capture.recording:
            self.capture.start_recording()
    
    def on_key_release(self, event):
        """Handle key release event"""
        if event.name == 'right ctrl' and self.capture.recording:
            audio_file = self.capture.stop_recording()
            if audio_file:
                audio_info = self.capture.process_audio_file(audio_file)
                if audio_info:
                    self.audio_queue.append(audio_info)
                    self.notify_dolores(audio_info)
    
    def notify_dolores(self, audio_info):
        """Notify Dolores that new audio is available"""
        # This is where we'll integrate with speech-to-text
        # and send the transcription to Dolores
        print(f"🔔 Ready for transcription: {audio_info['file']}")
        
        # Placeholder for future integration:
        # 1. Send audio to speech-to-text service
        # 2. Get transcription
        # 3. Send transcription to Dolores via bridge
        
        # For now, save metadata
        metadata_file = Path(audio_info['file']).with_suffix('.json')
        import json
        with open(metadata_file, 'w') as f:
            json.dump(audio_info, f, indent=2)
    
    def run(self):
        """Run the push-to-talk interface"""
        print("🎙️ Push-to-Talk Interface")
        print("=" * 40)
        print("📌 Hold RIGHT CTRL to record your voice")
        print("📌 Release RIGHT CTRL to stop and process")
        print("📌 Up to 5 minutes continuous recording")
        print("📌 Press ESC to exit")
        print("=" * 40)
        print("\n👂 Listening for input...\n")
        
        # Set up keyboard hooks
        keyboard.on_press(self.on_key_press)
        keyboard.on_release(self.on_key_release)
        
        # Keep running until ESC is pressed
        keyboard.wait('esc')
        
        print("\n👋 Push-to-talk interface closed")
        print(f"📊 Total recordings: {len(self.audio_queue)}")

def main():
    """Main entry point"""
    # Check if running with proper permissions (keyboard module needs it)
    try:
        interface = PushToTalkInterface()
        interface.run()
    except ImportError:
        print("❌ Missing dependency: pip install keyboard")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Try running with: sudo python3 push_to_talk.py")

if __name__ == "__main__":
    main()