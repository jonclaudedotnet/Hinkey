#!/usr/bin/env python3
"""
Check the structure of Dolores's SQLite database
"""

import sqlite3
from pathlib import Path

def check_database_structure():
    db_path = "./dolores_knowledge/dolores_memory.db"
    
    if not Path(db_path).exists():
        print("Database doesn't exist yet")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print(f"Found {len(tables)} tables:")
    for table in tables:
        table_name = table[0]
        print(f"\n📋 Table: {table_name}")
        
        # Get table info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        print("  Columns:")
        for col in columns:
            print(f"    - {col[1]} ({col[2]})")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  Rows: {count}")
        
        # Show some sample data
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            samples = cursor.fetchall()
            print("  Sample data:")
            for i, sample in enumerate(samples):
                print(f"    {i+1}. {sample}")
    
    conn.close()

if __name__ == "__main__":
    check_database_structure()