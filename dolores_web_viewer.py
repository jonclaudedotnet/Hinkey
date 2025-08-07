#!/usr/bin/env python3
"""
Dolores Web Viewer - Web interface showing DeepSeek responses
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
import threading

class DoloresWebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.serve_viewer()
        elif self.path == '/api/tasks':
            self.serve_tasks_json()
        else:
            self.send_error(404)
    
    def serve_viewer(self):
        html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dolores Viewer - DeepSeek Responses</title>
    <style>
        body { font-family: monospace; margin: 20px; background: #1a1a1a; color: #00ff00; }
        .task { border: 2px solid #00ff00; margin: 20px 0; padding: 15px; border-radius: 5px; }
        .header { background: #003300; padding: 10px; margin: -15px -15px 15px -15px; }
        .pending { border-color: #ffaa00; color: #ffaa00; }
        .completed { border-color: #00ff00; color: #00ff00; }
        .request { background: #002200; padding: 10px; margin: 10px 0; }
        .response { background: #001100; padding: 10px; margin: 10px 0; }
        .tokens { color: #00aaff; font-style: italic; }
        h1 { color: #00ff00; text-align: center; }
    </style>
    <script>
        function loadTasks() {
            fetch('/api/tasks')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('tasks');
                    container.innerHTML = '';
                    
                    data.forEach(task => {
                        const taskDiv = document.createElement('div');
                        taskDiv.className = `task ${task.status}`;
                        
                        taskDiv.innerHTML = `
                            <div class="header">
                                <strong>TASK #${task.id}</strong> - ${task.timestamp}
                                <br>Type: ${task.task_type} | Status: ${task.status}
                                ${task.tokens_used ? ` | Tokens: ${task.tokens_used}` : ''}
                            </div>
                            ${task.context ? `<div><strong>Context:</strong> ${task.context}</div>` : ''}
                            <div class="request"><strong>REQUEST:</strong><br>${task.content.replace(/\\n/g, '<br>')}</div>
                            ${task.result ? 
                                `<div class="response"><strong>DOLORES'S DEEPSEEK RESPONSE:</strong><br>${task.result.replace(/\\n/g, '<br>')}</div>` :
                                '<div class="response">⏳ Processing...</div>'
                            }
                        `;
                        
                        container.appendChild(taskDiv);
                    });
                })
                .catch(error => console.error('Error loading tasks:', error));
        }
        
        // Auto-refresh every 2 seconds
        setInterval(loadTasks, 2000);
        
        // Load on page start
        window.onload = loadTasks;
    </script>
</head>
<body>
    <h1>🔍 DOLORES VIEWER - DeepSeek Response Monitor</h1>
    <div id="tasks"></div>
</body>
</html>
        '''.strip()
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_tasks_json(self):
        try:
            bridge_dir = Path("./claude_dolores_bridge")
            task_db = bridge_dir / "shared_tasks.db"
            
            if not task_db.exists():
                tasks = []
            else:
                conn = sqlite3.connect(task_db)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, timestamp, requester, task_type, content, context, status, result, tokens_used
                    FROM tasks 
                    ORDER BY id DESC
                    LIMIT 20
                ''')
                
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
                
                conn.close()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(tasks).encode())
            
        except Exception as e:
            self.send_error(500, f"Error: {str(e)}")
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

def start_web_viewer(port=8080):
    """Start the web viewer server"""
    server = HTTPServer(('localhost', port), DoloresWebHandler)
    
    print(f"🌐 Dolores Web Viewer starting on http://localhost:{port}")
    print("Opening browser...")
    
    # Open browser in a separate thread
    def open_browser():
        import time
        time.sleep(1)  # Give server time to start
        webbrowser.open(f'http://localhost:{port}')
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Web viewer stopped")
        server.shutdown()

if __name__ == "__main__":
    start_web_viewer()