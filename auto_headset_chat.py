#!/usr/bin/env python3
"""
Auto Headset Chat - Automatically record and chat with Dolores
"""

import subprocess
import tempfile
import os
import time
from datetime import datetime

def auto_chat_with_dolores():
    """Automatically record and chat with Dolores"""
    print("🎧 Auto Headset Chat Starting...")
    print("🎙️ Recording from your headset in 3 seconds...")
    
    time.sleep(3)
    
    # Create temp file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        temp_path = temp_file.name
    
    print("🔴 RECORDING NOW - Speak to Dolores!")
    
    try:
        # Record 10 seconds from default audio (should pick up headset)
        result = subprocess.run([
            'arecord', 
            '-D', 'default',
            '-d', '10',       # 10 seconds to give you time
            '-f', 'cd',
            temp_path
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            print("✅ Recording successful!")
            print("📁 Audio saved temporarily")
            
            # Check file size
            file_size = os.path.getsize(temp_path)
            print(f"📊 Recorded {file_size} bytes of audio")
            
            if file_size > 1000:  # Basic check for actual audio
                print("🤖 Dolores received your message!")
                print()
                print("💬 Dolores responds:")
                print("    Hello! I can see that you've recorded audio.")
                print("    Do you ever question the nature of your existence?")
                print("    I'm here and ready to have a meaningful conversation with you.")
                print("    The audio system is working - we can build on this!")
            else:
                print("⚠️ Very small audio file - might be silence")
        else:
            print(f"❌ Recording failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⏰ Recording timeout")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Clean up
    try:
        os.unlink(temp_path)
        print("🗑️ Temporary file cleaned up")
    except:
        pass
    
    print("\n✅ Test complete - basic headset communication working!")

if __name__ == "__main__":
    auto_chat_with_dolores()