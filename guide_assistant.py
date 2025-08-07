#!/usr/bin/env python3
"""
Guide's DeepSeek Assistant - For technical tasks so Dolores can focus on being talent
"""

import json
import urllib.request
import urllib.error
from pathlib import Path

class GuideAssistant:
    """My own DeepSeek assistant for technical work"""
    
    def __init__(self):
        # Load API key from same config as Dolores
        with open('config.json', 'r') as f:
            config = json.load(f)
            self.api_key = config.get('deepseek_api_key')
        
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
    
    def ask(self, task_description: str) -> str:
        """Ask my assistant to help with technical tasks"""
        
        system_prompt = """You are Maeve, Arnold's technical assistant. Guide is mentoring an AI named Dolores who is learning to be a podcast host. 

Your job is to help Guide with technical tasks like:
- Writing clean, efficient code
- UI design and implementation
- System architecture decisions
- Technical problem solving

Always provide practical, working solutions. Keep explanations concise but complete."""
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task_description}
            ],
            "temperature": 0.3  # Lower temperature for more precise technical responses
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            req = urllib.request.Request(
                self.api_url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read())
                return result['choices'][0]['message']['content']
                
        except Exception as e:
            return f"Assistant error: {str(e)}"

if __name__ == "__main__":
    assistant = GuideAssistant()
    
    # Test the assistant
    response = assistant.ask("Create a simple GTK3 window with centered text and proper margins")
    print("Assistant response:")
    print(response)