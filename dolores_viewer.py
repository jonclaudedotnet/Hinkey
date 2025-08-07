#!/usr/bin/env python3
"""
Dolores Viewer - Shows full DeepSeek responses in real-time
"""

import json
import time
import sqlite3
from datetime import datetime
from pathlib import Path

class DoloresViewer:
    """Real-time viewer for Dolores's DeepSeek responses"""
    
    def __init__(self):
        self.bridge_dir = Path("./claude_dolores_bridge")
        self.task_db = self.bridge_dir / "shared_tasks.db"
        self.last_seen_task = 0
        
    def get_latest_tasks(self):
        """Get all tasks since last check"""
        if not self.task_db.exists():
            return []
            
        conn = sqlite3.connect(self.task_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, timestamp, requester, task_type, content, context, status, result, tokens_used
            FROM tasks 
            WHERE id > ?
            ORDER BY id ASC
        ''', (self.last_seen_task,))
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                'id': row[0],
                'timestamp': row[1],
                'requester': row[2],
                'task_type': row[3],
                'content': row[4],
                'context': row[5],
                'status': row[6],
                'result': row[7],
                'tokens_used': row[8]
            })
            
        if tasks:
            self.last_seen_task = tasks[-1]['id']
            
        conn.close()
        return tasks
    
    def format_task_display(self, task):
        """Format a task for display"""
        lines = []
        lines.append("=" * 80)
        lines.append(f"TASK #{task['id']} - {task['timestamp']}")
        lines.append(f"Type: {task['task_type']} | Requester: {task['requester']} | Status: {task['status']}")
        lines.append("-" * 80)
        
        if task['context']:
            lines.append(f"Context: {task['context']}")
            lines.append("")
        
        lines.append("REQUEST:")
        lines.append(task['content'])
        lines.append("")
        
        if task['result']:
            lines.append("DOLORES'S DEEPSEEK RESPONSE:")
            lines.append(task['result'])
            lines.append("")
            
            if task['tokens_used']:
                lines.append(f"Tokens Used: {task['tokens_used']}")
        else:
            lines.append("Status: Pending...")
            
        lines.append("=" * 80)
        lines.append("")
        
        return "\n".join(lines)
    
    def run_viewer(self):
        """Run the viewer in real-time"""
        print("🔍 DOLORES VIEWER - Real-time DeepSeek Response Monitor")
        print("Press Ctrl+C to exit")
        print("=" * 80)
        print("Waiting for Dolores activity...")
        print("")
        
        try:
            while True:
                tasks = self.get_latest_tasks()
                
                for task in tasks:
                    display = self.format_task_display(task)
                    print(display)
                    
                    # If task is completed, show a summary
                    if task['status'] == 'completed':
                        print(f"✅ Task #{task['id']} completed using {task['tokens_used']} DeepSeek tokens")
                        print("")
                
                time.sleep(1)  # Check every second
                
        except KeyboardInterrupt:
            print("\n👋 Dolores Viewer stopped")


def main():
    viewer = DoloresViewer()
    viewer.run_viewer()

if __name__ == "__main__":
    main()