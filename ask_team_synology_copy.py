#!/usr/bin/env python3
"""
Ask AI Team for Synology Copy-and-Organize Approach
"""

import asyncio
import sys
sys.path.append('.')

# Ask DeepSeek
import json
import requests

def ask_deepseek():
    """Ask DeepSeek about the Synology copy approach"""
    try:
        # Load config
        config_file = "config.json"
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        api_key = config.get('deepseek_api_key')
        if not api_key:
            print("❌ No DeepSeek API key found")
            return
            
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        prompt = """Design a system that copies files from one Synology NAS to another while:

1. Organizing files into smart folder structures on destination
2. Determining scan eligibility based on file type, size, other requirements
3. Creating batches for later processing
4. Handling 149k+ files efficiently

Current situation:
- Source: SYNSRT share with 149k files
- Processing only 256 files/hour currently
- Need to copy ALL files but scan selectively
- Want organized structure on destination for easier batch processing

What's the best architecture for this copy-organize-index approach?"""

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000
        }
        
        response = requests.post(
            'https://api.deepseek.com/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            print("\n🧠 DEEPSEEK ARCHITECTURAL ADVICE:")
            print("=" * 50) 
            print(content)
        else:
            print(f"❌ DeepSeek API error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error asking DeepSeek: {e}")

async def ask_perplexity():
    """Ask Perplexity for best practices"""
    try:
        from connect_to_lyra import DocmackLyraClient
        
        client = DocmackLyraClient()
        connected = await client.test_connection()
        
        if connected:
            query = "Best practices for copying and organizing 150k files between Synology NAS devices while preparing for selective content indexing. Need efficient folder organization strategies."
            
            result = await client.query_lyra_research(query)
            
            print("\n🌐 PERPLEXITY BEST PRACTICES:")
            print("=" * 50)
            print(result[:1000] + "..." if len(result) > 1000 else result)
        else:
            print("❌ Cannot reach Perplexity network")
            
    except Exception as e:
        print(f"❌ Error asking Perplexity: {e}")

def ask_dolores_locally():
    """Ask Dolores about file organization strategies"""
    try:
        from dolores_core import DoloresMemory
        memory = DoloresMemory()
        
        # Add a memory about the new approach
        memory.add_memory(
            "Jon wants to copy all files from source Synology to destination Synology with smart organization before selective scanning",
            category="technical",
            importance=5
        )
        
        stats = memory.get_memory_stats()
        
        print("\n🤖 DOLORES MEMORY UPDATE:")
        print("=" * 50)
        print(f"Stored new approach in memory. Total memories: {stats.get('total_memories', 0)}")
        print("Dolores will remember this architectural decision for future reference.")
        
    except Exception as e:
        print(f"Note: Dolores memory update skipped: {e}")

def main():
    print("🚨 SYNOLOGY COPY-AND-ORGANIZE APPROACH - ASKING AI TEAM")
    print("=" * 60)
    
    # Ask all AI systems
    ask_deepseek()
    asyncio.run(ask_perplexity())
    ask_dolores_locally()
    
    print("\n📋 SUMMARY: Team consulted on Synology-to-Synology copy approach")

if __name__ == "__main__":
    main()