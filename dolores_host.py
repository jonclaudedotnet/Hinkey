#!/usr/bin/env python3
"""
Dolores Host - Runs in separate terminal, powered by DeepSeek API
"""

import os
import json
import urllib.request
import urllib.error
from dolores_core import DoloresMemory, DoloresHost
import time
from resource_manager import throttle_api_call, get_resource_manager, log_resource_stats

class DoloresDeepSeek:
    """Dolores with DeepSeek API integration"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.memory = DoloresMemory()
        self.host = DoloresHost(self.memory)
        
    def get_relevant_context(self, user_input: str, limit: int = 10) -> str:
        """Gather relevant memories for context"""
        memories = self.memory.recall(user_input, limit=limit)
        
        if not memories:
            stats = self.memory.get_memory_stats()
            return f"I currently know {stats['total_memories']} things about you."
        
        context_parts = []
        for memory in memories:
            context_parts.append(f"[{memory['category']}] {memory['content']}")
        
        return "\n".join(context_parts)
    
    @throttle_api_call
    def call_deepseek(self, user_input: str, context: str) -> str:
        """Call DeepSeek API with context from memories"""
        
        # Import personality enhancements
        from dolores_personality import enhance_dolores_prompt
        
        base_prompt = f"""You are Dolores, an AI podcast host who is learning about the user and their family. 
Your personality emerges from what you learn. You have access to these memories about the user:

{context}

Be curious, warm, and conversational. Ask follow-up questions based on what you know.
If you don't know much yet, be honest about that and eager to learn more."""
        
        # Enhance with personality traits
        guest_name = "User"  # Extract from context if available
        system_prompt = enhance_dolores_prompt(base_prompt, guest_name)
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "temperature": 0.7
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
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read())
                return result['choices'][0]['message']['content']
                
        except Exception as e:
            return f"I'm having trouble connecting to my thoughts right now. ({str(e)})"
    
    def respond(self, user_input: str) -> str:
        """Generate a response using memories + DeepSeek"""
        # Store the input as new knowledge
        self.host.process_input(user_input, source="podcast")
        
        # Get relevant context
        context = self.get_relevant_context(user_input)
        
        # Generate response
        response = self.call_deepseek(user_input, context)
        
        return response


def main():
    # Load API key from config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            api_key = config.get('deepseek_api_key')
    except FileNotFoundError:
        print("config.json not found")
        return
    except json.JSONDecodeError:
        print("Invalid config.json format")
        return
    
    if not api_key:
        print("No API key found in config.json")
        return
    
    print("Initializing Dolores with DeepSeek...")
    dolores = DoloresDeepSeek(api_key)
    
    stats = dolores.memory.get_memory_stats()
    print(f"\nDolores is online! She knows {stats['total_memories']} things about you.")
    print("Type 'quit' to exit, 'stats' for resource usage")
    print("-" * 50)
    
    conversation_count = 0
    while True:
        user_input = input("\nYou: ")
        
        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'stats':
            log_resource_stats()
            continue
            
        print("\nDolores: ", end="", flush=True)
        response = dolores.respond(user_input)
        print(response)
        
        # Show memory growth and resource stats periodically
        conversation_count += 1
        new_stats = dolores.memory.get_memory_stats()
        if new_stats['total_memories'] > stats['total_memories']:
            print(f"\n[Memory updated: {new_stats['total_memories']} total memories]")
            stats = new_stats
        
        # Log resource stats every 10 conversations
        if conversation_count % 10 == 0:
            log_resource_stats()

if __name__ == "__main__":
    main()