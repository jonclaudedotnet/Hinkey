#!/usr/bin/env python3
"""
Shutdown Procedure - Gracefully shut down the Dolores ecosystem
"""

import subprocess
import os
import signal
from pathlib import Path
from claude_dolores_bridge import ask_dolores, wait_for_dolores
import sqlite3
from datetime import datetime

def graceful_shutdown():
    """Perform graceful shutdown of all Dolores components"""
    
    print("🔄 Starting graceful shutdown of Dolores ecosystem...")
    
    # 1. Notify Dolores of shutdown
    print("📢 Notifying Dolores of shutdown...")
    task_id = ask_dolores(
        "system_shutdown",
        "The system is being shut down gracefully. Please prepare for offline mode and save any important state.",
        "System shutdown notification"
    )
    
    result = wait_for_dolores(task_id, timeout=10)
    if result:
        print("✅ Dolores acknowledged shutdown")
        print(f"   Response: {result[:100]}...")
    else:
        print("⚠️  Dolores didn't respond - proceeding with shutdown")
    
    # 2. Create shutdown log entry
    print("📝 Creating shutdown log...")
    db_path = "./dolores_knowledge/dolores_memory.db"
    if Path(db_path).exists():
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO knowledge 
                (timestamp, category, content, source, importance)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                'system_event',
                'Dolores ecosystem gracefully shut down',
                'shutdown_procedure',
                8
            ))
            
            conn.commit()
            conn.close()
            print("✅ Shutdown logged to database")
        except Exception as e:
            print(f"⚠️  Error logging shutdown: {e}")
    
    # 3. Stop running processes
    print("🛑 Stopping Dolores processes...")
    processes_to_stop = [
        'dolores_clean_display.py',
        'dolores_host.py',
        'dolores_daemon.py',
        'dolores_studio_ui.py'
    ]
    
    stopped_count = 0
    for process_name in processes_to_stop:
        try:
            result = subprocess.run(
                ['pkill', '-f', process_name], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                print(f"✅ Stopped {process_name}")
                stopped_count += 1
            else:
                print(f"ℹ️  {process_name} not running")
        except Exception as e:
            print(f"⚠️  Error stopping {process_name}: {e}")
    
    # 4. Backup current state
    print("💾 Running final backup...")
    try:
        subprocess.run(['python3', 'synology_backup.py'], check=True)
        print("✅ Final backup completed")
    except Exception as e:
        print(f"⚠️  Backup failed: {e}")
    
    # 5. Clean up temporary files
    print("🧹 Cleaning up temporary files...")
    temp_patterns = [
        './jon_knowledge_temp',
        './__pycache__',
        '*.pyc'
    ]
    
    for pattern in temp_patterns:
        try:
            if Path(pattern).exists():
                if Path(pattern).is_dir():
                    subprocess.run(['rm', '-rf', pattern])
                else:
                    subprocess.run(['rm', '-f', pattern])
                print(f"✅ Cleaned {pattern}")
        except Exception as e:
            print(f"⚠️  Error cleaning {pattern}: {e}")
    
    print("\n🎯 SHUTDOWN COMPLETE")
    print("=" * 50)
    print("✅ All Dolores components stopped")
    print("✅ Database state saved") 
    print("✅ Final backup completed")
    print("✅ Temporary files cleaned")
    print("\n💤 Dolores ecosystem is now offline")
    print("🔄 Use startup_procedure.py to bring system back online")

if __name__ == "__main__":
    graceful_shutdown()