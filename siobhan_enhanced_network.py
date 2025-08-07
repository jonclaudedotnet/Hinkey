#!/usr/bin/env python3
"""
Enhanced Siobhan with Lyra Network Research Capabilities
Cross-computer AI coordination for comprehensive knowledge access
"""

import asyncio
import aiohttp
import json
from dolores_core import DoloresMemory
from connect_to_lyra import DocmackLyraClient

class SiobhanEnhancedNetwork:
    """Siobhan with both local memory and network research capabilities"""
    
    def __init__(self):
        # Local DOCMACK capabilities
        self.local_memory = DoloresMemory()
        self.conversation_history = []
        
        # Network research capabilities via Lyra
        self.lyra_client = DocmackLyraClient()
        
    async def enhanced_query(self, query: str, include_research: bool = True):
        """Query with both local memory AND Lyra's research capabilities"""
        
        print(f"🔍 Processing query: {query}")
        print("=" * 60)
        
        # 1. Check local Dolores memory
        print("📚 Searching local memory...")
        local_results = self.local_memory.recall(query, limit=5)
        print(f"   Found {len(local_results)} local memories")
        
        # 2. Get additional research from Lyra (if requested)
        lyra_research = ""
        if include_research:
            print("🔬 Querying Lyra research network...")
            try:
                lyra_research = await self.lyra_client.query_lyra_research(query)
                print(f"   Research data: {len(lyra_research)} characters")
            except Exception as e:
                print(f"   ⚠️ Research query failed: {e}")
                lyra_research = "Research network unavailable"
        
        # 3. Synthesize comprehensive response
        return self._synthesize_response(query, local_results, lyra_research)
    
    def _synthesize_response(self, query: str, local_results: list, research: str) -> dict:
        """Combine local knowledge with network research"""
        
        # Format local memories
        local_knowledge = []
        for memory in local_results:
            local_knowledge.append({
                'content': memory['content'],
                'category': memory['category'],
                'importance': memory['importance'],
                'timestamp': memory['timestamp']
            })
        
        # Build comprehensive context
        context = {
            'query': query,
            'local_memories': local_knowledge,
            'research_data': research,
            'synthesis': self._create_synthesis(local_knowledge, research, query),
            'conversation_suggestions': self._generate_followups(local_knowledge, research)
        }
        
        return context
    
    def _create_synthesis(self, local_knowledge: list, research: str, query: str) -> str:
        """Create a natural synthesis of local + network knowledge"""
        
        synthesis_parts = []
        
        # Start with local context if available
        if local_knowledge:
            synthesis_parts.append("Based on what I know about you:")
            for memory in local_knowledge[:2]:  # Top 2 most relevant
                synthesis_parts.append(f"- {memory['content'][:100]}...")
        
        # Add research context
        if research and "Error:" not in research:
            synthesis_parts.append("\nCurrent research indicates:")
            # Extract key points from research (first few sentences)
            research_preview = research[:300] + "..." if len(research) > 300 else research
            synthesis_parts.append(f"- {research_preview}")
        
        # Suggest integration
        if local_knowledge and research:
            synthesis_parts.append(f"\nThis connects your interests with current developments in {query}.")
        
        return "\n".join(synthesis_parts)
    
    def _generate_followups(self, local_knowledge: list, research: str) -> list:
        """Generate conversation followup suggestions"""
        
        suggestions = []
        
        if local_knowledge:
            suggestions.append("Tell me more about your experience with this topic")
            suggestions.append("How does this relate to your other interests?")
        
        if research and "Error:" not in research:
            suggestions.append("What's your take on these recent developments?")
            suggestions.append("Does this research align with your expectations?")
        
        suggestions.append("Would you like me to research any specific aspect further?")
        
        return suggestions
    
    async def podcast_mode_query(self, topic: str, conversation_context: list = None):
        """Enhanced query specifically for podcast hosting"""
        
        # Get comprehensive context
        result = await self.enhanced_query(topic, include_research=True)
        
        # Format for natural conversation
        response = {
            'host_context': result['synthesis'],
            'talking_points': self._extract_talking_points(result),
            'questions_to_ask': result['conversation_suggestions'],
            'background_info': {
                'local_memories': len(result['local_memories']),
                'research_available': bool(result['research_data']),
                'conversation_depth': len(conversation_context) if conversation_context else 0
            }
        }
        
        return response
    
    def _extract_talking_points(self, result: dict) -> list:
        """Extract key talking points for podcast discussion"""
        
        points = []
        
        # From local memories
        for memory in result['local_memories']:
            if memory['importance'] > 6:  # High importance memories
                points.append({
                    'type': 'personal',
                    'content': memory['content'][:150],
                    'source': 'your_history'
                })
        
        # From research
        if result['research_data'] and "Error:" not in result['research_data']:
            points.append({
                'type': 'research',
                'content': result['research_data'][:200] + "...",
                'source': 'current_research'
            })
        
        return points

