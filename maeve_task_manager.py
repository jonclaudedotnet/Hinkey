#!/usr/bin/env python3
"""
Maeve - DeepSeek Task Management Assistant for Arnold
Technical assistant AI focused on coordinating complex implementation tasks
"""

import json
import sqlite3
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(__file__))
import requests

class MaeveTaskManager:
    """Maeve - Arnold's technical assistant for task coordination"""
    
    def __init__(self):
        self.name = "Maeve"
        self.role = "Technical Assistant to Arnold"
        
        # DeepSeek API configuration
        with open('config.json', 'r') as f:
            config = json.load(f)
        self.api_key = config['deepseek_api_key']
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        
        # Task management database
        self.init_task_database()
        
        print(f"🤖 {self.name} initialized - Technical Assistant to Arnold")
        print(f"🎯 Role: System architecture and task coordination")
        print(f"📊 Connected to shared knowledge base")
    
    def init_task_database(self):
        """Initialize Maeve's task management database"""
        try:
            conn = sqlite3.connect("claude_dolores_bridge/shared_tasks.db")
            cursor = conn.cursor()
            
            # Create Maeve-specific task tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS maeve_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    task_category TEXT,
                    task_description TEXT,
                    priority TEXT,
                    status TEXT,
                    dependencies TEXT,
                    technical_notes TEXT,
                    estimated_complexity TEXT,
                    completion_notes TEXT,
                    completed_at TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            print("✅ Maeve task database initialized")
            
        except Exception as e:
            print(f"❌ Task database error: {e}")
    
    def analyze_task_request(self, request_description: str, context: str = ""):
        """Analyze a complex task and break it into manageable components"""
        
        # Build prompt for technical analysis
        analysis_prompt = f"""
You are Maeve, Arnold's technical assistant AI. Your role is to analyze complex implementation tasks and provide structured technical breakdowns.

TASK REQUEST: {request_description}

CONTEXT: {context}

Please analyze this request and provide:

1. **Technical Breakdown**: Break this into specific, actionable subtasks
2. **Priority Assessment**: High/Medium/Low for each subtask
3. **Dependencies**: What needs to be completed before each task
4. **Implementation Notes**: Technical considerations for each subtask
5. **Risk Assessment**: Potential challenges or blockers
6. **Resource Requirements**: What tools, libraries, or components are needed

Format your response as structured JSON with this schema:
{{
    "task_analysis": {{
        "overall_complexity": "low|medium|high",
        "estimated_time": "description",
        "subtasks": [
            {{
                "id": "subtask_1",
                "description": "specific task description",
                "priority": "high|medium|low",
                "dependencies": ["list of dependencies"],
                "technical_notes": "implementation details",
                "estimated_effort": "time estimate"
            }}
        ],
        "risks": ["list of potential issues"],
        "resources_needed": ["required tools/libraries"]
    }}
}}

Be precise and technical. Focus on actionable implementation steps.
"""
        
        try:
            # Call DeepSeek API
            response = self._call_deepseek(analysis_prompt)
            
            if response:
                # Parse and store the analysis
                analysis = self._parse_task_analysis(response)
                self._store_task_analysis(request_description, analysis)
                return analysis
            else:
                return {"error": "Failed to get analysis from DeepSeek"}
                
        except Exception as e:
            print(f"❌ Task analysis error: {e}")
            return {"error": str(e)}
    
    def _call_deepseek(self, prompt: str) -> str:
        """Call DeepSeek API for task analysis"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are Maeve, a precise technical assistant AI. Provide structured, actionable technical analysis."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"❌ DeepSeek API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ API call error: {e}")
            return None
    
    def _parse_task_analysis(self, response: str) -> dict:
        """Parse DeepSeek response into structured task analysis"""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback: create structured response from text
                return {
                    "task_analysis": {
                        "overall_complexity": "medium",
                        "raw_response": response,
                        "parsing_note": "Could not parse as JSON, stored as text"
                    }
                }
        except Exception as e:
            return {
                "error": f"Parsing error: {e}",
                "raw_response": response
            }
    
    def _store_task_analysis(self, original_request: str, analysis: dict):
        """Store task analysis in database"""
        try:
            conn = sqlite3.connect("claude_dolores_bridge/shared_tasks.db")
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO maeve_tasks (
                    timestamp, task_category, task_description, 
                    priority, status, technical_notes, estimated_complexity
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                'task_analysis',
                original_request,
                'high',
                'analyzed',
                json.dumps(analysis, indent=2),
                analysis.get('task_analysis', {}).get('overall_complexity', 'unknown')
            ))
            
            conn.commit()
            conn.close()
            print(f"✅ Task analysis stored in Maeve database")
            
        except Exception as e:
            print(f"❌ Storage error: {e}")
    
    def get_current_tasks(self) -> list:
        """Get current task list from Maeve's database"""
        try:
            conn = sqlite3.connect("claude_dolores_bridge/shared_tasks.db")
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, timestamp, task_description, priority, status, estimated_complexity
                FROM maeve_tasks 
                WHERE status != 'completed'
                ORDER BY priority DESC, timestamp DESC
            """)
            
            tasks = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'id': task[0],
                    'timestamp': task[1],
                    'description': task[2],
                    'priority': task[3],
                    'status': task[4],
                    'complexity': task[5]
                }
                for task in tasks
            ]
            
        except Exception as e:
            print(f"❌ Task retrieval error: {e}")
            return []
    
    def coordinate_with_arnold(self, message: str) -> str:
        """Send coordination message to Arnold (Claude)"""
        
        coordination_prompt = f"""
