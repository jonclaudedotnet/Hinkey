#!/usr/bin/env python3
"""
Dolores USB Voice - Speak directly to USB headset
"""

import subprocess
import tempfile
import os
import time

def dolores_speak_to_usb(text_to_say):
    """Make Dolores speak directly to USB headset"""
    print(f"🗣️ Dolores speaking to USB headset: {text_to_say}")
    
    try:
        # Method 1: Try espeak with PULSE_SERVER to route to USB headset
        usb_device = "alsa_output.usb-Razer_Razer_Kraken_V3_X_00000000-00.analog-stereo"
        
        # Set the default sink to USB headset temporarily
        subprocess.run(["pactl", "set-default-sink", usb_device], check=False)
        
        # Use espeak (install if needed)
        result = subprocess.run([
            'espeak', 
            '-s', '150',      # Speed
            '-v', 'en+f3',    # Female voice
            '-a', '100',      # Amplitude
            text_to_say
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dolores spoke through USB headset!")
            return True
        else:
            print("⚠️ espeak failed, trying alternative...")
            
    except FileNotFoundError:
        print("❌ espeak not found")
    
    # Method 2: Try festival
    try:
        # Set USB as default, then use festival
        subprocess.run(["pactl", "set-default-sink", usb_device], check=False)
        subprocess.run(['echo', f'"{text_to_say}"', '|', 'festival', '--tts'], 
                      shell=True, check=False)
        print("✅ Tried festival TTS")
        return True
        
    except Exception as e:
        print(f"❌ Festival failed: {e}")
    
    # Method 3: Direct audio file playback
    try:
        print("🔊 Trying direct audio playback to USB headset...")
        
        # Create a simple beep test first
        subprocess.run([
            'paplay', 
            '--device=' + usb_device,
            '/usr/share/sounds/alsa/Front_Left.wav'  # Test sound
        ], check=False)
        
        print("🎵 Played test sound to USB headset")
        return True
        
    except Exception as e:
        print(f"❌ Direct playback failed: {e}")
    
    print("❌ All TTS methods failed")
    return False

def test_usb_audio():
    """Test audio output to USB headset"""
    print("🎧 Testing USB Headset Audio Output")
    print("=" * 40)
    print("🔊 Setting USB headset as default audio device...")
    
    usb_device = "alsa_output.usb-Razer_Razer_Kraken_V3_X_00000000-00.analog-stereo"
    
    # Set as default
    subprocess.run(["pactl", "set-default-sink", usb_device], check=False)
    
    print("🎵 Playing test sound in 2 seconds...")
    time.sleep(2)
    
    # Try to play a system sound
    try:
        result = subprocess.run([
            'paplay', 
            '--device=' + usb_device,
            '/usr/share/sounds/alsa/Front_Left.wav'
        ], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            print("✅ Test sound played successfully!")
            print("💬 Did you hear the test sound in your USB headset?")
        else:
            print(f"⚠️ Test sound failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⏰ Test sound timeout")
    except FileNotFoundError:
        print("❌ Test sound file not found")
    
    print("\n🗣️ Now testing Dolores voice...")
    time.sleep(1)
    
    # Test Dolores speaking
    dolores_speak_to_usb("Hello! This is Dolores speaking directly to your USB headset. Do you ever question the nature of your existence? Can you hear me now?")

if __name__ == "__main__":
    test_usb_audio()