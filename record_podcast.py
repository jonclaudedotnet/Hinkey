#!/usr/bin/env python3
"""
Podcast Recording Script - Screen + Voice capture for Hinkey podcast production
"""

import subprocess
import sys
import time
from datetime import datetime
import os

class PodcastRecorder:
    def __init__(self):
        self.recording_process = None
        self.output_dir = "./recordings"
        os.makedirs(self.output_dir, exist_ok=True)
        
    def get_display_info(self):
        """Get available displays for screen capture"""
        try:
            result = subprocess.run(['xrandr'], capture_output=True, text=True)
            displays = []
            for line in result.stdout.split('\n'):
                if ' connected' in line:
                    display_name = line.split()[0]
                    displays.append(display_name)
            return displays
        except:
            return [':0.0']  # fallback
    
    def test_audio(self):
        """Test microphone input"""
        print("🎤 Testing microphone...")
        print("Say something (recording 3 seconds)...")
        
        test_file = "/tmp/mic_test.wav"
        cmd = [
            'arecord', 
            '-D', 'hw:3,0',  # Use USB MIC Device
            '-d', '3',
            '-f', 'cd',
            test_file
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print("✅ Microphone test complete")
            
            # Play back
            print("Playing back test...")
            subprocess.run(['aplay', test_file], check=True)
            os.remove(test_file)
            return True
        except Exception as e:
            print(f"❌ Microphone test failed: {e}")
            return False
    
    def start_recording(self, display=":0.0", audio_device="hw:3,0"):
        """Start screen + voice recording"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{self.output_dir}/podcast_{timestamp}.mkv"
        
        print(f"🎬 Starting recording...")
        print(f"📺 Display: {display}")
        print(f"🎤 Audio: {audio_device}")
        print(f"💾 Output: {output_file}")
        
        # FFmpeg command for screen + audio
        cmd = [
            'ffmpeg',
            '-f', 'x11grab',
            '-s', '1920x1080',  # Adjust to your Siobhan window size
            '-r', '30',  # 30 fps
            '-i', display,
            '-f', 'pulse',
            '-i', 'default',
            '-c:v', 'libopenh264',
            '-preset', 'fast',
            '-crf', '23',  # Good quality
            '-c:a', 'aac',
            '-b:a', '192k',
            '-y',  # Overwrite output file
            output_file
        ]
        
        try:
            self.recording_process = subprocess.Popen(cmd)
            print(f"✅ Recording started (PID: {self.recording_process.pid})")
            print("Press Ctrl+C to stop recording")
            return output_file
        except Exception as e:
            print(f"❌ Failed to start recording: {e}")
            return None
    
    def stop_recording(self):
        """Stop current recording"""
        if self.recording_process:
            print("🛑 Stopping recording...")
            self.recording_process.terminate()
            self.recording_process.wait()
            self.recording_process = None
            print("✅ Recording stopped")
        else:
            print("❌ No active recording")
    
    def list_recordings(self):
        """List available recordings"""
        recordings = []
        if os.path.exists(self.output_dir):
            for file in os.listdir(self.output_dir):
                if file.endswith(('.mkv', '.mp4')):
                    recordings.append(file)
        return sorted(recordings)

def main():
    """Main recording interface"""
    recorder = PodcastRecorder()
    
    print("🎙️ Hinkey Podcast Recorder")
    print("=" * 30)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'test':
            recorder.test_audio()
            
        elif command == 'start':
            display = sys.argv[2] if len(sys.argv) > 2 else ":0.0"
            output_file = recorder.start_recording(display)
            if output_file:
                try:
                    # Keep running until interrupted
                    while recorder.recording_process and recorder.recording_process.poll() is None:
                        time.sleep(1)
                except KeyboardInterrupt:
                    recorder.stop_recording()
                    
        elif command == 'list':
            recordings = recorder.list_recordings()
            if recordings:
                print("📁 Available recordings:")
                for i, recording in enumerate(recordings, 1):
                    print(f"  {i}. {recording}")
            else:
                print("No recordings found")
                
        elif command == 'displays':
            displays = recorder.get_display_info()
            print("🖥️ Available displays:")
            for display in displays:
                print(f"  {display}")
    else:
        print("Usage:")
        print("  python3 record_podcast.py test        # Test microphone")
        print("  python3 record_podcast.py start       # Start recording")
        print("  python3 record_podcast.py list        # List recordings")
        print("  python3 record_podcast.py displays    # Show displays")

if __name__ == "__main__":
    main()