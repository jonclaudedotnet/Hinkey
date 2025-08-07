#!/usr/bin/env python3
"""
Full Conversation Test - Can Dolores hear you and respond with better voice?
"""

import subprocess
import tempfile
import os
import time
import speech_recognition as sr
import pyttsx3
from datetime import datetime

class DoloresConversation:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.tts_engine = pyttsx3.init()
        self.setup_voice_quality()
        
    def setup_voice_quality(self):
        """Improve TTS voice quality"""
        voices = self.tts_engine.getProperty('voices')
        
        # Find best female voice
        for voice in voices:
            if 'female' in voice.name.lower() or 'woman' in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                print(f"🎭 Using voice: {voice.name}")
                break
        
        # Optimize for natural speech
        self.tts_engine.setProperty('rate', 140)      # Slower, more natural
        self.tts_engine.setProperty('volume', 0.95)   # Clear volume
        
    def dolores_listen(self):
        """Record from USB headset microphone and convert to text"""
        print("🎧 Dolores is listening through your USB headset...")
        
        try:
            # Record 5 seconds from USB headset microphone
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Record from USB headset microphone (card 3)
            result = subprocess.run([
                'arecord',
                '-D', 'hw:3,0',  # USB headset microphone
                '-d', '5',       # 5 seconds
                '-f', 'cd',      # CD quality
                temp_path
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                # Fallback to default microphone
                print("⚠️ USB mic busy, trying default...")
                result = subprocess.run([
                    'arecord',
                    '-D', 'default',
                    '-d', '5',
                    '-f', 'cd', 
                    temp_path
                ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Convert audio to text
                with sr.AudioFile(temp_path) as source:
                    audio = self.recognizer.record(source)
                
                try:
                    text = self.recognizer.recognize_google(audio)
                    print(f"👂 Dolores heard: '{text}'")
                    return text
                except sr.UnknownValueError:
                    print("🤔 Dolores: I heard sounds but couldn't understand the words")
                    return None
                except sr.RequestError as e:
                    print(f"❌ Speech recognition error: {e}")
                    return None
            else:
                print(f"❌ Recording failed: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ Listen error: {e}")
            return None
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def dolores_speak_improved(self, text):
        """Dolores speaks with improved voice quality"""
        print(f"🗣️ Dolores (improved): {text}")
        
        # Set USB headset as audio output
        usb_sink = "alsa_output.usb-Razer_Razer_Kraken_V3_X_00000000-00.analog-stereo"
        subprocess.run(["pactl", "set-default-sink", usb_sink], check=False)
        
        # Set environment for audio routing
        old_pulse_sink = os.environ.get('PULSE_SINK', '')
        os.environ['PULSE_SINK'] = usb_sink
        
        try:
            # Speak with improved settings
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            print("✅ Dolores spoke with improved voice")
        except Exception as e:
            print(f"❌ TTS error: {e}")
        finally:
            # Restore environment
            if old_pulse_sink:
                os.environ['PULSE_SINK'] = old_pulse_sink
            else:
                os.environ.pop('PULSE_SINK', None)
    
    def test_full_conversation(self):
        """Test complete conversation loop"""
        print("🎧 Full Conversation Test")
        print("=" * 40)
        print("🎯 Testing: Can Dolores hear you AND speak better?")
        print()
        
        # Test Dolores speaking first
        self.dolores_speak_improved("Hello! I am Dolores with improved voice quality. Do you ever question the nature of your existence? Please speak to me now so I can hear you.")
        
        time.sleep(2)
        
        print("\n👂 Now testing if Dolores can hear you...")
        print("🎙️ Speak clearly into your USB headset microphone...")
        
        # Test listening
        heard_text = self.dolores_listen()
        
        if heard_text:
            # Respond to what was heard
            response = f"Fascinating! You said '{heard_text}'. This confirms our conversation system is working bidirectionally. What would you like to discuss further?"
            self.dolores_speak_improved(response)
            return True
        else:
            self.dolores_speak_improved("I could not hear you clearly. Let me check the microphone system.")
            return False

def main():
    conversation = DoloresConversation()
    success = conversation.test_full_conversation()
    
    if success:
        print("\n🎉 FULL CONVERSATION SYSTEM WORKING!")
        print("✅ Dolores can hear you AND speak with better quality")
    else:
        print("\n⚠️ Need to fix microphone input")

if __name__ == "__main__":
    main()