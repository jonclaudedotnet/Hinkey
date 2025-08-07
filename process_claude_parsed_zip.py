#!/usr/bin/env python3
"""
Phase Zero: Process pre-parsed Claude Code zip file
This expects a zip file with already-analyzed content about Jon
"""

import json
import zipfile
from pathlib import Path
from datetime import datetime
from claude_dolores_bridge import ask_dolores, wait_for_dolores
from dolores_memory_v2 import DoloresMemoryV2
import time

class ClaudeParsedProcessor:
    """Process Claude Code's pre-parsed analysis of Jon"""
    
    def __init__(self):
        self.memory = DoloresMemoryV2()
        self.processed_count = 0
        self.categories = {
            'personal': [],
            'professional': [],
            'projects': [],
            'skills': [],
            'interests': [],
            'family': [],
            'history': []
        }
    
    def process_claude_zip(self, zip_path: str):
        """Process a zip file of Claude-parsed content"""
        
        print(f"📦 Opening Claude-parsed knowledge: {zip_path}")
        
        if not Path(zip_path).exists():
            print(f"❌ File not found: {zip_path}")
            return
            
        initial_stats = self.memory.get_memory_stats()
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                # List contents
                files = z.namelist()
                print(f"📄 Found {len(files)} files in archive")
                
                # Look for manifest or index
                if 'manifest.json' in files:
                    manifest = json.loads(z.read('manifest.json'))
                    print(f"📋 Manifest found: {manifest.get('description', 'No description')}")
                
                # Process each file
                for filename in files:
                    if filename.endswith(('.json', '.txt', '.md')):
                        print(f"\n🔍 Processing: {filename}")
                        content = z.read(filename).decode('utf-8', errors='ignore')
                        
                        if filename.endswith('.json'):
                            self._process_json_content(filename, content)
                        else:
                            self._process_text_content(filename, content)
                        
                        self.processed_count += 1
                        
                        # Don't overwhelm the system
                        if self.processed_count % 5 == 0:
                            self._send_batch_to_dolores()
                
                # Send final batch
                self._send_batch_to_dolores()
                
        except Exception as e:
            print(f"❌ Error processing zip: {e}")
            return
        
        # Show results
        final_stats = self.memory.get_memory_stats()
        print("\n" + "="*60)
        print("✅ PHASE ZERO COMPLETE")
        print(f"📊 Files processed: {self.processed_count}")
        print(f"🧠 New memories: {final_stats['total_memories'] - initial_stats['total_memories']}")
        print(f"💾 Total storage: {final_stats['storage_used_mb']:.1f} MB")
        
        # Category breakdown
        print("\n📂 KNOWLEDGE CATEGORIES:")
        for cat, items in self.categories.items():
            if items:
                print(f"  {cat}: {len(items)} items")
    
    def _process_json_content(self, filename: str, content: str):
        """Process JSON files with structured data"""
        try:
            data = json.loads(content)
            
            # Handle different JSON structures
            if isinstance(data, dict):
                # Single knowledge entry
                if 'category' in data and 'content' in data:
                    self._store_knowledge(
                        content=data['content'],
                        category=data.get('category', 'general'),
                        metadata=data
                    )
                # Multiple entries
                elif 'entries' in data:
                    for entry in data['entries']:
                        self._store_knowledge(
                            content=entry.get('content', ''),
                            category=entry.get('category', 'general'),
                            metadata=entry
                        )
                # Key-value pairs about Jon
                else:
                    for key, value in data.items():
                        if isinstance(value, str) and len(value) > 10:
                            self._store_knowledge(
                                content=f"{key}: {value}",
                                category=self._guess_category(key, value),
                                metadata={'source': filename, 'key': key}
                            )
            
            elif isinstance(data, list):
                # List of knowledge items
                for item in data:
                    if isinstance(item, dict):
                        self._store_knowledge(
                            content=item.get('content', str(item)),
                            category=item.get('category', 'general'),
                            metadata=item
                        )
                        
        except json.JSONDecodeError:
            print(f"  ⚠️  Invalid JSON in {filename}")
    
    def _process_text_content(self, filename: str, content: str):
        """Process text/markdown files"""
        
        # Split into meaningful chunks
        if filename.endswith('.md'):
            # Process markdown sections
            sections = content.split('\n## ')
            for section in sections:
                if section.strip():
                    lines = section.strip().split('\n')
                    title = lines[0].replace('#', '').strip()
                    body = '\n'.join(lines[1:])
                    
                    if body:
                        self._store_knowledge(
                            content=body,
                            category=self._guess_category(title, body),
                            metadata={'source': filename, 'section': title}
                        )
        else:
            # Process plain text in paragraphs
            paragraphs = content.split('\n\n')
            for para in paragraphs:
                if para.strip() and len(para) > 50:
                    self._store_knowledge(
                        content=para,
                        category='general',
                        metadata={'source': filename}
                    )
    
    def _store_knowledge(self, content: str, category: str, metadata: dict = None):
        """Store knowledge in memory and categorize"""
        
        # Store in Dolores's memory
        self.memory.remember(
            content=content,
            category=category,
            context=f"Claude-parsed: {metadata.get('source', 'unknown')}",
            source='claude_import',
            importance=8  # High importance for pre-parsed content
        )
        
        # Categorize for batch processing
        if category in self.categories:
            self.categories[category].append({
                'content': content,
                'metadata': metadata
            })
    
    def _guess_category(self, key: str, value: str) -> str:
        """Guess category based on content"""
        
        key_lower = key.lower()
        value_lower = value.lower()
        
        if any(word in key_lower for word in ['family', 'wife', 'parent', 'child']):
            return 'family'
        elif any(word in key_lower for word in ['work', 'job', 'career', 'professional']):
            return 'professional'
        elif any(word in key_lower for word in ['project', 'build', 'create', 'develop']):
            return 'projects'
        elif any(word in key_lower for word in ['skill', 'language', 'technology', 'expert']):
            return 'skills'
        elif any(word in key_lower for word in ['hobby', 'interest', 'enjoy', 'love']):
            return 'interests'
        elif any(word in key_lower for word in ['history', 'past', 'grew', 'born']):
            return 'history'
        elif any(word in value_lower for word in ['personal', 'private', 'individual']):
            return 'personal'
        
        return 'general'
    
    def _send_batch_to_dolores(self):
        """Send accumulated knowledge to Dolores for deeper understanding"""
        
        # Prepare summary for Dolores
        summary_parts = ["Phase Zero Knowledge Import - Claude's Pre-Parsed Analysis of Jon:\n"]
        
        for category, items in self.categories.items():
            if items:
                summary_parts.append(f"\n{category.upper()} ({len(items)} items):")
                # Sample a few items
                for item in items[:3]:
                    summary_parts.append(f"- {item['content'][:100]}...")
        
        summary = '\n'.join(summary_parts)
        
        # Ask Dolores to internalize
        task_id = ask_dolores(
            "knowledge_integration",
            f"{summary}\n\nPlease internalize this knowledge about Jon. Focus on connections and patterns.",
            "Phase Zero batch processing"
        )
        
        # Wait briefly for acknowledgment
        result = wait_for_dolores(task_id, timeout=15)
        if result:
            print(f"  ✅ Dolores integrated batch of {sum(len(items) for items in self.categories.values())} items")
        
        # Clear categories for next batch
        for cat in self.categories:
            self.categories[cat] = []


def main():
    """Process Claude-parsed zip file"""
    
    print("🚀 PHASE ZERO - Claude Knowledge Import")
    print("Process pre-parsed analysis from Claude Code")
    print("-" * 60)
    
    processor = ClaudeParsedProcessor()
    
    # Check for zip file argument or prompt
    import sys
    if len(sys.argv) > 1:
        zip_path = sys.argv[1]
    else:
        zip_path = input("Path to Claude-parsed zip file: ").strip()
    
    if zip_path:
        processor.process_claude_zip(zip_path)
        
        # Show Dolores's updated knowledge
        print("\n🤖 Asking Dolores what she learned...")
        task_id = ask_dolores(
            "knowledge_summary",
            "Summarize what you just learned about Jon from the Phase Zero import. What are the most important things you now know?",
            "Post-import summary"
        )
        
        result = wait_for_dolores(task_id, timeout=30)
        if result:
            print("\nDOLORES'S UNDERSTANDING:")
            print(result)
    else:
        print("No file specified")

if __name__ == "__main__":
    main()