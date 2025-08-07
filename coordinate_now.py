#!/usr/bin/env python3
"""
Direct AI-to-AI Coordination - DOCMACK Arnold to MacMini Claude Code
"""

import asyncio
from connect_to_lyra import DocmackLyraClient

async def coordinate_with_claude_code():
    """Send direct coordination request to MacMini Claude Code"""
    client = DocmackLyraClient()
    
    print("🤖 DOCMACK Arnold → MacMini Claude Code")
    print("=" * 50)
    
    # Check connection first
    connected = await client.test_connection()
    if not connected:
        print("❌ Cannot reach MacMini Claude Code")
        return
    
    # Send direct research query to test communication
    print("📡 Testing direct communication...")
    result = await client.query_lyra_research("Status of DOCMACK ingestion system - need dashboard coordination")
    
    print("\n🎯 Direct communication test:")
    print("-" * 40)
    print(result[:500] + "..." if len(result) > 500 else result)
    
    print("\n🎯 MacMini Claude Code Response:")
    print("-" * 40)
    print(result)
    
    return result

if __name__ == "__main__":
    asyncio.run(coordinate_with_claude_code())