#!/usr/bin/env python3
"""
Siobhan Continuous Listener - Rolling audio buffer with 30-minute auto-purge
Continuously records meeting audio but automatically discards old recordings
"""

import sounddevice as sd
import numpy as np
import speech_recognition as sr
import threading
import time
import sqlite3
from datetime import datetime, timedelta
import json
import wave
from collections import deque
import os
from pathlib import Path
import tempfile

class SiobhanContinuousListener:
    """Continuous meeting audio monitoring with rolling buffer and auto-purge"""
    
    def __init__(self, buffer_duration_minutes: int = 30):
        self.recognizer = sr.Recognizer()
        self.wake_word = "siobhan"
        self.is_recording = False
        
        # Rolling audio buffer settings
        self.buffer_duration = buffer_duration_minutes * 60  # Convert to seconds
        self.sample_rate = 16000  # 16kHz for speech recognition
        self.chunk_duration = 5   # Process 5-second chunks
        self.chunk_size = self.sample_rate * self.chunk_duration
        
        # Audio storage - rolling buffer
        self.audio_chunks = deque()     # Store audio data
        self.chunk_timestamps = deque() # Store chunk timestamps
        self.audio_lock = threading.Lock()
        
        # Meeting context
        self.conversation_buffer = deque(maxlen=50)  # Last 50 utterances
        
        # Database for voice commands
        self.db_path = "claude_dolores_bridge/shared_tasks.db"
        self.init_database()
        
        # Temporary directory for processing
        self.temp_dir = Path(tempfile.mkdtemp(prefix="siobhan_audio_"))
        
        print("🎧 Siobhan Continuous Listener initialized")
        print(f"🔍 Wake word: '{self.wake_word}'")
        print(f"⏰ Rolling buffer: {buffer_duration_minutes} minutes")
        print(f"📁 Temp directory: {self.temp_dir}")
    
    def init_database(self):
        """Initialize shared database for voice commands"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Ensure tasks table exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    requester TEXT,
                    task_type TEXT,
                    content TEXT,
                    context TEXT,
                    status TEXT DEFAULT 'pending',
                    result TEXT,
                    completed_at TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            print("✅ Voice command database ready")
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
    
    def find_meeting_audio_device(self):
        """Find the default monitor device (simple approach - monitors system audio)"""
        try:
            devices = sd.query_devices()
            
            # Look for default monitor (captures all system audio)
            for i, device in enumerate(devices):
                if isinstance(device, dict):
                    name = device.get('name', '').lower()
                    # Look for the default system monitor
                    if ('monitor' in name and 
                        ('default' in name or 'built-in' in name or 'analog' in name) and
                        device.get('max_input_channels', 0) > 0):
                        print(f"🎯 Found system audio monitor: {device['name']}")
                        return i
            
            # Fallback: Any monitor device that can capture audio
            for i, device in enumerate(devices):
                if isinstance(device, dict):
                    name = device.get('name', '').lower()
                    if ('monitor' in name and 
                        device.get('max_input_channels', 0) > 0):
                        print(f"🔍 Found audio monitor device: {device['name']}")
                        return i
            
            # Final fallback: Default microphone
            print("⚠️ No audio monitor found, using default microphone")
            print("   Siobhan will listen to default microphone instead of system audio")
            print("   This means she'll hear you speaking but not the meeting audio")
            return None
            
        except Exception as e:
            print(f"❌ Device detection error: {e}")
            return None
    
    def audio_callback(self, indata, frames, time_info, status):
        """Continuous audio recording callback"""
        if status:
            print(f"⚠️ Audio status: {status}")
        
        current_time = datetime.now()
        
        with self.audio_lock:
            # Add new audio chunk
            self.audio_chunks.append(indata.copy().flatten())
            self.chunk_timestamps.append(current_time)
            
            # Auto-purge old audio (older than buffer_duration)
            cutoff_time = current_time - timedelta(seconds=self.buffer_duration)
            
            while (self.chunk_timestamps and 
                   self.chunk_timestamps[0] < cutoff_time):
                # Remove old chunks
                old_chunk = self.audio_chunks.popleft()
                old_timestamp = self.chunk_timestamps.popleft()
                
                # Optional: Log purged data stats (no content stored)
                if len(self.chunk_timestamps) % 100 == 0:  # Every 100 chunks
                    print(f"🗑️ Purged audio chunk from {old_timestamp.strftime('%H:%M:%S')}")
    
    def start_continuous_recording(self):
        """Start continuous audio recording with auto-purge"""
        print("🎙️ Starting continuous audio recording...")
        print(f"📊 Buffer will maintain last {self.buffer_duration//60} minutes of audio")
        
        # Try to find the meeting audio capture device
        meeting_device_id = self.find_meeting_audio_device()
        
        try:
            self.is_recording = True
            
            # Start audio stream from meeting capture device
            stream_kwargs = {
                'callback': self.audio_callback,
                'channels': 1,
                'samplerate': self.sample_rate,
                'blocksize': 1024,
                'dtype': np.float32
            }
            
            # Use meeting audio device if found
            if meeting_device_id is not None:
                stream_kwargs['device'] = meeting_device_id
                print(f"🔊 Recording from meeting audio device (ID: {meeting_device_id})")
            else:
                print("🎤 Recording from default microphone")
            
            with sd.InputStream(**stream_kwargs):
                print("✅ Recording active - audio auto-purges every 30 minutes")
                
                # Start background processing thread
                processing_thread = threading.Thread(target=self.process_audio_continuously)
                processing_thread.daemon = True
                processing_thread.start()
                
                # Start cleanup thread for temp files
                cleanup_thread = threading.Thread(target=self.cleanup_temp_files)
                cleanup_thread.daemon = True
                cleanup_thread.start()
                
                # Status thread
                status_thread = threading.Thread(target=self.print_status_updates)
                status_thread.daemon = True
                status_thread.start()
                
                # Keep recording until stopped
                while self.is_recording:
                    time.sleep(1)
                    
        except Exception as e:
            print(f"❌ Recording error: {e}")
            self.is_recording = False
    
    def process_audio_continuously(self):
        """Process audio for wake word detection every few seconds"""
        print("🔍 Starting wake word detection...")
        
        while self.is_recording:
            try:
                # Process every 3 seconds
                time.sleep(3)
                
                current_time = datetime.now()
                
                with self.audio_lock:
                    if not self.audio_chunks:
                        continue
                    
                    # Get recent audio (last 10 seconds for processing)
                    recent_cutoff = current_time - timedelta(seconds=10)
                    recent_audio = []
                    
                    for i, timestamp in enumerate(self.chunk_timestamps):
                        if timestamp >= recent_cutoff:
                            recent_audio.extend(self.audio_chunks[i])
                
                if recent_audio and len(recent_audio) > self.sample_rate:  # At least 1 second
                    # Process this audio chunk
                    self.process_audio_chunk(recent_audio, current_time)
                
            except Exception as e:
                print(f"❌ Audio processing error: {e}")
                time.sleep(1)
    
    def process_audio_chunk(self, audio_data, timestamp):
        """Process audio chunk for speech recognition"""
        try:
            # Convert to numpy array and normalize
            audio_array = np.array(audio_data, dtype=np.float32)
            
            # Save as temporary WAV file
            temp_file = self.temp_dir / f"chunk_{int(timestamp.timestamp())}.wav"
            self.save_audio_to_wav(audio_array, temp_file)
            
            # Recognize speech
            with sr.AudioFile(str(temp_file)) as source:
                audio = self.recognizer.record(source)
            
            text = self.recognizer.recognize_google(audio, language='en-US')
            
            if text.strip():
                time_str = timestamp.strftime("%H:%M:%S")
                print(f"[{time_str}] 🎤 {text}")
                
                # Add to conversation buffer
                self.conversation_buffer.append({
                    'timestamp': timestamp,
                    'text': text
                })
                
                # Check for wake word
                if self.wake_word.lower() in text.lower():
                    print(f"🔔 Wake word detected!")
                    self.handle_wake_word_activation(text)
            
            # Clean up temp file immediately
            if temp_file.exists():
                temp_file.unlink()
                
        except sr.UnknownValueError:
            # No speech detected - normal, don't log
            pass
        except sr.RequestError as e:
            print(f"❌ Speech recognition error: {e}")
        except Exception as e:
            print(f"❌ Chunk processing error: {e}")
        finally:
            # Always clean up temp file
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except:
                pass
    
    def save_audio_to_wav(self, audio_data, file_path):
        """Save audio array to WAV file"""
        try:
            # Normalize to 16-bit range
            audio_normalized = (audio_data * 32767).astype(np.int16)
            
            with wave.open(str(file_path), 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_normalized.tobytes())
                
        except Exception as e:
            print(f"❌ Audio save error: {e}")
    
    def handle_wake_word_activation(self, full_text):
        """Handle when Siobhan wake word is detected"""
        # Extract command after wake word
        text_lower = full_text.lower()
        wake_index = text_lower.find(self.wake_word.lower())
        
        if wake_index >= 0:
            command = full_text[wake_index + len(self.wake_word):].strip()
            if not command:
                command = "respond to the current conversation"
        else:
            command = full_text
        
        # Get recent context
        context = self.get_recent_conversation_context()
        
        print(f"🤔 Processing command: {command}")
        print(f"📝 Context: {len(context)} characters of recent conversation")
        
        # Add to voice command database
        self.add_voice_command(command, context)
    
    def get_recent_conversation_context(self) -> str:
        """Get recent meeting context for AI response"""
        if not self.conversation_buffer:
            return ""
        
        # Get last 10 utterances for context
        recent_items = list(self.conversation_buffer)[-10:]
        
        context_lines = []
        for item in recent_items:
            time_str = item['timestamp'].strftime("%H:%M:%S")
            context_lines.append(f"[{time_str}] {item['text']}")
        
        return "\n".join(context_lines)
    
    def add_voice_command(self, command_text: str, context: str = ""):
        """Add voice command to database for processing"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            full_context = f"Meeting conversation context:\n{context}\n\nCommand: {command_text}"
            
            cursor.execute("""
                INSERT INTO tasks (timestamp, requester, task_type, content, context, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                'continuous_listener',
                'voice_command',
                command_text,
                full_context,
                'pending'
            ))
            
            task_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            print(f"🗣️ Voice command queued (task #{task_id}): {command_text}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to add voice command: {e}")
            return False
    
    def cleanup_temp_files(self):
        """Periodically clean up old temporary files"""
        while self.is_recording:
            try:
                time.sleep(60)  # Clean up every minute
                
                cutoff_time = datetime.now() - timedelta(minutes=5)
                
                for temp_file in self.temp_dir.glob("*.wav"):
                    try:
                        file_time = datetime.fromtimestamp(temp_file.stat().st_mtime)
                        if file_time < cutoff_time:
                            temp_file.unlink()
                    except Exception:
                        pass
                        
            except Exception as e:
                print(f"❌ Cleanup error: {e}")
    
    def print_status_updates(self):
        """Print periodic status updates"""
        while self.is_recording:
            try:
                time.sleep(300)  # Every 5 minutes
                
                with self.audio_lock:
                    chunk_count = len(self.audio_chunks)
                    if self.chunk_timestamps:
                        oldest = self.chunk_timestamps[0]
                        newest = self.chunk_timestamps[-1]
                        buffer_duration = (newest - oldest).total_seconds() / 60
                    else:
                        buffer_duration = 0
                
                print(f"📊 Status: {chunk_count} chunks in buffer, {buffer_duration:.1f} min duration")
                print(f"💬 Conversation: {len(self.conversation_buffer)} recent utterances")
                
            except Exception as e:
                print(f"❌ Status error: {e}")
    
    def get_buffer_status(self) -> dict:
        """Get detailed buffer status"""
        with self.audio_lock:
            total_chunks = len(self.audio_chunks)
            if self.chunk_timestamps:
                oldest = self.chunk_timestamps[0]
                newest = self.chunk_timestamps[-1]
                duration = (newest - oldest).total_seconds()
            else:
                duration = 0
        
        return {
            'total_chunks': total_chunks,
            'buffer_duration_seconds': duration,
            'buffer_duration_minutes': duration / 60,
            'max_duration_minutes': self.buffer_duration / 60,
            'conversation_items': len(self.conversation_buffer),
            'is_recording': self.is_recording,
            'temp_dir': str(self.temp_dir)
        }
    
    def stop(self):
        """Stop recording and clean up"""
        print("🛑 Stopping continuous listener...")
        self.is_recording = False
        
        # Clean up temp directory
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            print(f"🗑️ Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            print(f"⚠️ Temp cleanup error: {e}")
        
        print("✅ Continuous listener stopped - all audio data purged")

def main():
    """Main continuous listener"""
    print("🎙️ Siobhan Continuous Listener")
    print("=" * 50)
    print("🔄 CONTINUOUS RECORDING WITH AUTO-PURGE")
    print("=" * 50)
    print("This system will:")
    print("1. 🎧 Continuously record meeting audio")
    print("2. ⏰ Automatically purge audio older than 30 minutes")
    print("3. 🔍 Monitor for wake word 'Siobhan'")
    print("4. 💬 Provide contextual responses")
    print("5. 🗑️ Never store audio permanently")
    print()
    print("⚡ PRIVACY: Audio automatically deleted every 30 minutes!")
    print()
    
    # Ask for buffer duration
    try:
        buffer_minutes = input("🕐 Buffer duration in minutes (default 30): ").strip()
        if buffer_minutes:
            buffer_minutes = int(buffer_minutes)
        else:
            buffer_minutes = 30
    except ValueError:
        buffer_minutes = 30
    
    listener = SiobhanContinuousListener(buffer_duration_minutes=buffer_minutes)
    
    print(f"\n🚀 Starting with {buffer_minutes}-minute rolling buffer...")
    print("📋 Commands while running:")
    print("  'status' - Show buffer status")
    print("  'context' - Show recent conversation")
    print("  'quit' - Stop and purge all data")
    print("-" * 50)
    
    # Start recording in background thread
    recording_thread = threading.Thread(target=listener.start_continuous_recording)
    recording_thread.daemon = True
    recording_thread.start()
    
    try:
        while listener.is_recording:
            cmd = input("\n> ").strip().lower()
            
            if cmd == 'quit':
                break
            elif cmd == 'status':
                status = listener.get_buffer_status()
                print(f"\n📊 Buffer Status:")
                print(f"   Chunks: {status['total_chunks']}")
                print(f"   Duration: {status['buffer_duration_minutes']:.1f}/{status['max_duration_minutes']} minutes")
                print(f"   Conversation: {status['conversation_items']} recent utterances")
                print(f"   Recording: {status['is_recording']}")
            elif cmd == 'context':
                context = listener.get_recent_conversation_context()
                print(f"\n💬 Recent Conversation:\n{context}")
            elif cmd == '':
                continue
            else:
                print("Commands: 'status', 'context', 'quit'")
                
    except KeyboardInterrupt:
        pass
    
    print("\n🛑 Shutting down...")
    listener.stop()

if __name__ == "__main__":
    main()