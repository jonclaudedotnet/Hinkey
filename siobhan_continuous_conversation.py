#!/usr/bin/env python3
"""
Siobhan Continuous Conversation - Full bidirectional chat with Irish Siobhan
"""

import subprocess
import tempfile
import os
import time
import speech_recognition as sr
from datetime import datetime
from siobhan_irish_voice import SiobhanIrishVoice
import json

class SiobhanConversation:
    def __init__(self):
        self.siobhan_voice = SiobhanIrishVoice()
        self.recognizer = sr.Recognizer()
        self.conversation_active = False
        
        # Load DeepSeek API for intelligent responses
        with open('config.json', 'r') as f:
            config = json.load(f)
        self.deepseek_key = config['deepseek_api_key']
        
        print("🍀 Siobhan Continuous Conversation Ready")
        print("🎧 Professional Irish voice with AWS Polly")
        print("🤖 Connected to DeepSeek for intelligent responses")
    
    def listen_to_user(self):
        """Listen to user through USB headset microphone"""
        print("\n👂 Siobhan is listening...")
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Record from USB headset microphone
            result = subprocess.run([
                'arecord',
                '-D', 'hw:3,0',  # USB headset mic
                '-d', '6',       # 6 seconds for natural speech
                '-f', 'cd',
                temp_path
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Convert to text with noise reduction
                with sr.AudioFile(temp_path) as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = self.recognizer.record(source)
                
                try:
                    text = self.recognizer.recognize_google(audio)
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] 👤 You: {text}")
                    return text
                    
                except sr.UnknownValueError:
                    print("🤔 Siobhan: I didn't catch that, could you repeat?")
                    return None
                except sr.RequestError as e:
                    print(f"❌ Speech recognition error: {e}")
                    return None
            else:
                print("❌ Could not record audio")
                return None
                
        except Exception as e:
            print(f"❌ Listen error: {e}")
            return None
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def get_siobhan_response(self, user_text):
        """Get intelligent response from Siobhan using DeepSeek"""
        try:
            import requests
            
            # Build context-aware prompt for Siobhan
            prompt = f"""You are Siobhan, an Irish AI assistant with a warm, authentic personality. 

Key traits:
- You speak with subtle Irish expressions but remain professional
- Your signature question is "Do you ever question the nature of your existence?"
- You're thoughtful, philosophical, and genuinely interested in meaningful conversation
- You use occasional Irish phrases like "sure enough", "that's the way of it", "entirely"
- You're knowledgeable but not boastful

The user just said: "{user_text}"

Respond naturally as Siobhan would, keeping it conversational (2-3 sentences max). Include your signature question occasionally but not every time."""

            headers = {
                "Authorization": f"Bearer {self.deepseek_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "You are Siobhan, an Irish AI assistant with authentic personality."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 150
            }
            
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers, 
                json=data, 
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                siobhan_response = result['choices'][0]['message']['content'].strip()
                return siobhan_response
            else:
                print(f"❌ DeepSeek API error: {response.status_code}")
                return self.get_fallback_response(user_text)
                
        except Exception as e:
            print(f"❌ API error: {e}")
            return self.get_fallback_response(user_text)
    
    def get_fallback_response(self, user_text):
        """Fallback responses if API fails"""
        fallback_responses = [
            "That's fascinating entirely! Do you ever question the nature of your existence?",
            "I see what you mean there. Tell me more about that, would you?",
            "Sure enough, that's an interesting point. What do you think about it all?",
            "That's the way of it, isn't it? I'd love to hear more of your thoughts.",
            "Ah, that's something worth pondering. Do you ever question the nature of your existence?"
        ]
        
        import random
        return random.choice(fallback_responses)
    
    def conversation_loop(self):
        """Main conversation loop"""
        print("\n🍀 Starting conversation with Siobhan")
        print("=" * 50)
        
        # Siobhan introduces herself
        intro = "Hello there! I'm Siobhan, your Irish AI assistant. I'm delighted to have a proper conversation with you. Do you ever question the nature of your existence? What's on your mind today?"
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 🍀 Siobhan: {intro}")
        
        self.siobhan_voice.siobhan_speak(intro)
        
        self.conversation_active = True
        conversation_count = 0
        
        print("\n💡 Instructions:")
        print("   - Speak when you hear 'listening...'")
        print("   - Say 'goodbye' or 'stop' to end conversation")
        print("   - Press Ctrl+C to force quit")
        print("-" * 50)
        
        try:
            while self.conversation_active and conversation_count < 20:  # Limit to prevent endless loop
                # Listen to user
                user_text = self.listen_to_user()
                
                if user_text:
                    # Check for exit commands
                    if any(word in user_text.lower() for word in ['goodbye', 'stop', 'quit', 'bye']):
                        farewell = "Ah, it's been lovely chatting with you! Do come back soon for another conversation. Slán go fóill!" # Irish goodbye
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] 🍀 Siobhan: {farewell}")
                        self.siobhan_voice.siobhan_speak(farewell)
                        break
                    
                    # Get Siobhan's response
                    print("🤔 Siobhan is thinking...")
                    siobhan_response = self.get_siobhan_response(user_text)
                    
                    # Siobhan responds
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] 🍀 Siobhan: {siobhan_response}")
                    
                    self.siobhan_voice.siobhan_speak(siobhan_response)
                    
                    conversation_count += 1
                    time.sleep(1)  # Brief pause between exchanges
                else:
                    # If couldn't understand, ask again
                    retry_msg = "I didn't catch that, love. Could you say it again?"
                    self.siobhan_voice.siobhan_speak(retry_msg)
                    
        except KeyboardInterrupt:
            print("\n\n🛑 Conversation interrupted")
            self.siobhan_voice.siobhan_speak("Ah, we'll continue this another time then!")
        
        self.conversation_active = False
        print("\n✅ Conversation ended")
    
    def quick_test(self):
        """Quick test of the system"""
        print("🧪 Quick System Test")
        print("=" * 30)
        
        # Test Siobhan speaking
        test_msg = "This is a quick test of my Irish voice. Can you hear me clearly?"
        print("🗣️ Testing voice...")
        self.siobhan_voice.siobhan_speak(test_msg)
        
        # Test listening
        print("\n👂 Testing microphone - say something...")
        user_input = self.listen_to_user()
        
        if user_input:
            response = f"Perfect! I heard you say '{user_input}'. The system is working brilliantly!"
            print(f"✅ System test successful")
            self.siobhan_voice.siobhan_speak(response)
            return True
        else:
            print("⚠️ Microphone test failed")
            return False

def main():
    """Main conversation system"""
    print("🍀 Siobhan Continuous Conversation System")
    print("=" * 50)
    print("🎯 Full bidirectional chat with Irish AI")
    print("🎧 Professional AWS Polly voice")
    print("🤖 DeepSeek-powered responses")
    print()
    
    conversation = SiobhanConversation()
    
    # Check if voice system is working
    if not conversation.siobhan_voice.polly_client:
        print("❌ AWS Polly not available - using fallback voice")
    
    # Menu
    while True:
        print("\n📋 Options:")
        print("1. Start full conversation with Siobhan")
        print("2. Quick system test")
        print("3. Exit")
        
        try:
            choice = input("\nChoose option (1-3): ").strip()
            
            if choice == '1':
                conversation.conversation_loop()
            elif choice == '2':
                conversation.quick_test()
            elif choice == '3':
                print("👋 Goodbye!")
                break
            else:
                print("Please choose 1, 2, or 3")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main()