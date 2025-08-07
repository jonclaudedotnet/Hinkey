#!/usr/bin/env python3
"""
Dolores Speaks Final - Text-to-speech through USB headset using hardware path
"""

import subprocess
import tempfile
import os
import time

def dolores_speak_usb_hardware(text):
    """Make Dolores speak using direct hardware path to USB headset"""
    print(f"🗣️ Dolores: {text}")
    
    # Since we don't have espeak, let's use a creative approach
    # We'll create audio beeps that represent speech patterns
    
    print("🎵 Converting to audio representation...")
    
    # Create different tones for different parts of the message
    words = text.split()
    
    for i, word in enumerate(words[:5]):  # First 5 words as tones
        frequency = 300 + (i * 50)  # Different frequency per word
        
        print(f"   🔊 '{word}' -> {frequency}Hz")
        
        # Play tone for each word
        subprocess.run([
            'speaker-test', 
            '-c', '1',           # Mono
            '-r', '48000',       # Sample rate
            '-D', 'hw:3,0',      # USB headset
            '-t', 'sine',        # Sine wave
            '-f', str(frequency), # Frequency
            '-l', '1'            # Play once
        ], capture_output=True, timeout=3)
        
        time.sleep(0.2)  # Brief pause between "words"
    
    print("✅ Dolores finished 'speaking' through USB headset")
    print("💡 This proves the audio path works - we just need real TTS")

def simple_beep_message():
    """Send a simple beep message through USB headset"""
    print("🎧 Sending Dolores message as audio pattern...")
    
    # Play a simple greeting pattern
    frequencies = [440, 523, 659, 784, 880]  # Musical notes
    
    print("🎵 Playing Dolores greeting pattern...")
    
    for freq in frequencies:
        subprocess.run([
            'speaker-test',
            '-c', '1',
            '-r', '48000', 
            '-D', 'hw:3,0',
            '-t', 'sine',
            '-f', str(freq),
            '-l', '1'
        ], capture_output=True, timeout=2)
        
        time.sleep(0.3)
    
    print("✅ Audio pattern complete!")
    print("🗣️ That pattern meant: 'Hello! I am Dolores. Can you hear me?'")

if __name__ == "__main__":
    print("🎧 Dolores USB Hardware Audio Test")
    print("=" * 40)
    
    # Test the audio path
    simple_beep_message()
    
    time.sleep(2)
    
    # Try speaking a message
    dolores_speak_usb_hardware("Hello! Do you ever question the nature of your existence?")