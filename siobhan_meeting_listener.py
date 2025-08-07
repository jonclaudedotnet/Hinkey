#!/usr/bin/env python3
"""
Siobhan Meeting Listener - Real-time meeting audio capture and processing
Listens to Google Meet, transcribes conversations, responds to wake word
"""

import subprocess
import threading
import time
import queue
import speech_recognition as sr
from pathlib import Path
from datetime import datetime
import re
from claude_dolores_bridge import ask_dolores, wait_for_dolores

class MeetingAudioCapture:
    def __init__(self):
        # Audio capture setup
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.audio_queue = queue.Queue()
        self.transcript_buffer = []
        
        # Meeting context
        self.meeting_context = ""
        self.last_speaker_time = time.time()
        
        # Wake word detection
        self.wake_words = ["siobhan", "siobhan,", "siobhan?"]
        self.listening_for_response = False
        
        # Processing state
        self.processing_response = False
        
    def setup_meeting_audio_input(self):
        """Set up audio input to capture meeting audio"""
        # Create virtual input to capture meeting audio
        print("🎧 Setting up meeting audio capture...")
        
        # This captures the audio that would go to speakers (meeting audio)
        cmd = [
            'pactl', 'load-module', 'module-null-sink',
            'sink_name=meeting_capture',
            'sink_properties=device.description="Meeting_Audio_Capture"'
        ]
        
        try:
            subprocess.run(cmd)
            print("✅ Meeting audio capture device created")
            
            # Set up loopback so meeting participants can still hear
            loopback_cmd = [
                'pactl', 'load-module', 'module-loopback',
                'source=meeting_capture.monitor',
                'latency_msec=1'
            ]
            subprocess.run(loopback_cmd)
            
        except subprocess.CalledProcessError:
            print("⚠️  Audio capture device may already exist")
    
    def start_listening(self):
        """Start listening to meeting audio"""
        print("👂 Starting meeting audio listener...")
        
        # Find the microphone (we'll use default for now)
        try:
            self.microphone = sr.Microphone()
            
            # Adjust for ambient noise
            with self.microphone as source:
                print("🔧 Calibrating for background noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
                
        except Exception as e:
            print(f"❌ Microphone setup failed: {e}")
            return False
            
        # Start background listening
        self.stop_listening = self.recognizer.listen_in_background(
            self.microphone, self.audio_callback, phrase_time_limit=5
        )
        
        print("✅ Meeting listener started")
        return True
    
    def audio_callback(self, recognizer, audio):
        """Process audio chunks from the meeting"""
        try:
            # Transcribe the audio
            text = recognizer.recognize_google(audio).lower()
            
            if text.strip():
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] Heard: {text}")
                
                # Add to transcript buffer
                self.transcript_buffer.append(f"[{timestamp}] {text}")
                
                # Keep only last 20 entries for context
                if len(self.transcript_buffer) > 20:
                    self.transcript_buffer.pop(0)
                
                # Update meeting context
                self.meeting_context = "\n".join(self.transcript_buffer[-10:])
                
                # Check for wake word
                self.check_for_wake_word(text)
                
        except sr.UnknownValueError:
            # Speech not recognized - this is normal
            pass
        except sr.RequestError as e:
            print(f"⚠️  Speech recognition error: {e}")
    
    def check_for_wake_word(self, text):
        """Check if Siobhan was mentioned"""
        text_lower = text.lower()
        
        for wake_word in self.wake_words:
            if wake_word in text_lower:
                print(f"🎯 Wake word detected: '{wake_word}'")
                
                # Extract the question/context after the wake word
                parts = text_lower.split(wake_word, 1)
                if len(parts) > 1:
                    question_context = parts[1].strip()
                else:
                    question_context = "respond to the current conversation"
                
                # Trigger response
                self.trigger_siobhan_response(question_context)
                break
    
    def trigger_siobhan_response(self, question_context):
        """Get Siobhan to respond based on meeting context"""
        if self.processing_response:
            print("⏳ Siobhan is still processing previous response...")
            return
        
        self.processing_response = True
        print("🤔 Siobhan is processing the meeting context...")
        
        # Build full context for Dolores
        full_context = f"""
Meeting Context (last few minutes of conversation):
{self.meeting_context}

Question/Request: {question_context}

Please provide a brief, natural response suitable for a Google Meet call. 
Be conversational and helpful based on the meeting context.
"""

        # Get response from Dolores
        task_id = ask_dolores(
            'meeting_response',
            full_context,
            'Live meeting response with context'
        )
        
        # Wait for response (with timeout)
        response = wait_for_dolores(task_id, timeout=15)
        
        if response:
            # Clean up the response for speaking
            clean_response = self.clean_response_for_speech(response)
            
            print(f"💬 Siobhan will respond: {clean_response[:100]}...")
            
            # Add to voice command database for daemon to process
            self.add_voice_command(clean_response)
            
        else:
            print("⚠️  Siobhan didn't respond in time")
        
        self.processing_response = False
    
    def add_voice_command(self, text):
        """Add voice command to database for daemon processing"""
        import sqlite3
        import os
        from datetime import datetime
        
        db_path = os.path.join(os.path.dirname(__file__), 'claude_dolores_bridge', 'shared_tasks.db')
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Insert voice command task with meeting context metadata
            cursor.execute("""
                INSERT INTO tasks (timestamp, requester, task_type, content, context, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                'meeting_listener',
                'voice_command',
                text,
                f'Meeting response - Context: {self.meeting_context[-200:]}...' if len(self.meeting_context) > 200 else f'Meeting response - Context: {self.meeting_context}',
                'pending'
            ))
            
            task_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            print(f"🎤 Added voice command to queue (task #{task_id})")
            
        except Exception as e:
            print(f"⚠️  Failed to add voice command: {e}")
    
    def clean_response_for_speech(self, response):
        """Clean Dolores response for natural speech"""
        # Remove LEARN entries
        clean = re.sub(r'\*\*LEARN.*?\*\*.*?(?=\n\n|\Z)', '', response, flags=re.DOTALL)
        clean = re.sub(r'LEARN:.*?(?=\n[A-Z]|\n\n|\Z)', '', clean, flags=re.DOTALL)
        
        # Remove task markers
        clean = re.sub(r'\*\*Task.*?\*\*\s*', '', clean)
        clean = re.sub(r'---.*?(?=\n\n|\Z)', '', clean, flags=re.DOTALL)
        
        # Clean up formatting
        clean = re.sub(r'\*\*(.*?)\*\*', r'\1', clean)  # Remove bold
        clean = re.sub(r'\n\s*\n\s*\n', '\n\n', clean)  # Normalize spacing
        clean = clean.strip()
        
        return clean
    
    def get_meeting_summary(self):
        """Get summary of what's been discussed"""
        if not self.transcript_buffer:
            return "No meeting content captured yet."
        
        return f"Meeting discussion (last {len(self.transcript_buffer)} exchanges):\n{self.meeting_context}"
    
    def stop(self):
        """Stop listening"""
        if hasattr(self, 'stop_listening'):
            self.stop_listening(wait_for_stop=False)
        print("👋 Meeting listener stopped")

def main():
    """Main meeting listener"""
    print("🎙️ Siobhan Meeting Listener")
    print("=" * 40)
    print("This system will:")
    print("1. Listen to your Google Meet audio")
    print("2. Transcribe conversations in real-time") 
    print("3. Respond when someone says 'Siobhan'")
    print("4. Give contextual responses based on meeting discussion")
    print()
    
    listener = MeetingAudioCapture()
    
    # Setup audio capture
    listener.setup_meeting_audio_input()
    
    # Start listening
    if not listener.start_listening():
        print("❌ Failed to start listening")
        return
    
    print("\n📋 Meeting listener is active!")
    print("💡 Say 'Siobhan, what do you think?' in your meeting")
    print("⏳ Participants should pause briefly for AI processing time")
    print("📝 Type 'summary' to see meeting transcript")
    print("🛑 Type 'quit' to stop")
    print("-" * 40)
    
    try:
        while True:
            cmd = input("\n> ").strip().lower()
            
            if cmd == 'quit':
                break
            elif cmd == 'summary':
                print("\n" + listener.get_meeting_summary())
            elif cmd == 'context':
                print(f"\nCurrent context buffer:\n{listener.meeting_context}")
            else:
                print("Commands: 'summary', 'context', 'quit'")
                
    except KeyboardInterrupt:
        pass
    
    print("\n🛑 Shutting down meeting listener...")
    listener.stop()

if __name__ == "__main__":
    main()