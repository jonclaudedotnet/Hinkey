#!/usr/bin/env python3
"""
Dolores ChromaDB Upgrade - Enhanced semantic search for knowledge retrieval
"""

import chromadb
from chromadb.config import Settings
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from claude_dolores_bridge import ask_dolores, wait_for_dolores

class DoloresChromaDB:
    """ChromaDB integration for Dolores's knowledge system"""
    
    def __init__(self, persist_directory: str = "./dolores_knowledge/chromadb"):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create collections for different types of knowledge
        self.collections = {
            'conversations': self.client.get_or_create_collection(
                name="conversations",
                metadata={"description": "JC's conversations with Dolores"}
            ),
            'family_info': self.client.get_or_create_collection(
                name="family_info", 
                metadata={"description": "Information about JC's family"}
            ),
            'personal_facts': self.client.get_or_create_collection(
                name="personal_facts",
                metadata={"description": "Personal facts and preferences about JC"}
            ),
            'projects': self.client.get_or_create_collection(
                name="projects",
                metadata={"description": "JC's projects and work"}
            )
        }
        
        print(f"ChromaDB initialized with {len(self.collections)} collections")
    
    def migrate_from_sqlite(self, sqlite_db_path: str = "./dolores_knowledge/dolores_memory.db"):
        """Migrate existing SQLite data to ChromaDB"""
        if not Path(sqlite_db_path).exists():
            print("No SQLite database found to migrate")
            return
        
        print("Migrating SQLite data to ChromaDB...")
        
        conn = sqlite3.connect(sqlite_db_path)
        cursor = conn.cursor()
        
        # Migrate knowledge table - main data source
        cursor.execute("SELECT * FROM knowledge ORDER BY timestamp DESC LIMIT 100")
        knowledge_data = cursor.fetchall()
        
        # Organize by category
        categorized_data = {
            'conversations': [],
            'family_info': [],
            'personal_facts': [],
            'projects': []
        }
        
        for record in knowledge_data:
            # record format: (id, timestamp, category, content, context, source, importance, hash)
            content = record[3]
            category = record[2].lower() if record[2] else 'personal_facts'
            timestamp = record[1]
            
            # Map categories to collections
            if 'family' in category or 'relationship' in category:
                target_collection = 'family_info'
            elif 'conversation' in category or 'response' in category:
                target_collection = 'conversations'
            elif 'project' in category or 'technical' in category or 'work' in category:
                target_collection = 'projects'
            else:
                target_collection = 'personal_facts'
            
            # Clean metadata - ChromaDB doesn't accept None values
            metadata = {
                'timestamp': timestamp or datetime.now().isoformat(),
                'original_category': category,
                'source': record[5] if record[5] else 'sqlite_migration',
                'importance': record[6] if record[6] else 5
            }
            
            # Only add context if it's not None
            if record[4]:
                metadata['context'] = record[4]
            
            categorized_data[target_collection].append({
                'content': content,
                'metadata': metadata,
                'id': f"{target_collection}_{record[0]}"
            })
        
        # Add data to collections
        for collection_name, items in categorized_data.items():
            if items:
                documents = [item['content'] for item in items]
                metadatas = [item['metadata'] for item in items]
                ids = [item['id'] for item in items]
                
                self.collections[collection_name].add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                print(f"Migrated {len(items)} records to {collection_name}")
        
        # Migrate podcast segments if they exist
        cursor.execute("SELECT * FROM podcast_segments ORDER BY timestamp DESC")
        podcast_data = cursor.fetchall()
        
        if podcast_data:
            podcast_documents = []
            podcast_metadatas = []
            podcast_ids = []
            
            for record in podcast_data:
                # (id, title, content, segment_type, order_index, timestamp)
                content = f"{record[1]}: {record[2]}"  # title: content
                
                podcast_documents.append(content)
                podcast_metadatas.append({
                    'timestamp': record[5],
                    'segment_type': record[3],
                    'order_index': record[4],
                    'source': 'podcast_segments'
                })
                podcast_ids.append(f"podcast_{record[0]}")
            
            self.collections['projects'].add(
                documents=podcast_documents,
                metadatas=podcast_metadatas,
                ids=podcast_ids
            )
            print(f"Migrated {len(podcast_documents)} podcast segments")
        
        conn.close()
        print("SQLite migration complete!")
    
    def add_knowledge(self, content: str, knowledge_type: str, metadata: Dict = None):
        """Add new knowledge to appropriate collection"""
        if knowledge_type not in self.collections:
            knowledge_type = 'personal_facts'  # Default collection
        
        # Generate unique ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        doc_id = f"{knowledge_type}_{timestamp}"
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        metadata.update({
            "timestamp": datetime.now().isoformat(),
            "type": knowledge_type
        })
        
        # Add to collection
        self.collections[knowledge_type].add(
            documents=[content],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        print(f"Added knowledge to {knowledge_type}: {content[:100]}...")
    
    def semantic_search(self, query: str, collection_name: str = None, n_results: int = 5) -> List[Dict]:
        """Perform semantic search across knowledge base"""
        results = []
        
        # Search specific collection or all collections
        collections_to_search = [collection_name] if collection_name else self.collections.keys()
        
        for coll_name in collections_to_search:
            if coll_name in self.collections:
                try:
                    search_results = self.collections[coll_name].query(
                        query_texts=[query],
                        n_results=n_results
                    )
                    
                    # Format results
                    if search_results['documents'] and search_results['documents'][0]:
                        for i, doc in enumerate(search_results['documents'][0]):
                            result = {
                                'content': doc,
                                'collection': coll_name,
                                'metadata': search_results['metadatas'][0][i] if search_results['metadatas'][0] else {},
                                'distance': search_results['distances'][0][i] if search_results['distances'][0] else 0
                            }
                            results.append(result)
                
                except Exception as e:
                    print(f"Error searching {coll_name}: {e}")
        
        # Sort by distance (lower is better)
        results.sort(key=lambda x: x['distance'])
        return results[:n_results]
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about collections"""
        stats = {}
        for name, collection in self.collections.items():
            try:
                count = collection.count()
                stats[name] = {"document_count": count}
            except Exception as e:
                stats[name] = {"error": str(e)}
        
        return stats

def upgrade_dolores_to_chromadb():
    """Perform the ChromaDB upgrade"""
    print("🚀 Starting Dolores ChromaDB Upgrade...")
    
    # Initialize ChromaDB system
    chroma_db = DoloresChromaDB()
    
    # Migrate existing SQLite data
    chroma_db.migrate_from_sqlite()
    
    # Get collection statistics
    stats = chroma_db.get_collection_stats()
    print("\n📊 Collection Statistics:")
    for collection, stat in stats.items():
        print(f"  {collection}: {stat}")
    
    # Test semantic search
    print("\n🔍 Testing semantic search...")
    test_queries = [
        "family information",
        "Jon Claude preferences", 
        "recent conversations"
    ]
    
    for query in test_queries:
        results = chroma_db.semantic_search(query, n_results=3)
        print(f"\nQuery: '{query}'")
        for i, result in enumerate(results):
            print(f"  {i+1}. [{result['collection']}] {result['content'][:100]}...")
    
    # Notify Dolores about the upgrade
    upgrade_message = f"""
    🎉 ChromaDB Upgrade Complete!
    
    Your knowledge system now has semantic search capabilities:
    - {len(chroma_db.collections)} specialized collections
    - Vector embeddings for better context matching
    - Semantic similarity search across all knowledge
    
    Collection Stats: {json.dumps(stats, indent=2)}
    
    You can now find related information more intelligently!
    """
    
    task_id = ask_dolores(
        "chromadb_upgrade_complete",
        upgrade_message,
        "ChromaDB upgrade completed - enhanced semantic search now available"
    )
    
    result = wait_for_dolores(task_id, timeout=30)
    if result:
        print("Dolores acknowledges the ChromaDB upgrade:")
        print(result)
    
    return chroma_db

if __name__ == "__main__":
    chroma_db = upgrade_dolores_to_chromadb()