#!/usr/bin/env python3
"""
Complete Integration Test - Tests the full meeting voice system
1. Simulates wake word detection in meeting listener
2. Verifies voice command gets added to database 
3. Confirms voice daemon processes and speaks the command
"""

import sqlite3
import os
import time
import subprocess
import signal
from datetime import datetime

def simulate_meeting_trigger():
    """Simulate the meeting listener detecting 'Siobhan' and generating a response"""
    print("🎯 Simulating meeting wake word detection...")
    
    # Import the meeting listener class
    from siobhan_meeting_listener import MeetingAudioCapture
    
    # Create listener instance
    listener = MeetingAudioCapture()
    
    # Simulate some meeting context
    listener.meeting_context = """
[14:30:15] participant1: So what do you all think about the new project timeline?
[14:30:18] participant2: I think it's aggressive but doable
[14:30:22] participant1: Siobhan, what's your perspective on this?
"""
    
    # Simulate wake word detection
    print("💬 Simulating: 'Siobhan, what's your perspective on this?'")
    listener.trigger_siobhan_response("what's your perspective on this")
    
    print("✅ Meeting trigger simulation complete")

def check_voice_command_created():
    """Check if voice command was added to database"""
    db_path = os.path.join(os.path.dirname(__file__), 'claude_dolores_bridge', 'shared_tasks.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check for recent voice commands
        cursor.execute("""
            SELECT id, content, status FROM tasks 
            WHERE task_type = 'voice_command' 
            AND requester = 'meeting_listener'
            ORDER BY id DESC LIMIT 1
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            task_id, content, status = result
            print(f"✅ Voice command found in database:")
            print(f"   Task ID: {task_id}")
            print(f"   Content: {content[:100]}...")
            print(f"   Status: {status}")
            return task_id
        else:
            print("❌ No voice command found in database")
            return None
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None

def test_voice_daemon_processing(task_id):
    """Test that voice daemon processes the command"""
    print("🎙️ Starting voice daemon to process command...")
    
    # Start voice daemon
    daemon_process = subprocess.Popen(
        ['python3', 'siobhan_voice_system.py', '--daemon'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give it time to process
    time.sleep(5)
    
    # Check if task was processed
    db_path = os.path.join(os.path.dirname(__file__), 'claude_dolores_bridge', 'shared_tasks.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] == 'completed':
            print("✅ Voice daemon successfully processed the command!")
            print("🗣️ Siobhan should have spoken the response")
        else:
            print(f"⚠️  Task status: {result[0] if result else 'Not found'}")
            
    except Exception as e:
        print(f"❌ Database check error: {e}")
    
    # Stop the daemon
    daemon_process.terminate()
    try:
        daemon_process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        daemon_process.kill()
    
    print("🛑 Voice daemon stopped")

def main():
    print("🎯 COMPLETE SIOBHAN VOICE INTEGRATION TEST")
    print("=" * 50)
    print("This test simulates the full meeting participation flow:")
    print("1. Meeting listener detects wake word")
    print("2. Dolores generates contextual response") 
    print("3. Response added to voice command database")
    print("4. Voice daemon processes and speaks response")
    print()
    
    # Step 1: Simulate meeting trigger
    simulate_meeting_trigger()
    print()
    
    # Step 2: Check if voice command was created
    task_id = check_voice_command_created()
    print()
    
    if task_id:
        # Step 3: Test voice daemon processing
        test_voice_daemon_processing(task_id)
    else:
        print("❌ Cannot test voice daemon - no voice command created")
    
    print()
    print("🎉 INTEGRATION TEST COMPLETE!")
    print("If you heard Siobhan speak a response, the full system is working!")

if __name__ == "__main__":
    main()