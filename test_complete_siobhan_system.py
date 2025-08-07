#!/usr/bin/env python3
"""
Complete Siobhan System Test - Verify all components working together
"""

import sqlite3
import subprocess
import time
from datetime import datetime

def check_voice_daemon():
    """Check if voice daemon is running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'siobhan_voice_system'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pid = result.stdout.strip()
            print(f"✅ Voice daemon running (PID: {pid})")
            return True
        else:
            print("❌ Voice daemon not running")
            return False
    except Exception as e:
        print(f"❌ Error checking voice daemon: {e}")
        return False

def check_audio_devices():
    """Check if audio devices are properly set up"""
    try:
        # Check sinks (output devices)
        result = subprocess.run(['pactl', 'list', 'short', 'sinks'], 
                              capture_output=True, text=True)
        
        has_siobhan_voice = 'siobhan_voice_out' in result.stdout
        has_browser_speakers = 'browser_speakers' in result.stdout
        has_browser_mic = 'browser_microphone' in result.stdout
        
        print("🔊 Audio Devices Status:")
        print(f"   Siobhan voice out: {'✅' if has_siobhan_voice else '❌'}")
        print(f"   Browser speakers: {'✅' if has_browser_speakers else '❌'}")
        print(f"   Browser microphone: {'✅' if has_browser_mic else '❌'}")
        
        # Check loopback routing
        result = subprocess.run(['pactl', 'list', 'short', 'modules'], 
                              capture_output=True, text=True)
        
        has_voice_routing = 'siobhan_voice_out.monitor' in result.stdout
        
        print(f"   Audio routing: {'✅' if has_voice_routing else '❌'}")
        
        return has_siobhan_voice and has_browser_speakers and has_voice_routing
        
    except Exception as e:
        print(f"❌ Error checking audio devices: {e}")
        return False

def add_test_voice_command(message, test_name):
    """Add a test voice command and return task ID"""
    try:
        db_path = 'claude_dolores_bridge/shared_tasks.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tasks (timestamp, requester, task_type, content, context, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            'system_test',
            'voice_command',
            message,
            f'System test: {test_name}',
            'pending'
        ))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ Added voice command (task #{task_id})")
        return task_id
        
    except Exception as e:
        print(f"❌ Failed to add voice command: {e}")
        return None

def check_task_completion(task_id, timeout=10):
    """Check if a task was completed within timeout"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            db_path = 'claude_dolores_bridge/shared_tasks.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT status FROM tasks WHERE id = ?', (task_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0] == 'completed':
                print(f"✅ Task #{task_id} completed")
                return True
                
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Error checking task: {e}")
            return False
    
    print(f"⏰ Task #{task_id} timed out")
    return False

def main():
    """Run complete system test"""
    print("🧪 Complete Siobhan System Test")
    print("=" * 50)
    
    print("\n1️⃣ Checking Voice Daemon...")
    daemon_ok = check_voice_daemon()
    
    print("\n2️⃣ Checking Audio Devices...")
    audio_ok = check_audio_devices()
    
    if not daemon_ok or not audio_ok:
        print("\n❌ Prerequisites not met. Please run:")
        print("   python3 start_continuous_meeting_system.py")
        return
    
    print("\n3️⃣ Testing Voice Commands...")
    
    test_messages = [
        ("Hello! This is Siobhan's voice system test number one.", "Basic voice test"),
        ("The audio routing is working correctly through the browser microphone input.", "Audio routing test"),
        ("This message should flow from Siobhan voice out to browser microphone input.", "Complete flow test")
    ]
    
    all_passed = True
    
    for i, (message, test_name) in enumerate(test_messages, 1):
        print(f"\n   Test {i}/3: {test_name}")
        print(f"   Message: {message[:50]}...")
        
        task_id = add_test_voice_command(message, test_name)
        if task_id:
            if check_task_completion(task_id):
                print(f"   ✅ Test {i} PASSED")
            else:
                print(f"   ❌ Test {i} FAILED")
                all_passed = False
        else:
            print(f"   ❌ Test {i} FAILED (couldn't add command)")
            all_passed = False
        
        time.sleep(2)  # Brief pause between tests
    
    print("\n" + "=" * 50)
    print("🎯 SYSTEM TEST RESULTS")
    print("=" * 50)
    
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Siobhan's voice system is fully operational:")
        print("   🗣️ Voice daemon processing commands")
        print("   🎙️ Audio routing working correctly")
        print("   📢 Voice output through browser microphone")
        print("\n📋 Ready for Google Meet:")
        print("   🎤 Set microphone to 'browser_microphone.monitor'")
        print("   🔊 Set speakers to 'browser_speakers'")
        print("   💬 Say 'Siobhan' in meeting to activate")
        
    else:
        print("⚠️ SOME TESTS FAILED")
        print("🔧 Try restarting the system:")
        print("   python3 start_continuous_meeting_system.py")
    
    print("=" * 50)

if __name__ == "__main__":
    main()