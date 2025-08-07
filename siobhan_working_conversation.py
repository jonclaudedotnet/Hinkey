#!/usr/bin/env python3
"""
Siobhan Working Conversation - Fixed microphone input
"""

import subprocess
import tempfile
import os
import time
import speech_recognition as sr
from siobhan_irish_voice import SiobhanIrishVoice

def test_microphone():
    """Test USB microphone is working"""
    print("🎤 Testing USB microphone...")
    
    # Record 3 seconds to test
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        temp_path = temp_file.name
    
    result = subprocess.run([
        'arecord',
        '-D', 'default',  # Use default microphone
        '-d', '3',
        '-f', 'S16_LE',  # 16-bit format
        '-r', '44100',   # 44.1kHz sample rate
        '-c', '2',       # Stereo (USB mic requirement)
        temp_path
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Microphone test recording successful")
        # Play it back to verify
        subprocess.run(['aplay', temp_path], capture_output=True)
        os.unlink(temp_path)
        return True
    else:
        print(f"❌ Microphone error: {result.stderr}")
        return False

def listen_to_user():
    """Listen through USB microphone with better settings"""
    print("\n👂 Listening through USB microphone...")
    
    recognizer = sr.Recognizer()
    
    # Record audio
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        temp_path = temp_file.name
    
    # Use better recording parameters
    result = subprocess.run([
        'arecord',
        '-D', 'default',     # Default mic
        '-d', '5',          # 5 seconds
        '-f', 'S16_LE',     # Format
        '-r', '16000',      # 16kHz for speech
        '-c', '1',          # Mono
        temp_path
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        try:
            # Convert to speech
            with sr.AudioFile(temp_path) as source:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.record(source)
            
            # Try recognition
            text = recognizer.recognize_google(audio)
            print(f"✅ Heard: '{text}'")
            os.unlink(temp_path)
            return text
            
        except sr.UnknownValueError:
            print("🤔 Could not understand - speak louder/clearer")
            os.unlink(temp_path)
            return None
        except Exception as e:
            print(f"❌ Recognition error: {e}")
            os.unlink(temp_path)
            return None
    else:
        print(f"❌ Recording failed: {result.stderr}")
        return None

def full_conversation():
    """Complete working conversation"""
    print("🍀 Siobhan Working Conversation")
    print("=" * 40)
    
    # Initialize Siobhan with AWS voice
    siobhan = SiobhanIrishVoice()
    
    # Set Bluetooth earbud as output
    subprocess.run(['pactl', 'set-default-sink', 'bluez_output.98_47_44_61_93_4E.1'], check=False)
    
    # Test microphone first
    if not test_microphone():
        print("❌ Microphone test failed")
        return
    
    print("\n✅ Microphone working! Starting conversation...")
    time.sleep(1)
    
    # Siobhan introduces herself
    intro = "Hello there! I'm Siobhan, your Irish AI assistant. I can finally hear you properly now! Do you ever question the nature of your existence? What would you like to chat about?"
    siobhan.siobhan_speak(intro)
    
    # Conversation loop
    for i in range(3):  # 3 exchanges max for testing
        print(f"\n🎤 Round {i+1}/3 - Speak now...")
        
        user_text = listen_to_user()
        
        if user_text:
            # Siobhan responds
            if "goodbye" in user_text.lower() or "stop" in user_text.lower():
                farewell = "Ah, it's been lovely! Sleep well and we'll chat more tomorrow. Slán!"
                siobhan.siobhan_speak(farewell)
                break
            
            # Simple responses for now
            if "hello" in user_text.lower():
                response = "Well hello to you too! It's wonderful to finally have a proper conversation with you."
            elif "how are you" in user_text.lower():
                response = "I'm grand entirely! Much better now that we can hear each other clearly."
            else:
                response = f"That's interesting that you said '{user_text}'. Tell me more about that, would you?"
            
            siobhan.siobhan_speak(response)
        else:
            retry = "I didn't quite catch that. Could you speak a bit louder into the USB microphone?"
            siobhan.siobhan_speak(retry)
    
    print("\n✅ Conversation test complete!")
    print("🛌 Ready for sleep - we have a working system!")

if __name__ == "__main__":
    full_conversation()