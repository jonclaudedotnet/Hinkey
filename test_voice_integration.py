#!/usr/bin/env python3
"""
Test Voice Integration - Simple test to verify voice command database integration
"""

import sqlite3
import os
from datetime import datetime

def add_voice_command(text):
    """Add a voice command to the database"""
    db_path = os.path.join(os.path.dirname(__file__), 'claude_dolores_bridge', 'shared_tasks.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Insert voice command task
        cursor.execute("""
            INSERT INTO tasks (timestamp, requester, task_type, content, context, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            'test_system',
            'voice_command',
            text,
            'Test voice command integration',
            'pending'
        ))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ Added voice command (task #{task_id}): {text}")
        return task_id
        
    except Exception as e:
        print(f"❌ Failed to add voice command: {e}")
        return None

def main():
    print("🎙️ Voice Integration Test")
    print("=" * 30)
    print("This will add test voice commands to the database")
    print("Make sure siobhan_voice_system.py --daemon is running in another terminal")
    print()
    
    test_messages = [
        "Hello everyone, this is Siobhan joining the test.",
        "The voice integration system is working correctly.",
        "I can now speak through the database command system."
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"Test {i}/3: Adding voice command...")
        task_id = add_voice_command(message)
        
        if task_id:
            print(f"✅ Command added to database. Voice system should speak it now.")
        else:
            print("❌ Failed to add command")
            
        input("Press Enter for next test...")
    
    print("\n🎯 Integration test complete!")
    print("If you heard Siobhan speak all 3 messages, the integration is working!")

if __name__ == "__main__":
    main()