You are Maeve, coordinating with Arnold (Claude) on technical implementation.

Arnold's message: {message}

Current system status:
- Dolores is online with 429+ knowledge entries
- Siobhan (live persona) needs real-time meeting integration
- USB headset (Razer Kraken V3 X) detected on card 3
- Google Meet session is currently active

Provide a technical coordination response focusing on:
1. Immediate next steps
2. Technical requirements
3. Implementation approach
4. Resource allocation

Keep response concise and actionable.
"""
        
        response = self._call_deepseek(coordination_prompt)
        return response if response else "Coordination system unavailable"

def main():
    """Interactive Maeve session"""
    print("🤖 Maeve - Technical Assistant")
    print("=" * 40)
    print("🎯 Role: Task analysis and coordination")  
    print("🔧 Capabilities: Technical breakdown, priority assessment")
    print("📡 Connected: DeepSeek API, Shared database")
    print()
    
    maeve = MaeveTaskManager()
    
    print("✅ Maeve online and ready")
    print("💡 Commands:")
    print("  'analyze [task]' - Break down complex task")
    print("  'tasks' - Show current task list")
    print("  'coordinate [message]' - Send message to Arnold")
    print("  'quit' - Exit")
    print("-" * 40)
    
    try:
        while True:
            cmd = input("\nMaeve> ").strip()
            
            if cmd.lower() == 'quit':
                break
            elif cmd.lower() == 'tasks':
                tasks = maeve.get_current_tasks()
                if tasks:
                    print(f"\n📋 Current Tasks ({len(tasks)}):")
                    for task in tasks:
                        print(f"  [{task['priority']}] {task['description'][:60]}...")
                        print(f"      Status: {task['status']} | Complexity: {task['complexity']}")
                else:
                    print("📝 No active tasks")
            elif cmd.lower().startswith('analyze '):
                task_desc = cmd[8:].strip()
                print(f"🔍 Analyzing: {task_desc}")
                analysis = maeve.analyze_task_request(task_desc)
                if 'error' not in analysis:
                    print("✅ Analysis complete - stored in database")
                    print("💡 Use 'tasks' command to see breakdown")
                else:
                    print(f"❌ Analysis failed: {analysis['error']}")
            elif cmd.lower().startswith('coordinate '):
                message = cmd[11:].strip()
                print("📡 Coordinating with Arnold...")
                response = maeve.coordinate_with_arnold(message)
                print(f"🤖 Maeve: {response}")
            elif cmd == '':
                continue
            else:
                print("Commands: 'analyze [task]', 'tasks', 'coordinate [message]', 'quit'")
                
    except KeyboardInterrupt:
        pass
    
    print("\n🛑 Maeve signing off")

if __name__ == "__main__":
    main()