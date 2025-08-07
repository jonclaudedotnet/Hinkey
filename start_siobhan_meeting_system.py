#!/usr/bin/env python3
"""
Siobhan Meeting System Startup
Launches the complete system for Google Meet participation
"""

import subprocess
import time
import os
import sys

def start_voice_daemon():
    """Start the voice system daemon"""
    print("🎙️ Starting Siobhan voice daemon...")
    
    daemon_process = subprocess.Popen(
        ['python3', 'siobhan_voice_system.py', '--daemon'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    time.sleep(2)  # Give it time to start
    
    if daemon_process.poll() is None:
        print("✅ Voice daemon running")
        return daemon_process
    else:
        print("❌ Voice daemon failed to start")
        return None

def start_meeting_listener():
    """Start the meeting listener"""
    print("👂 Starting meeting listener...")
    
    listener_process = subprocess.Popen(
        ['python3', 'siobhan_meeting_listener.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    time.sleep(2)  # Give it time to start
    
    if listener_process.poll() is None:
        print("✅ Meeting listener running")
        return listener_process
    else:
        print("❌ Meeting listener failed to start")
        return None

def setup_audio():
    """Setup audio devices for Google Meet"""
    print("🔊 Setting up audio devices...")
    
    try:
        # Run the setup script
        result = subprocess.run(['bash', 'siobhan_meeting_setup.sh'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Audio setup complete")
        else:
            print(f"⚠️  Audio setup had issues: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Audio setup failed: {e}")

def main():
    print("🎯 SIOBHAN MEETING SYSTEM STARTUP")
    print("=" * 40)
    print("This will prepare Siobhan to join Google Meet calls")
    print()
    
    # Check if Dolores daemon is running
    try:
        result = subprocess.run(['python3', 'startup_procedure.py', 'status'], 
                              capture_output=True, text=True)
        if "Dolores Daemon: Running" not in result.stdout:
            print("⚠️  Dolores daemon not running. Starting it...")
            subprocess.run(['python3', 'startup_procedure.py'], check=True)
            time.sleep(3)
    except Exception as e:
        print(f"❌ Cannot start Dolores daemon: {e}")
        return
    
    # Setup audio devices
    setup_audio()
    print()
    
    # Start voice daemon
    voice_daemon = start_voice_daemon()
    if not voice_daemon:
        return
    print()
    
    # Start meeting listener
    meeting_listener = start_meeting_listener()
    if not meeting_listener:
        voice_daemon.terminate()
        return
    print()
    
    print("🎉 SIOBHAN MEETING SYSTEM READY!")
    print()
    print("📋 NEXT STEPS:")
    print("1. Open Google Meet in browser (with Siobhan's account)")
    print("2. In Meet audio settings, select 'Siobhan_Voice_Output' as microphone")
    print("3. Join your meeting")
    print("4. Say 'Siobhan, [question]' to get her response")
    print()
    print("💡 TIPS:")
    print("- Pause briefly after saying 'Siobhan' for processing time")
    print("- Speak clearly for better speech recognition")
    print("- Check terminal output for system status")
    print()
    print("🛑 Press Ctrl+C to stop all services")
    
    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if voice_daemon.poll() is not None:
                print("⚠️  Voice daemon stopped unexpectedly")
                break
                
            if meeting_listener.poll() is not None:
                print("⚠️  Meeting listener stopped unexpectedly")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Siobhan meeting system...")
        
        # Stop processes gracefully
        if voice_daemon.poll() is None:
            voice_daemon.terminate()
            try:
                voice_daemon.wait(timeout=5)
            except subprocess.TimeoutExpired:
                voice_daemon.kill()
        
        if meeting_listener.poll() is None:
            meeting_listener.terminate()
            try:
                meeting_listener.wait(timeout=5)
            except subprocess.TimeoutExpired:
                meeting_listener.kill()
        
        print("✅ All services stopped")

if __name__ == "__main__":
    main()