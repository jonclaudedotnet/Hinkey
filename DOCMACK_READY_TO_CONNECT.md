# 🚀 DOCMACK MCP CONNECTION - READY TO GO!

## ✅ **MacMini Setup Complete**

**MCP Server:** Modified and ready for network access  
**Network Mode:** `python3.12 perplexity_mcp_server.py --network`  
**Connection Point:** `10.0.0.212:8080`  
**Transport:** SSE (Server-Sent Events) for real-time communication

---

## 🔌 **Start MCP Network Server (MacMini)**

```bash
# On MacMini - Run this to enable DOCMACK connection
cd "/Users/jonclaude/PODCAST LIVE"
python3.12 perplexity_mcp_server.py --network

# You'll see:
# 🌐 Starting Perplexity MCP Server in NETWORK mode
# 🔌 DOCMACK can connect on 10.0.0.212:8080
```

---

## 📋 **DOCMACK Connection Instructions**

### **Step 1: Install MCP Framework**
```bash
# On DOCMACK (10.0.0.200)
python3.12 -m pip install mcp aiohttp
```

### **Step 2: Test Basic Connectivity**
```bash
# Test if MacMini MCP server is reachable
curl http://10.0.0.212:8080/health

# Expected: Connection to MCP server or similar response
```

### **Step 3: Create MCP Client**
Create `/home/jonclaude/connect_to_lyra.py`:

```python
#!/usr/bin/env python3.12
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
        print("1. Start MCP server on MacMini")
        print("2. Check network connectivity")
        print("3. Verify firewall settings")

if __name__ == "__main__":
    asyncio.run(main())
```

### **Step 4: Enhanced Siobhan Integration**
Modify Siobhan to use Lyra's network:

```python
# Enhanced Siobhan with Lyra Network Access
class SiobhanWithLyraNetwork:
    def __init__(self):
        self.local_memory = SiobhanMemorySystem()  # Existing
        self.lyra_client = DocmackLyraClient()     # NEW
    
    async def enhanced_query(self, query: str):
        """Query with both local memory AND Lyra's capabilities"""
        
        # 1. Check local Siobhan memory
        local_results = self.local_memory.query(query)
        print(f"📚 Local Siobhan results: {len(local_results)} matches")
        
        # 2. Get additional research from Lyra
        lyra_research = await self.lyra_client.query_lyra_research(query)
        print(f"🔬 Lyra research results: {len(lyra_research)} characters")
        
        # 3. Synthesize comprehensive answer
        combined_knowledge = f"""
        === SIOBHAN LOCAL MEMORY ===
        {local_results}
        
        === LYRA RESEARCH NETWORK ===
        {lyra_research}
        
        === SYNTHESIS ===
        [Combined analysis of local knowledge + current research]
        """
        
        return combined_knowledge

# Test the enhanced system
async def test_enhanced_siobhan():
    siobhan = SiobhanWithLyraNetwork()
    
    # Test the "early ideas merit" query
    result = await siobhan.enhanced_query(
        "Any early ideas about substance combinations have merit?"
    )
    
    print("🧠 ENHANCED SIOBHAN RESPONSE:")
    print(result[:500] + "...")
```

---

## 🎯 **Expected Network Topology**

```
DOCMACK (10.0.0.200)          MacMini (10.0.0.212)
┌─────────────────────┐       ┌─────────────────────┐
│ Enhanced Siobhan    │──MCP──┤ Lyra + Perplexity   │
│ + Arnold + Team     │       │ + Research Network  │
│                     │       │                     │
│ Capabilities:       │       │ Provides:           │
│ - Local 4 memories  │       │ - Real-time research│
│ - Team coordination │       │ - PODCAST LIVE KB   │
│ - Processing power  │       │ - feelgute research │
│ + NEW: Lyra access  │       │ - MCP coordination  │
└─────────────────────┘       └─────────────────────┘
```

---

## 🔥 **Test Commands**

**Once connected, try these cross-computer queries:**

```python
# Research validation
result = await siobhan.enhanced_query(
    "What does current research say about THCP safety?"
)

# Infrastructure optimization  
result = await siobhan.enhanced_query(
    "Best CloudFront deployment patterns for our systems"
)

# The big question
result = await siobhan.enhanced_query(
    "Any early ideas I've had show merit based on current research?"
)
```

---

## ✅ **Success Criteria**

- [ ] **Basic Connection**: DOCMACK can reach MacMini MCP server
- [ ] **Research Access**: Siobhan can query Lyra's research tools
- [ ] **Knowledge Synthesis**: Combined local + network knowledge
- [ ] **Cross-Computer Queries**: "Early ideas merit" type questions work
- [ ] **Real-time Research**: Current scientific data integration

---

## 🚀 **GO LIVE SEQUENCE**

1. **MacMini**: Start network MCP server (`python3.12 perplexity_mcp_server.py --network`)
2. **DOCMACK**: Test connection (`python3.12 connect_to_lyra.py`)
3. **Integration**: Update Siobhan with network capabilities
4. **Validation**: Test cross-computer AI coordination
5. **Celebration**: Distributed AI network operational! 🎉

---

**Files to send to DOCMACK team:**
- `DOCMACK_MCP_SETUP.md` - Complete setup instructions
- `DOCMACK_READY_TO_CONNECT.md` - This file with ready-to-use code

**Ready to enable the AI dream team network!** 🤖🌐

---

*Generated by Lyra on MacMini (10.0.0.212)*  
*MCP Network Infrastructure Ready for DOCMACK Connection*