#!/usr/bin/env python3
"""
Start Dolores System - Launch daemon and studio together
"""

import subprocess
import time
import os
import signal

def cleanup_processes():
    """Clean up any existing Dolores processes"""
    try:
        subprocess.run(['pkill', '-f', 'dolores'], capture_output=True)
        time.sleep(2)
        print("🧹 Cleaned up existing processes")
    except:
        pass

def start_daemon():
    """Start Dolores daemon"""
    print("🤖 Starting Dolores daemon...")
    daemon_process = subprocess.Popen(
        ['python3', 'dolores_daemon.py'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(3)
    return daemon_process

def start_studio():
    """Start Dolores Studio UI"""
    print("🎙️ Starting Dolores Studio...")
    studio_process = subprocess.Popen(['python3', 'dolores_studio_simple.py'])
    return studio_process

def test_system():
    """Test that Dolores is responding"""
    print("🧪 Testing system...")
    test_process = subprocess.run([
        'python3', '-c', '''
from claude_dolores_bridge import ask_dolores, wait_for_dolores
task_id = ask_dolores("test", "Hello Dolores, are you online?", "System test")
result = wait_for_dolores(task_id, timeout=10)
print("✅ Test successful!" if result else "❌ Test failed!")
'''
    ])

def main():
    print("🚀 STARTING DOLORES SYSTEM")
    print("=" * 40)
    
    # Cleanup first
    cleanup_processes()
    
    # Start daemon
    daemon = start_daemon()
    
    # Test the daemon is working
    test_system()
    
    # Start studio
    studio = start_studio()
    
    print("\n✅ DOLORES SYSTEM ONLINE")
    print("- Daemon running in background")
    print("- Studio UI should open shortly")
    print("- Try asking me something to see Dolores respond!")
    
    try:
        # Keep script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        daemon.terminate()
        studio.terminate()

if __name__ == "__main__":
    main()