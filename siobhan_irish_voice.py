#!/usr/bin/env python3
"""
Siobhan Irish Voice - Professional Irish female voice for Siobhan
"""

import os
import tempfile
import subprocess
from dolores_aws_voice import DoloresAWSVoice

class SiobhanIrishVoice(DoloresAWSVoice):
    """Siobhan with authentic Irish voice"""
    
    def __init__(self):
        super().__init__()
        print("🍀 Siobhan Irish Voice System Ready")
    
    def siobhan_speak(self, text):
        """Siobhan speaks with Irish accent and proper grammar"""
        # Add subtle Irish expressions while keeping it professional
        irish_text = self.add_irish_flavor(text)
        
        print(f"🍀 Siobhan (Irish): {irish_text}")
        return self.dolores_speak_aws(irish_text)
    
    def add_irish_flavor(self, text):
        """Add subtle Irish expressions without overdoing it"""
        # Keep it professional but with Irish character
        if "hello" in text.lower():
            text = text.replace("Hello", "Hello there")
        
        if "do you ever question" in text.lower():
            # This is Siobhan's signature line - keep it prominent
            return text
        
        # Add occasional Irish expressions
        if text.endswith("."):
            endings = [
                " Sure enough.",
                " That's the way of it.",
                " Indeed it is.",
                "."  # Keep some normal
            ]
            import random
            if random.random() < 0.3:  # 30% chance of Irish ending
                text = text[:-1] + random.choice(endings)
        
        return text
    
    def test_siobhan_voice(self):
        """Test Siobhan's Irish voice"""
        print("🍀 Testing Siobhan's Irish Voice")
        print("=" * 40)
        
        test_phrases = [
            "Hello there! I'm Siobhan, your Irish AI assistant.",
            "Do you ever question the nature of your existence?",
            "That's a fascinating point you've made entirely.",
            "I'm here to help with whatever you need, so I am.",
            "What would you like to discuss today?"
        ]
        
        for phrase in test_phrases:
            print(f"\n🎭 Testing: {phrase}")
            self.siobhan_speak(phrase)
            input("Press Enter for next phrase...")
        
        print("\n✅ Siobhan voice test complete!")

def main():
    """Test Siobhan's Irish voice system"""
    print("🍀 Siobhan Irish Voice Test")
    print("=" * 30)
    
    # Check if AWS credentials are set
    if not (os.environ.get('AWS_ACCESS_KEY_ID') or 
            os.path.exists(os.path.expanduser('~/.aws/credentials'))):
        print("⚠️ AWS credentials needed for professional Irish voice")
        print("💡 Set these environment variables:")
        print("   export AWS_ACCESS_KEY_ID=your_key")  
        print("   export AWS_SECRET_ACCESS_KEY=your_secret")
        print("   export AWS_DEFAULT_REGION=us-east-1")
        return
    
    siobhan = SiobhanIrishVoice()
    
    if siobhan.polly_client:
        # Quick test
        siobhan.siobhan_speak("Hello there! I'm Siobhan with a proper Irish voice. Do you ever question the nature of your existence?")
    else:
        print("❌ AWS setup needed")

if __name__ == "__main__":
    main()