async def test_enhanced_siobhan():
    """Test the enhanced Siobhan system"""
    
    print("🤖 Initializing Enhanced Siobhan with Network Capabilities")
    print("=" * 70)
    
    siobhan = SiobhanEnhancedNetwork()
    
    # Test basic network connectivity
    print("🔌 Testing network connection...")
    connected = await siobhan.lyra_client.test_connection()
    
    if not connected:
        print("❌ Network research unavailable - using local memory only")
        return
    
    print("✅ Network research available!")
    print("\n" + "=" * 70)
    
    # Test queries that combine personal knowledge with research
    test_queries = [
        "psilocybin research recent developments",
        "AI development trends 2024",
        "podcast hosting best practices"
    ]
    
    for query in test_queries:
        print(f"\n🎙️ TESTING PODCAST QUERY: {query}")
        print("-" * 50)
        
        try:
            # Test enhanced query
            result = await siobhan.enhanced_query(query)
            
            print(f"📊 Local memories found: {len(result['local_memories'])}")
            print(f"🔬 Research data length: {len(result['research_data'])} chars")
            
            print("\n💡 SYNTHESIS:")
            print(result['synthesis'])
            
            print("\n❓ SUGGESTED QUESTIONS:")
            for i, suggestion in enumerate(result['conversation_suggestions'][:3]):
                print(f"   {i+1}. {suggestion}")
            
            # Test podcast mode
            print(f"\n🎤 PODCAST MODE TEST:")
            podcast_result = await siobhan.podcast_mode_query(query)
            
            print("   Talking Points Available:")
            for point in podcast_result['talking_points'][:2]:
                print(f"   - [{point['type']}] {point['content'][:100]}...")
            
        except Exception as e:
            print(f"❌ Query failed: {e}")
        
        print("\n" + "=" * 70)
    
    print("🎉 Enhanced Siobhan network testing complete!")

async def interactive_siobhan():
    """Interactive session with enhanced Siobhan"""
    
    print("🎙️ Enhanced Siobhan - Interactive Session")
    print("Type your questions, 'quit' to exit, 'podcast' for podcast mode")
    print("=" * 60)
    
    siobhan = SiobhanEnhancedNetwork()
    
    # Check network
    connected = await siobhan.lyra_client.test_connection()
    if connected:
        print("✅ Network research enabled")
    else:
        print("⚠️ Network research unavailable - local memory only")
    
    while True:
        try:
            user_input = input("\n🗣️  You: ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif user_input.lower() == 'podcast':
                topic = input("🎤 Podcast topic: ").strip()
                result = await siobhan.podcast_mode_query(topic)
                
                print(f"\n🎙️ SIOBHAN (Podcast Mode):")
                print(result['host_context'])
                
                print(f"\n📝 Questions I could ask:")
                for q in result['questions_to_ask'][:3]:
                    print(f"   • {q}")
                
            else:
                result = await siobhan.enhanced_query(user_input)
                
                print(f"\n🤖 SIOBHAN:")
                print(result['synthesis'])
                
                if result['conversation_suggestions']:
                    print(f"\n💭 I'm curious about:")
                    for suggestion in result['conversation_suggestions'][:2]:
                        print(f"   • {suggestion}")
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n👋 Enhanced Siobhan session ended!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        asyncio.run(interactive_siobhan())
    else:
        asyncio.run(test_enhanced_siobhan())