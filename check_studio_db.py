#!/usr/bin/env python3
"""Check and debug Studio database issues"""

import sqlite3
from pathlib import Path

db_path = Path("./claude_dolores_bridge/shared_tasks.db")

if db_path.exists():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check all tasks
    cursor.execute("""
        SELECT id, task_type, status, 
               CASE WHEN result IS NULL THEN 'NULL' 
                    WHEN LENGTH(result) > 50 THEN SUBSTR(result, 1, 50) || '...'
                    ELSE result END as result_preview
        FROM tasks 
        ORDER BY id DESC 
        LIMIT 10
    """)
    
    print("Recent tasks in database:")
    print("-" * 80)
    for row in cursor.fetchall():
        print(f"ID: {row[0]}, Type: {row[1]}, Status: {row[2]}")
        print(f"Result: {row[3]}")
        print("-" * 80)
    
    conn.close()
else:
    print("Database not found!")

# Also check if daemon is processing
print("\nChecking for unprocessed tasks...")
from claude_dolores_bridge import ClaudeDoloresBridge
bridge = ClaudeDoloresBridge()
pending = bridge.get_pending_tasks_for_dolores()
print(f"Found {len(pending)} pending tasks")

if pending:
    print("\nPending tasks that need processing:")
    for task in pending:
        print(f"Task {task['id']}: {task['type']}")