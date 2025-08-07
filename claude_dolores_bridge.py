#!/usr/bin/env python3
"""
Claude-Dolores Bridge - Direct communication channel between Claude Code and Dolores
"""

import json
import sqlite3
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

class ClaudeDoloresBridge:
    """Direct communication bridge between Claude and Dolores"""
    
    def __init__(self):
        self.bridge_dir = Path("./claude_dolores_bridge")
        self.bridge_dir.mkdir(exist_ok=True)
        
        # Message queue files
        self.claude_to_dolores = self.bridge_dir / "claude_to_dolores.jsonl"
        self.dolores_to_claude = self.bridge_dir / "dolores_to_claude.jsonl"
        
        # Shared task database
        self.task_db = self.bridge_dir / "shared_tasks.db"
        self._init_task_db()
        
    def _init_task_db(self):
        """Initialize shared task database"""
        conn = sqlite3.connect(self.task_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                requester TEXT NOT NULL,
                task_type TEXT NOT NULL,
                content TEXT NOT NULL,
                context TEXT,
                status TEXT DEFAULT 'pending',
                result TEXT,
                tokens_used INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def claude_requests_help(self, task_type: str, content: str, 
                           context: Optional[str] = None) -> int:
        """Claude requests Dolores's help with a task"""
        conn = sqlite3.connect(self.task_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tasks (requester, task_type, content, context)
            VALUES (?, ?, ?, ?)
        ''', ('claude', task_type, content, context))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Also append to message queue for real-time processing
        message = {
            'task_id': task_id,
            'timestamp': datetime.now().isoformat(),
            'type': task_type,
            'content': content,
            'context': context
        }
        
        with open(self.claude_to_dolores, 'a') as f:
            f.write(json.dumps(message) + '\n')
        
        return task_id
    
    def dolores_completes_task(self, task_id: int, result: str, tokens_used: int = 0):
        """Dolores marks a task as complete"""
        conn = sqlite3.connect(self.task_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE tasks 
            SET status = 'completed', result = ?, tokens_used = ?
            WHERE id = ?
        ''', (result, tokens_used, task_id))
        
        conn.commit()
        conn.close()
        
        # Notify Claude
        message = {
            'task_id': task_id,
            'timestamp': datetime.now().isoformat(),
            'status': 'completed',
            'result': result,
            'tokens_used': tokens_used
        }
        
        with open(self.dolores_to_claude, 'a') as f:
            f.write(json.dumps(message) + '\n')
    
    def claude_check_result(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Claude checks if a task is complete"""
        conn = sqlite3.connect(self.task_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT status, result, tokens_used 
            FROM tasks WHERE id = ?
        ''', (task_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0] == 'completed':
            return {
                'status': 'completed',
                'result': row[1],
                'tokens_used': row[2]
            }
        elif row:
            return {'status': row[0]}
        else:
            return None
    
    def get_pending_tasks_for_dolores(self) -> list:
        """Get all pending tasks for Dolores to process"""
        conn = sqlite3.connect(self.task_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, task_type, content, context 
            FROM tasks 
            WHERE requester = 'claude' AND status = 'pending'
            ORDER BY timestamp ASC
        ''')
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                'id': row[0],
                'type': row[1],
                'content': row[2],
                'context': row[3]
            })
        
        conn.close()
        return tasks


# Helper functions for Claude Code
def ask_dolores(task_type: str, content: str, context: Optional[str] = None) -> int:
    """Quick function for Claude to ask Dolores for help"""
    bridge = ClaudeDoloresBridge()
    task_id = bridge.claude_requests_help(task_type, content, context)
    print(f"Requested Dolores's help with task #{task_id}")
    return task_id

def check_dolores_result(task_id: int) -> Optional[Dict[str, Any]]:
    """Check if Dolores completed a task"""
    bridge = ClaudeDoloresBridge()
    return bridge.claude_check_result(task_id)

def wait_for_dolores(task_id: int, timeout: int = 30) -> Optional[str]:
    """Wait for Dolores to complete a task"""
    bridge = ClaudeDoloresBridge()
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        result = bridge.claude_check_result(task_id)
        if result and result['status'] == 'completed':
            return result['result']
        time.sleep(1)
    
    return None