#!/usr/bin/env python3
import sqlite3
from pathlib import Path

db_path = Path("./claude_dolores_bridge/shared_tasks.db")

if db_path.exists():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get column names
    cursor.execute("PRAGMA table_info(tasks)")
    columns = cursor.fetchall()
    print("Database columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Get a sample task
    cursor.execute("SELECT * FROM tasks ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    
    if row:
        print(f"\nSample task structure:")
        for i, col in enumerate(columns):
            print(f"  {col[1]}: {row[i]}")
    
    conn.close()
else:
    print("Database not found!")