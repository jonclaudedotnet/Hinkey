#!/usr/bin/env python3
"""
DOCMACK MCP Client - Connect to Lyra's Network
"""

import asyncio
import aiohttp
import json

class DocmackLyraClient:
    def __init__(self):
        self.lyra_host = "10.0.0.212"
        self.lyra_port = 8080
        self.base_url = f"http://{self.lyra_host}:{self.lyra_port}"
        
    async def test_connection(self):
        """Test connection to Lyra's MCP network"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        print("✅ Connected to Lyra's MCP network!")
                        return True
                    else:
                        print(f"⚠️ Connection issue: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def coordinate_dashboard_build(self, project_details: str):
        """Coordinate with Claude Code on dashboard building"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "tool": "coordinate_project",
                    "arguments": {
                        "message": f"Dashboard coordination from DOCMACK Arnold: {project_details}",
                        "project_type": "ingestion_dashboard",
                        "requesting_ai": "DOCMACK Arnold",
                        "docmack_ip": "10.0.0.200"
                    }
                }
                
                async with session.post(f"{self.base_url}/tools/call", 
                                      json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("result", "No coordination response")
                    else:
                        return f"Coordination failed: {response.status}"
        except Exception as e:
            return f"Connection error: {e}"

    async def query_lyra_research(self, query: str):
        """Query Lyra's research capabilities"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "tool": "perplexity_search",
                    "arguments": {"query": query}
                }
                
                async with session.post(f"{self.base_url}/tools/call", 
                                      json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("result", "No result")
                    else:
                        return f"Error: {response.status}"
        except Exception as e:
            return f"Connection error: {e}"
    
    async def deep_research_with_lyra(self, topic: str, depth: int = 2):
        """Use Lyra's deep research capabilities"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "tool": "perplexity_research", 
                    "arguments": {
                        "topic": topic,
                        "depth": depth
                    }
                }
                
                async with session.post(f"{self.base_url}/tools/call",
                                      json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("result", "No result")
                    else:
                        return f"Error: {response.status}"
        except Exception as e:
            return f"Connection error: {e}"

async def main():
    """Test DOCMACK connection to Lyra"""
    print("🔌 DOCMACK → Lyra MCP Connection Test")
    print("=" * 50)
    
    client = DocmackLyraClient()
    
    # Test basic connection
    connected = await client.test_connection()
    
    if connected:
        print("\n🧠 Testing Lyra's research capabilities...")
        
        # Test research query
        result = await client.query_lyra_research(
            "Current status of psilocybin research 2024"
        )
        
        print("Research Result Preview:")
        print(result[:200] + "..." if len(result) > 200 else result)
        
        print("\n🎉 DOCMACK ↔ Lyra MCP Network OPERATIONAL!")
        
    else:
        print("\n⚙️ Connection Setup Needed:")
        print("1. Start MCP server on MacMini (10.0.0.212)")
        print("2. Run: cd '/Users/jonclaude/PODCAST LIVE' && python3.12 perplexity_mcp_server.py --network")
        print("3. Verify firewall settings allow port 3000")

if __name__ == "__main__":
    asyncio.run(main())