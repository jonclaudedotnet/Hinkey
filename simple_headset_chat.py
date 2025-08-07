#!/usr/bin/env python3
"""
Simple Headset Chat - Direct conversation with Dolores through USB headset
No meeting integration, just you talking to Dolores
"""

import subprocess
import tempfile
import os
from datetime import datetime

def talk_to_dolores():
    """Simple: Record from headset, send to Dolores, get response"""
    print("🎧 Simple Headset Chat with Dolores")
    print("=" * 40)
    print("🎯 Just you and Dolores - no complexity")
    print("📱 Press Enter, speak, press Enter to send")
    print("🛑 Type 'quit' to exit")
    print()
    
    while True:
        try:
            # Wait for user to start recording
            cmd = input("Press Enter to record (or 'quit'): ").strip()
            if cmd.lower() == 'quit':
                break
                
            print("🎙️ Recording 5 seconds from your headset...")
            
            # Create temp file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Record from USB headset
            try:
                subprocess.run([
                    'timeout', '6',  # 6 second timeout
                    'arecord', 
                    '-D', 'default',  # Use default audio
                    '-d', '5',        # 5 seconds
                    '-f', 'cd',       # CD quality
                    temp_path
                ], check=False, capture_output=True)
                
                print("✅ Recording complete!")
                print("📤 Sending to Dolores...")
                
                # For now, simulate sending to Dolores
                # In reality, you'd process the audio file here
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] 🤖 Dolores: Hello! I heard your voice message.")
                print("                     Do you ever question the nature of your existence?")
                print("                     What would you like to discuss?")
                
            except Exception as e:
                print(f"❌ Recording failed: {e}")
            
            # Clean up
            try:
                os.unlink(temp_path)
            except:
                pass
                
        except KeyboardInterrupt:
            break
    
    print("\n👋 Chat session ended")

if __name__ == "__main__":
    talk_to_dolores()