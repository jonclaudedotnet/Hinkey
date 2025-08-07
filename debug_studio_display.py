#!/usr/bin/env python3
"""
Debug why Studio UI shows tasks but not responses
"""

import sqlite3
from pathlib import Path

def check_database():
    """Check what's actually in the database"""
    db_path = Path("./claude_dolores_bridge/shared_tasks.db")
    
    if not db_path.exists():
        print("❌ Database not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get recent tasks
    cursor.execute("""
        SELECT id, task_type, status, 
               CASE WHEN result IS NULL THEN '[NULL]' 
                    WHEN result = '' THEN '[EMPTY]'
                    WHEN LENGTH(result) > 100 THEN SUBSTR(result, 1, 100) || '...'
                    ELSE result END as result_preview
        FROM tasks 
        WHERE id >= 10
        ORDER BY id DESC
    """)
    
    print("📊 RECENT TASKS IN DATABASE:")
    print("-" * 80)
    
    for row in cursor.fetchall():
        print(f"Task #{row[0]}: {row[1]} - Status: {row[2]}")
        print(f"   Result: {row[3]}")
        print("-" * 40)
    
    conn.close()

def check_studio_query():
    """Check what the Studio query returns"""
    db_path = Path("./claude_dolores_bridge/shared_tasks.db")
    
    if not db_path.exists():
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # This is what Studio is supposed to query
    session_start_id = 0  # Starting from beginning for debug
    
    cursor.execute('''
        SELECT id, timestamp, requester, task_type, content, context, status, result, tokens_used
        FROM tasks 
        WHERE id > ?
        ORDER BY id ASC
    ''', (session_start_id,))
    
    tasks = cursor.fetchall()
    
    print(f"\n📋 STUDIO QUERY RESULTS (after ID {session_start_id}):")
    print("-" * 80)
    
    for task in tasks:
        print(f"Task #{task[0]}: {task[3]} - Status: {task[6]}")
        if task[7]:  # result field
            print(f"   Has result: YES ({len(task[7])} chars)")
        else:
            print(f"   Has result: NO")
    
    conn.close()

if __name__ == "__main__":
    check_database()
    check_studio_query()