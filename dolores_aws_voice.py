#!/usr/bin/env python3
"""
Dolores AWS Voice - Professional female voice using AWS Polly
"""

import boto3
import subprocess
import tempfile
import os
import time
import speech_recognition as sr
from datetime import datetime

class DoloresAWSVoice:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
        # Initialize AWS Polly client
        try:
            # AWS credentials should be in ~/.aws/credentials or environment
            self.polly_client = boto3.client('polly')
            print("✅ AWS Polly client initialized")
            
            # Test connection
            response = self.polly_client.describe_voices(LanguageCode='en-US')
            print(f"🔊 Found {len(response['Voices'])} AWS voices")
            
            # Select best female voice
            self.select_best_voice(response['Voices'])
            
        except Exception as e:
            print(f"❌ AWS Polly setup error: {e}")
            print("💡 Need to configure AWS credentials")
            self.polly_client = None
    
    def select_best_voice(self, voices):
        """Select the best Irish female voice for Siobhan"""
        # Siobhan should sound Irish but speak properly
        preferred_voices = [
            'Niamh',     # Irish English, Neural (if available)
            'Amy',       # British English, Neural (closest to Irish)
            'Emma',      # British English, Neural
            'Joanna',    # US English, Neural (fallback)
            'Salli',     # US English, Neural
        ]
        
        available_voices = {v['Id']: v for v in voices if v['Gender'] == 'Female'}
        
        for voice_name in preferred_voices:
            if voice_name in available_voices:
                self.voice_id = voice_name
                voice_info = available_voices[voice_name]
                print(f"🍀 Selected Irish voice: {voice_name} ({voice_info['LanguageCode']})")
                if 'Neural' in voice_info.get('SupportedEngines', []):
                    self.engine = 'neural'
                    print("🧠 Using Neural engine for authentic Irish sound")
                else:
                    self.engine = 'standard'
                return
        
        # Fallback to first available female voice
        if available_voices:
            self.voice_id = list(available_voices.keys())[0]
            self.engine = 'standard'
            print(f"🔄 Using fallback voice: {self.voice_id}")
        else:
            print("❌ No female voices found")
            self.voice_id = 'Joanna'
            self.engine = 'neural'
    
    def dolores_speak_aws(self, text):
        """Dolores speaks using AWS Polly professional voice"""
        if not self.polly_client:
            print("❌ AWS Polly not available, using fallback")
            return self.dolores_speak_fallback(text)
        
        print(f"🗣️ Dolores (AWS {self.voice_id}): {text}")
        
        try:
            # Generate speech with AWS Polly
            response = self.polly_client.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=self.voice_id,
                Engine=self.engine,
                SampleRate='22050'
            )
            
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(response['AudioStream'].read())
            
            # Set USB headset as output
            usb_sink = "alsa_output.usb-Razer_Razer_Kraken_V3_X_00000000-00.analog-stereo"
            subprocess.run(["pactl", "set-default-sink", usb_sink], check=False)
            
            # Play through USB headset using mpv (or ffplay/mplayer)
            players = ['mpv', 'ffplay', 'mplayer', 'cvlc']
            
            for player in players:
                try:
                    if player == 'mpv':
                        cmd = ['mpv', '--no-video', '--really-quiet', temp_path]
                    elif player == 'ffplay':
                        cmd = ['ffplay', '-nodisp', '-autoexit', temp_path]
                    elif player == 'mplayer':
                        cmd = ['mplayer', '-really-quiet', temp_path]
                    elif player == 'cvlc':
                        cmd = ['cvlc', '--intf', 'dummy', '--play-and-exit', temp_path]
                    
                    result = subprocess.run(cmd, capture_output=True, timeout=10)
                    if result.returncode == 0:
                        print(f"✅ Played via {player}")
                        break
                        
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            else:
                # Fallback: convert to WAV and use aplay
                wav_path = temp_path.replace('.mp3', '.wav')
                subprocess.run(['ffmpeg', '-i', temp_path, wav_path], 
                             capture_output=True, check=False)
                subprocess.run(['aplay', '-D', 'hw:3,0', wav_path], 
                             capture_output=True, check=False)
                os.unlink(wav_path)
            
            # Clean up
            os.unlink(temp_path)
            print("✅ AWS Polly speech complete")
            return True
            
        except Exception as e:
            print(f"❌ AWS Polly error: {e}")
            return self.dolores_speak_fallback(text)
    
    def dolores_speak_fallback(self, text):
        """Fallback TTS if AWS fails"""
        print(f"🔄 Dolores (fallback): {text}")
        
        import pyttsx3
        engine = pyttsx3.init()
        
        voices = engine.getProperty('voices')
        for voice in voices:
            if 'female' in voice.name.lower():
                engine.setProperty('voice', voice.id)
                break
        
        engine.setProperty('rate', 140)
        engine.setProperty('volume', 0.95)
        
        usb_sink = "alsa_output.usb-Razer_Razer_Kraken_V3_X_00000000-00.analog-stereo"
        subprocess.run(["pactl", "set-default-sink", usb_sink], check=False)
        
        old_pulse_sink = os.environ.get('PULSE_SINK', '')
        os.environ['PULSE_SINK'] = usb_sink
        
        try:
            engine.say(text)
            engine.runAndWait()
            return True
        finally:
            if old_pulse_sink:
                os.environ['PULSE_SINK'] = old_pulse_sink
            else:
                os.environ.pop('PULSE_SINK', None)
    
    def dolores_listen(self):
        """Listen through USB headset microphone"""
        print("👂 Dolores listening...")
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Record from USB headset
            result = subprocess.run([
                'arecord',
                '-D', 'hw:3,0',
                '-d', '5',
                '-f', 'cd',
                temp_path
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                with sr.AudioFile(temp_path) as source:
                    # Adjust for noise
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = self.recognizer.record(source)
                
                try:
                    text = self.recognizer.recognize_google(audio)
                    print(f"👂 Heard: '{text}'")
                    return text
                except sr.UnknownValueError:
                    print("🤔 Could not understand audio")
                    return None
                except sr.RequestError as e:
                    print(f"❌ Recognition error: {e}")
                    return None
            else:
                print("❌ Recording failed")
                return None
                
        except Exception as e:
            print(f"❌ Listen error: {e}")
            return None
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def test_aws_voice(self):
        """Test AWS Polly voice quality"""
        print("🎧 Testing AWS Polly Professional Voice")
        print("=" * 50)
        
        test_message = "Hello! I am Siobhan, your Irish AI assistant. Do you ever question the nature of your existence? I should sound properly Irish now, not robotic at all."
        
        success = self.dolores_speak_aws(test_message)
        
        if success:
            print("\n🎉 AWS Voice test complete!")
        
        return success

def setup_aws_credentials():
    """Help user set up AWS credentials"""
    print("🔧 AWS Credentials Setup")
    print("=" * 30)
    print("To use AWS Polly, you need:")
    print("1. AWS Access Key ID")
    print("2. AWS Secret Access Key") 
    print("3. AWS Region (e.g., us-east-1)")
    print()
    print("💡 You can set these via:")
    print("   aws configure")
    print("   or environment variables:")
    print("   export AWS_ACCESS_KEY_ID=your_key")
    print("   export AWS_SECRET_ACCESS_KEY=your_secret")
    print("   export AWS_DEFAULT_REGION=us-east-1")

def main():
    dolores = DoloresAWSVoice()
    
    if dolores.polly_client:
        dolores.test_aws_voice()
    else:
        setup_aws_credentials()

if __name__ == "__main__":
    main()