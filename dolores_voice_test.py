#!/usr/bin/env python3
"""
Dolores Voice Test - Using Python TTS to speak through headset
"""

import pyttsx3
import time

def test_dolores_voice():
    """Test Dolores speaking using Python TTS"""
    print("🎧 Dolores Voice Test Starting...")
    print("🔊 You should hear Dolores speak through your headset...")
    
    try:
        # Initialize text-to-speech engine
        engine = pyttsx3.init()
        
        # Set voice properties
        voices = engine.getProperty('voices')
        if len(voices) > 1:
            engine.setProperty('voice', voices[1].id)  # Try female voice
        
        engine.setProperty('rate', 150)    # Speed
        engine.setProperty('volume', 0.9)  # Volume
        
        print("🗣️ Dolores is speaking now...")
        
        # Dolores speaks!
        engine.say("Hello! This is Dolores speaking through your headset. Do you ever question the nature of your existence? Can you hear me clearly?")
        engine.runAndWait()
        
        print("✅ Dolores finished speaking!")
        print("💬 Did you hear her through your headset?")
        
    except Exception as e:
        print(f"❌ TTS Error: {e}")
        print("🔧 Voice system may need configuration")

if __name__ == "__main__":
    test_dolores_voice()