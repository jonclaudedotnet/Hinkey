"""
Dolores - An AI companion that learns everything about you and your family
"""

import json
import sqlite3
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib
from resource_manager import (
    throttle_database_operation, 
    throttle_file_operation,
    managed_database_connection,
    managed_sleep
)


class DoloresMemory:
    """Core memory system for Dolores - stores and retrieves personal knowledge"""
    
    def __init__(self, storage_path: str = "./dolores_knowledge"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Initialize database for structured knowledge
        self.db_path = self.storage_path / "dolores_memory.db"
        self._init_database()
        
        # Paths for different types of knowledge
        self.conversations_path = self.storage_path / "conversations"
        self.family_data_path = self.storage_path / "family"
        self.podcast_transcripts_path = self.storage_path / "podcasts"
        self.personal_facts_path = self.storage_path / "facts"
        
        # Create subdirectories
        for path in [self.conversations_path, self.family_data_path, 
                     self.podcast_transcripts_path, self.personal_facts_path]:
            path.mkdir(exist_ok=True)
    
    @throttle_database_operation
    def _init_database(self):
        """Initialize SQLite database for structured knowledge retrieval"""
        with managed_database_connection(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            # Knowledge entries table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    category TEXT NOT NULL,
                    content TEXT NOT NULL,
                    context TEXT,
                    source TEXT,
                    importance INTEGER DEFAULT 5,
                    hash TEXT UNIQUE
                )
            ''')
            
            # Relationships table (family connections, etc)
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
            
            # Topics table for organizing conversations
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    last_discussed DATETIME,
                    sentiment TEXT
                )
            ''')
            
            conn.commit()
    
    @throttle_database_operation
    @throttle_file_operation
    def remember(self, content: str, category: str, context: Optional[str] = None, 
                 source: str = "conversation", importance: int = 5) -> bool:
        """Store a piece of knowledge in Dolores's memory"""
        # Create hash to avoid duplicates
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        try:
            with managed_database_connection(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO knowledge (category, content, context, source, importance, hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (category, content, context, source, importance, content_hash))
                conn.commit()
            
            # Also save raw content to appropriate directory with throttling
            managed_sleep(0.01)  # Brief pause between operations
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
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
            
            return True
            
        except sqlite3.IntegrityError:
            # Content already exists
            return False
    
    @throttle_database_operation
    def recall(self, query: str, category: Optional[str] = None, 
               limit: int = 10) -> List[Dict[str, Any]]:
        """Search Dolores's memory for relevant information"""
        with managed_database_connection(str(self.db_path)) as conn:
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
            
            return results
    
    @throttle_database_operation
    def add_family_member(self, name: str, relationship: str, details: Optional[str] = None):
        """Add information about a family member"""
        with managed_database_connection(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO relationships (person1, person2, relationship_type, details)
                VALUES (?, ?, ?, ?)
            ''', ("User", name, relationship, details))
            conn.commit()
        
        # Also store as general knowledge
        self.remember(
            f"{name} is my {relationship}. {details or ''}",
            category="family",
            importance=8
        )
    
    @throttle_database_operation
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about Dolores's memory"""
        with managed_database_connection(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM knowledge")
            total_memories = cursor.fetchone()[0]
            
            cursor.execute("SELECT category, COUNT(*) FROM knowledge GROUP BY category")
            categories = dict(cursor.fetchall())
            
            cursor.execute("SELECT COUNT(*) FROM relationships")
            total_relationships = cursor.fetchone()[0]
        
        # Calculate storage used
        total_size = sum(f.stat().st_size for f in self.storage_path.rglob('*') if f.is_file())
        
        return {
            'total_memories': total_memories,
            'categories': categories,
            'total_relationships': total_relationships,
            'storage_used_mb': total_size / (1024 * 1024),
            'storage_used_gb': total_size / (1024 * 1024 * 1024)
        }


class DoloresHost:
    """The podcast host personality of Dolores"""
    
    def __init__(self, memory: DoloresMemory):
        self.memory = memory
        self.conversation_context = []
        
    def process_input(self, text: str, source: str = "conversation"):
        """Process new information from user"""
        # Extract key information
        if "my" in text.lower() or "i" in text.lower():
            self.memory.remember(text, category="personal", source=source, importance=7)
        
        # Look for family references
        family_keywords = ["mother", "father", "sister", "brother", "wife", "husband", 
                          "daughter", "son", "mom", "dad", "child", "parent"]
        for keyword in family_keywords:
            if keyword in text.lower():
                self.memory.remember(text, category="family", source=source, importance=8)
                break
        
        # Store general conversation
        self.memory.remember(text, category="general", source=source)
        
    def prepare_podcast_response(self, topic: str) -> str:
        """Prepare a response based on accumulated knowledge"""
        # Search for relevant memories
        memories = self.memory.recall(topic)
        
        if memories:
            # Build context from memories
            context = "\n".join([m['content'] for m in memories[:5]])
            return f"Based on what I know about you: {context}"
        else:
            return "Tell me more about that - I want to understand better."


# Example usage functions
def initialize_dolores():
    """Initialize Dolores with her memory system"""
    dolores_memory = DoloresMemory()
    dolores = DoloresHost(dolores_memory)
    return dolores

def teach_dolores(dolores: DoloresHost, information: str):
    """Teach Dolores something new"""
    dolores.process_input(information)
    stats = dolores.memory.get_memory_stats()
    print(f"Dolores now knows {stats['total_memories']} things")
    print(f"Using {stats['storage_used_mb']:.2f} MB of storage")