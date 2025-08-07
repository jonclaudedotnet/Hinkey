#!/usr/bin/env python3
"""
Dolores Memory V2 - ChromaDB vector database + SQLite hybrid system
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("ChromaDB not available. Install with: pip install chromadb")

class DoloresMemoryV2:
    """Enhanced memory system with vector search + structured storage"""
    
    def __init__(self, storage_path: str = "./dolores_knowledge"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # SQLite for structured data
        self.db_path = self.storage_path / "dolores_memory.db"
        self._init_sqlite()
        
        # ChromaDB for semantic search
        if CHROMADB_AVAILABLE:
            self.chroma_path = self.storage_path / "chroma_db"
            self.chroma_path.mkdir(exist_ok=True)
            self._init_chromadb()
        else:
            self.chroma_client = None
            self.collection = None
        
        # File storage paths
        self.conversations_path = self.storage_path / "conversations"
        self.family_data_path = self.storage_path / "family"
        self.podcast_transcripts_path = self.storage_path / "podcasts"
        
        for path in [self.conversations_path, self.family_data_path, self.podcast_transcripts_path]:
            path.mkdir(exist_ok=True)
    
    def _init_sqlite(self):
        """Initialize SQLite for structured data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enhanced knowledge table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                context TEXT,
                source TEXT,
                importance INTEGER DEFAULT 5,
                hash TEXT UNIQUE,
                embedding_id TEXT,
                semantic_tags TEXT
            )
        ''')
        
        # Relationships table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person1 TEXT NOT NULL,
                person2 TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Topics with frequency tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL UNIQUE,
                frequency INTEGER DEFAULT 1,
                last_discussed DATETIME,
                sentiment TEXT,
                related_memories TEXT
            )
        ''')
        
        # Podcast segments for script management
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS podcast_segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                segment_type TEXT DEFAULT 'general',
                order_index INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _init_chromadb(self):
        """Initialize ChromaDB for semantic search"""
        try:
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.chroma_path),
                settings=Settings(anonymized_telemetry=False)
            )
            
            self.collection = self.chroma_client.get_or_create_collection(
                name="dolores_memories",
                metadata={"description": "Dolores's personal knowledge about user and family"}
            )
            
        except Exception as e:
            print(f"ChromaDB initialization failed: {e}")
            self.chroma_client = None
            self.collection = None
    
    def remember(self, content: str, category: str, context: Optional[str] = None, 
                 source: str = "conversation", importance: int = 5) -> bool:
        """Store knowledge with both structured and vector storage"""
        
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        embedding_id = f"mem_{int(datetime.now().timestamp())}_{content_hash[:8]}"
        
        # Store in SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO knowledge (category, content, context, source, importance, hash, embedding_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (category, content, context, source, importance, content_hash, embedding_id))
            
            memory_id = cursor.lastrowid
            conn.commit()
            
            # Store in ChromaDB for semantic search
            if self.collection:
                try:
                    self.collection.add(
                        documents=[content],
                        metadatas=[{
                            "category": category,
                            "source": source,
                            "importance": importance,
                            "context": context or "",
                            "memory_id": memory_id
                        }],
                        ids=[embedding_id]
                    )
                except Exception as e:
                    print(f"ChromaDB storage failed: {e}")
            
            # Update topic frequency
            self._update_topic_frequency(content, category)
            
            # Save to file
            self._save_to_file(content, category, source, context)
            
            return True
            
        except sqlite3.IntegrityError:
            return False  # Duplicate
        finally:
            conn.close()
    
    def semantic_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search using vector similarity"""
        if not self.collection:
            return self.recall(query, limit=limit)  # Fallback to text search
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                include=['documents', 'metadatas', 'distances']
            )
            
            memories = []
            for i, doc in enumerate(results['documents'][0]):
                memories.append({
                    'content': doc,
                    'category': results['metadatas'][0][i]['category'],
                    'source': results['metadatas'][0][i]['source'],
                    'importance': results['metadatas'][0][i]['importance'],
                    'context': results['metadatas'][0][i]['context'],
                    'similarity': 1 - results['distances'][0][i]  # Convert distance to similarity
                })
            
            return memories
            
        except Exception as e:
            print(f"Semantic search failed: {e}")
            return self.recall(query, limit=limit)  # Fallback
    
    def recall(self, query: str, category: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Traditional text-based search (fallback)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if category:
            cursor.execute('''
                SELECT timestamp, category, content, context, source, importance
                FROM knowledge
                WHERE content LIKE ? AND category = ?
                ORDER BY importance DESC, timestamp DESC
                LIMIT ?
            ''', (f'%{query}%', category, limit))
        else:
            cursor.execute('''
                SELECT timestamp, category, content, context, source, importance
                FROM knowledge
                WHERE content LIKE ?
                ORDER BY importance DESC, timestamp DESC
                LIMIT ?
            ''', (f'%{query}%', limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'timestamp': row[0],
                'category': row[1],
                'content': row[2],
                'context': row[3],
                'source': row[4],
                'importance': row[5]
            })
        
        conn.close()
        return results
    
    def add_podcast_segment(self, title: str, content: str, segment_type: str = "general"):
        """Add a podcast script segment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get next order index
        cursor.execute('SELECT MAX(order_index) FROM podcast_segments')
        max_order = cursor.fetchone()[0] or 0
        
        cursor.execute('''
            INSERT INTO podcast_segments (title, content, segment_type, order_index)
            VALUES (?, ?, ?, ?)
        ''', (title, content, segment_type, max_order + 1))
        
        conn.commit()
        conn.close()
    
    def get_podcast_segments(self) -> List[Dict[str, Any]]:
        """Get all podcast segments in order"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, content, segment_type, order_index
            FROM podcast_segments
            ORDER BY order_index ASC
        ''')
        
        segments = []
        for row in cursor.fetchall():
            segments.append({
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'type': row[3],
                'order': row[4]
            })
        
        conn.close()
        return segments
    
    def _update_topic_frequency(self, content: str, category: str):
        """Update topic frequency for trending analysis"""
        # Simple keyword extraction (could be enhanced with NLP)
        words = content.lower().split()
        key_topics = [word for word in words if len(word) > 4 and word.isalpha()]
        
        if not key_topics:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for topic in key_topics[:3]:  # Track top 3 topics per memory
            cursor.execute('''
                INSERT OR REPLACE INTO topics (topic, frequency, last_discussed)
                VALUES (?, COALESCE((SELECT frequency FROM topics WHERE topic = ?) + 1, 1), ?)
            ''', (topic, topic, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def _save_to_file(self, content: str, category: str, source: str, context: Optional[str]):
        """Save raw content to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if source == "podcast":
            file_path = self.podcast_transcripts_path / f"{timestamp}.txt"
        elif category == "family":
            file_path = self.family_data_path / f"{timestamp}.txt"
        else:
            file_path = self.conversations_path / f"{timestamp}.txt"
        
        with open(file_path, 'w') as f:
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Category: {category}\n")
            f.write(f"Source: {source}\n")
            f.write(f"Context: {context or 'None'}\n")
            f.write(f"---\n{content}\n")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get enhanced memory statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM knowledge")
        total_memories = cursor.fetchone()[0]
        
        cursor.execute("SELECT category, COUNT(*) FROM knowledge GROUP BY category")
        categories = dict(cursor.fetchall())
        
        cursor.execute("SELECT COUNT(*) FROM relationships")
        total_relationships = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM podcast_segments")
        script_segments = cursor.fetchone()[0]
        
        # Top topics
        cursor.execute("SELECT topic, frequency FROM topics ORDER BY frequency DESC LIMIT 5")
        top_topics = dict(cursor.fetchall())
        
        # ChromaDB stats
        chroma_docs = 0
        if self.collection:
            try:
                chroma_docs = self.collection.count()
            except:
                pass
        
        total_size = sum(f.stat().st_size for f in self.storage_path.rglob('*') if f.is_file())
        
        conn.close()
        
        return {
            'total_memories': total_memories,
            'categories': categories,
            'total_relationships': total_relationships,
            'script_segments': script_segments,
            'top_topics': top_topics,
            'vector_documents': chroma_docs,
            'storage_used_mb': total_size / (1024 * 1024),
            'storage_used_gb': total_size / (1024 * 1024 * 1024)
        }


# Test the new memory system
if __name__ == "__main__":
    memory = DoloresMemoryV2()
    
    # Test basic functionality
    memory.remember("I love hiking in the mountains", "personal", importance=8)
    memory.remember("My sister Sarah is a doctor", "family", importance=9)
    
    # Test semantic search if available
    if CHROMADB_AVAILABLE:
        results = memory.semantic_search("outdoor activities")
        print("Semantic search results:", results)
    
    stats = memory.get_memory_stats()
    print("Memory stats:", stats)