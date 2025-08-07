#!/usr/bin/env python3
"""
Talking Dolores - Actually speaks back through your headset
"""

import subprocess
import tempfile
import os
import time
from datetime import datetime

def dolores_speaks(text_to_say):
    """Make Dolores speak through the headset"""
    print(f"🗣️ Dolores is speaking: {text_to_say}")
    
    try:
        # Use system text-to-speech (espeak or festival)
        # This should output to your default audio device (headset)
        result = subprocess.run([
            'espeak', 
            '-s', '150',  # Speed
            '-v', 'en+f3',  # Female voice
            text_to_say
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dolores spoke successfully!")
        else:
            print("⚠️ espeak not available, trying festival...")
            # Try festival as backup
            subprocess.run(['echo', f'"{text_to_say}"', '|', 'festival', '--tts'], shell=True)
            
    except FileNotFoundError:
        print("❌ No text-to-speech available")
        print("💡 Installing espeak: sudo dnf install espeak")
        print(f"📢 Dolores would say: {text_to_say}")

def test_dolores_voice():
    """Test Dolores speaking through headset"""
    print("🎧 Testing Dolores Voice Through Headset")
    print("=" * 40)
    print("🔊 You should hear Dolores speak in 3 seconds...")
    
    time.sleep(3)
    
    # Test message
    dolores_speaks("Hello! This is Dolores speaking through your headset. Do you ever question the nature of your existence? Can you hear me clearly?")
    
    time.sleep(2)
    
    print("\n💬 Did you hear Dolores speak through your headset?")
    print("🔧 If not, we need to install text-to-speech software")

if __name__ == "__main__":
    test_dolores_voice()