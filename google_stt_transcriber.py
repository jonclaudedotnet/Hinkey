#!/usr/bin/env python3
"""
Google Speech-to-Text Transcriber for Dolores Audio Captures
"""

import os
import json
from pathlib import Path
from google.cloud import speech
from claude_dolores_bridge import ask_dolores

class GoogleSTTTranscriber:
    def __init__(self, credentials_path=None):
        """Initialize Google STT client"""
        if credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        self.client = speech.SpeechClient()
        self.audio_dir = Path("./audio_captures")
        
    def transcribe_audio_file(self, audio_file_path):
        """Transcribe a single audio file"""
        audio_file = Path(audio_file_path)
        
        if not audio_file.exists():
            return None
            
        print(f"🎧 Transcribing: {audio_file.name}")
        
        # Read the audio file
        with open(audio_file, 'rb') as f:
            audio_content = f.read()
        
        # Configure the audio and recognition settings
        audio = speech.RecognitionAudio(content=audio_content)
        
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=44100,  # CD quality from arecord
            language_code="en-US",
            enable_automatic_punctuation=True,
            enable_word_time_offsets=True,
            model="latest_long"  # Better for longer audio
        )
        
        try:
            # Perform the transcription
            response = self.client.recognize(config=config, audio=audio)
            
            if not response.results:
                print("❌ No speech detected in audio")
                return None
            
            # Extract the transcription
            transcript = ""
            confidence_scores = []
            
            for result in response.results:
                transcript += result.alternatives[0].transcript + " "
                confidence_scores.append(result.alternatives[0].confidence)
            
            transcript = transcript.strip()
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            
            print(f"✅ Transcription complete (confidence: {avg_confidence:.2f})")
            print(f"📝 Text: {transcript[:100]}...")
            
            return {
                'transcript': transcript,
                'confidence': avg_confidence,
                'audio_file': str(audio_file),
                'word_count': len(transcript.split())
            }
            
        except Exception as e:
            print(f"❌ Transcription failed: {e}")
            return None
    
    def process_latest_audio(self):
        """Find and transcribe the most recent audio file"""
        audio_files = sorted(self.audio_dir.glob("voice_*.wav"))
        
        if not audio_files:
            print("No audio files found")
            return None
            
        latest_file = audio_files[-1]
        return self.transcribe_audio_file(latest_file)
    
    def send_to_dolores(self, transcription_result):
        """Send transcription to Dolores via bridge"""
        if not transcription_result:
            return None
            
        transcript = transcription_result['transcript']
        confidence = transcription_result['confidence']
        
        message = f"Jon Claude said: \"{transcript}\""
        
        task_id = ask_dolores(
            'voice_input',
            message,
            f'Voice transcription (confidence: {confidence:.2f})'
        )
        
        print(f"📡 Sent to Dolores (Task #{task_id})")
        return task_id
    
    def process_and_send_latest(self):
        """Complete workflow: transcribe latest audio and send to Dolores"""
        print("🚀 Processing latest audio capture...")
        
        transcription = self.process_latest_audio()
        if transcription:
            task_id = self.send_to_dolores(transcription)
            return transcription, task_id
        
        return None, None

def main():
    """Test the transcription system"""
    print("🎙️ Google STT Transcriber")
    print("=" * 40)
    
    # Check if credentials are set up
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        print("⚠️  Google Cloud credentials not found!")
        print("📋 Setup instructions:")
        print("1. Go to Google Cloud Console")
        print("2. Enable Speech-to-Text API")
        print("3. Create service account and download JSON key")
        print("4. Set: export GOOGLE_APPLICATION_CREDENTIALS=path/to/key.json")
        print()
        
        # For testing, we can still show the structure
        print("🧪 Testing with dummy credentials...")
        print("(This will fail but shows the workflow)")
    
    try:
        transcriber = GoogleSTTTranscriber()
        transcription, task_id = transcriber.process_and_send_latest()
        
        if transcription and task_id:
            print("🎯 Success! Voice input sent to Dolores")
            print(f"   Task ID: {task_id}")
            print(f"   Transcript: {transcription['transcript']}")
        else:
            print("❌ No audio to process or transcription failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure Google Cloud credentials are properly configured")

if __name__ == "__main__":
    main()