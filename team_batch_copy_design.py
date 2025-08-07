#!/usr/bin/env python3
"""
Ask AI Team to Design Batch Copy System with Mounted Folder Selection
"""

import asyncio
import sys
sys.path.append('.')

# Ask DeepSeek for system design
import json
import requests

def ask_deepseek_batch_design():
    """Ask DeepSeek for batch copy system design"""
    try:
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
        
        prompt = """Design a Python system for batch copying files with these requirements:

1. **Mounted Folder Selection**: User can select from multiple mounted network drives (CIFS/SMB)
2. **Batch Processing**: Copy files in configurable batches (e.g., 1000 files per batch)
3. **Smart Organization**: Organize files by type into destination folders during copy
4. **Resume Capability**: Track progress, resume interrupted batches
5. **UI Selection**: Show available mounted drives, let user pick source/destination

System should handle:
- Multiple source drives mounted at different paths
- Batch size configuration
- Progress tracking per batch
- File type detection and routing
- Error handling and retry logic
- Database tracking of copied files

What's the best architecture for this batch copy system with mount selection?"""

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1200
        }
        
        response = requests.post(
            'https://api.deepseek.com/chat/completions',
            headers=headers,
            json=payload,
            timeout=45
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            print("🧠 DEEPSEEK BATCH COPY SYSTEM DESIGN:")
            print("=" * 60) 
            print(content)
        else:
            print(f"❌ DeepSeek API error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error asking DeepSeek: {e}")

async def ask_perplexity_batch_practices():
    """Ask Perplexity for batch copy best practices"""
    try:
        from connect_to_lyra import DocmackLyraClient
        
        client = DocmackLyraClient()
        connected = await client.test_connection()
        
        if connected:
            query = "Python file copy system with batch processing, mounted drive selection, and resume capability. Best practices for handling large file operations with user interface for drive selection."
            
            result = await client.query_lyra_research(query)
            
            print("\n🌐 PERPLEXITY BATCH COPY BEST PRACTICES:")
            print("=" * 60)
            print(result[:1200] + "..." if len(result) > 1200 else result)
        else:
            print("❌ Cannot reach Perplexity network")
            
    except Exception as e:
        print(f"❌ Error asking Perplexity: {e}")

def check_current_mounts():
    """Check what drives are currently mounted"""
    import subprocess
    import os
    
    print("\n📁 CURRENT MOUNTED DRIVES:")
    print("=" * 40)
    
    try:
        # Check mount points
        result = subprocess.run(['mount'], capture_output=True, text=True)
        
        # Filter for network mounts
        network_mounts = []
        for line in result.stdout.split('\n'):
            if 'cifs' in line or 'nfs' in line or '10.0.0.' in line:
                parts = line.split()
                if len(parts) >= 3:
                    source = parts[0]
                    mount_point = parts[2]
                    fs_type = parts[4] if len(parts) > 4 else 'unknown'
                    
                    # Check if accessible
                    try:
                        files = len(os.listdir(mount_point))
                        network_mounts.append({
                            'source': source,
                            'mount_point': mount_point,
                            'type': fs_type,
                            'accessible': True,
                            'file_count': files
                        })
                    except:
                        network_mounts.append({
                            'source': source,
                            'mount_point': mount_point,
                            'type': fs_type,
                            'accessible': False,
                            'file_count': 0
                        })
        
        for mount in network_mounts:
            status = "✅" if mount['accessible'] else "❌"
            print(f"{status} {mount['source']}")
            print(f"   → {mount['mount_point']} ({mount['type']})")
            if mount['accessible']:
                print(f"   → {mount['file_count']} items")
            print()
            
        return network_mounts
        
    except Exception as e:
        print(f"Error checking mounts: {e}")
        return []

def main():
    print("🚨 BATCH COPY SYSTEM DESIGN - CONSULTING AI TEAM")
    print("=" * 70)
    
    # Check current environment
    mounts = check_current_mounts()
    
    # Ask AI team for design
    ask_deepseek_batch_design()
    asyncio.run(ask_perplexity_batch_practices())
    
    print(f"\n📋 SUMMARY: Team consulted for batch copy system with {len(mounts)} mounted drives available")

if __name__ == "__main__":
    main()