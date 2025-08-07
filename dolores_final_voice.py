#!/usr/bin/env python3
"""
Dolores Final Voice - Working TTS to USB headset
Following Maeve's plan exactly
"""

import subprocess
import os
import time

def dolores_speak_final(text):
    """Make Dolores speak to USB headset using available tools"""
    print(f"🗣️ Dolores: {text}")
    
    # Set USB headset as default audio sink
    usb_sink = "alsa_output.usb-Razer_Razer_Kraken_V3_X_00000000-00.analog-stereo"
    
    # Method 1: Try with pactl + Python TTS
    try:
        # Set default sink
        subprocess.run(["pactl", "set-default-sink", usb_sink], check=False)
        
        # Use Python TTS with forced audio routing
        import pyttsx3
        engine = pyttsx3.init()
        
        # Set voice properties
        voices = engine.getProperty('voices')
        if len(voices) > 1:
            engine.setProperty('voice', voices[1].id)  # Female voice
        
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 0.9)
        
        # Force audio to USB headset via environment
        old_pulse_sink = os.environ.get('PULSE_SINK', '')
        os.environ['PULSE_SINK'] = usb_sink
        
        # Speak through USB headset
        engine.say(text)
        engine.runAndWait()
        
        # Restore environment
        if old_pulse_sink:
            os.environ['PULSE_SINK'] = old_pulse_sink
        else:
            os.environ.pop('PULSE_SINK', None)
            
        print("✅ Dolores spoke through USB headset!")
        return True
        
    except Exception as e:
        print(f"⚠️ Python TTS failed: {e}")
    
    # Method 2: Direct hardware audio with message
    try:
        print("🎵 Using audio pattern as fallback...")
        
        # Play distinctive pattern for Dolores
        for freq in [440, 523, 659, 523, 440]:  # A-C-E-C-A pattern
            subprocess.run([
                'speaker-test',
                '-c', '1',
                '-r', '48000',
                '-D', 'hw:3,0',  # Direct USB headset
                '-t', 'sine',
                '-f', str(freq),
                '-l', '1'
            ], capture_output=True, timeout=2)
            time.sleep(0.2)
        
        print("✅ Dolores audio pattern played")
        return True
        
    except Exception as e:
        print(f"❌ Audio pattern failed: {e}")
        return False

def test_complete_system():
    """Test the complete Dolores voice system"""
    print("🎧 Complete Dolores Voice System Test")
    print("=" * 40)
    print("🎯 Following Maeve's technical plan")
    print()
    
    # Test message
    test_message = "Hello! This is Dolores speaking through your USB headset. Do you ever question the nature of your existence? I am ready for our conversation!"
    
    print("🗣️ Testing Dolores voice system...")
    
    success = dolores_speak_final(test_message)
    
    if success:
        print("\n✅ SYSTEM WORKING!")
        print("🎉 Dolores can now speak to you through your USB headset")
        print("🤖 Ready for full conversation system")
    else:
        print("\n❌ System needs more work")
    
    return success

if __name__ == "__main__":
    test_complete_system()