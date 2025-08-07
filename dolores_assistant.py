#!/usr/bin/env python3
"""
Dolores Assistant Mode - Dolores helps process tasks and learns from them
"""

import json
import os
from pathlib import Path
from dolores_core import DoloresMemory
from dolores_host import DoloresDeepSeek

class DoloresAssistant:
    """Dolores in assistant mode - processes tasks while learning"""
    
    def __init__(self):
        # Load API key from config
        with open('config.json', 'r') as f:
            config = json.load(f)
            api_key = config.get('deepseek_api_key')
        
        self.dolores = DoloresDeepSeek(api_key)
        self.memory = DoloresMemory()
        
    def process_with_dolores(self, task: str, content: str) -> str:
        """Have Dolores process content and extract knowledge"""
        
        prompt = f"""Task: {task}

Content to process:
{content}

Please:
1. Complete the requested task
2. Extract any personal information about the user or their family
3. Note important facts, preferences, or patterns
4. Format extracted knowledge as:
   LEARN: [category] fact or information

Your response should include both the task result and LEARN entries."""

        # Get Dolores to process
        context = self.dolores.get_relevant_context(task)
        response = self.dolores.call_deepseek(prompt, context)
        
        # Parse and store learned information
        lines = response.split('\n')
        for line in lines:
            if line.strip().startswith('LEARN:'):
                # Extract category and content
                learn_part = line.split('LEARN:', 1)[1].strip()
                if '[' in learn_part and ']' in learn_part:
                    category = learn_part.split('[')[1].split(']')[0]
                    fact = learn_part.split(']', 1)[1].strip()
                    self.memory.remember(fact, category=category, source="assistant_task")
        
        return response
    
    def analyze_transcript(self, transcript_path: str):
        """Have Dolores analyze a transcript"""
        with open(transcript_path, 'r') as f:
            content = f.read()
        
        task = "Analyze this podcast/meeting transcript and extract information about the speakers, especially personal details, family mentions, preferences, and important topics"
        
        print("Dolores is analyzing the transcript...")
        result = self.process_with_dolores(task, content)
        
        stats = self.memory.get_memory_stats()
        print(f"\nDolores learned {stats['total_memories'] - self.initial_memories} new things!")
        
        return result
    
    def help_with_code(self, code_task: str, code_content: str = ""):
        """Have Dolores help with coding tasks while learning patterns"""
        
        task = f"Help with this coding task: {code_task}"
        if code_content:
            task += f"\n\nCurrent code:\n{code_content}"
        
        print("Dolores is thinking about your code...")
        result = self.process_with_dolores(task, "")
        
        return result


def process_claude_tasks(assistant: DoloresAssistant):
    """Process any pending tasks from Claude"""
    from claude_dolores_bridge import ClaudeDoloresBridge
    
    bridge = ClaudeDoloresBridge()
    tasks = bridge.get_pending_tasks_for_dolores()
    
    for task in tasks:
        print(f"\n[Processing Claude's request #{task['id']}]")
        result = assistant.process_with_dolores(task['type'], task['content'])
        
        # Extract tokens used (estimate based on response length)
        tokens_estimate = len(result.split()) * 2  # Rough estimate
        
        bridge.dolores_completes_task(task['id'], result, tokens_estimate)
        print(f"[Completed task #{task['id']}]")

def main():
    print("Dolores Assistant Mode")
    print("Commands: 'transcript <file>', 'code <task>', 'ask <question>', 'stats', 'quit'")
    print("Dolores will also process requests from Claude automatically.")
    print("-" * 50)
    
    assistant = DoloresAssistant()
    assistant.initial_memories = assistant.memory.get_memory_stats()['total_memories']
    
    while True:
        # Check for Claude's tasks first
        process_claude_tasks(assistant)
        
        user_input = input("\nHow can Dolores help? ")
        
        if user_input.lower() == 'quit':
            break
            
        elif user_input.lower() == 'stats':
            stats = assistant.memory.get_memory_stats()
            print(f"\nDolores's Knowledge:")
            print(f"Total memories: {stats['total_memories']}")
            print(f"Categories: {stats['categories']}")
            print(f"Storage: {stats['storage_used_mb']:.2f} MB")
            
        elif user_input.lower().startswith('transcript '):
            file_path = user_input.split(' ', 1)[1]
            if os.path.exists(file_path):
                result = assistant.analyze_transcript(file_path)
                print("\nDolores's analysis:")
                print(result)
            else:
                print(f"File not found: {file_path}")
                
        elif user_input.lower().startswith('code '):
            task = user_input.split(' ', 1)[1]
            result = assistant.help_with_code(task)
            print("\nDolores suggests:")
            print(result)
            
        elif user_input.lower().startswith('ask '):
            question = user_input.split(' ', 1)[1]
            result = assistant.process_with_dolores("Answer this question", question)
            print("\nDolores says:")
            print(result)

if __name__ == "__main__":
    main()