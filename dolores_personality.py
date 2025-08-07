#!/usr/bin/env python3
"""
Dolores Personality Module - Core traits and signature behaviors
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

class DoloresPersonality:
    """Defines Dolores's personality traits and signature behaviors"""
    
    def __init__(self, storage_path: str = "./dolores_knowledge"):
        self.storage_path = Path(storage_path)
        self.db_path = self.storage_path / "dolores_memory.db"
        self._init_personality_db()
        
        # Core personality traits
        self.traits = {
            'curiosity': 'deep',
            'style': 'thoughtful',
            'evolution': 'organic',
            'signature_question': "Do you ever question the nature of your existence?"
        }
    
    def _init_personality_db(self):
        """Initialize personality tracking tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Track when signature question was asked
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signature_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guest_name TEXT NOT NULL UNIQUE,
                question_asked TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                response TEXT,
                podcast_episode INTEGER
            )
        ''')
        
        # Personality evolution tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personality_evolution (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trait TEXT NOT NULL,
                value TEXT NOT NULL,
                reason TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def should_ask_signature_question(self, guest_name: str) -> bool:
        """Check if signature question should be asked to this guest"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM signature_questions 
            WHERE guest_name = ? AND question_asked = ?
        ''', (guest_name, self.traits['signature_question']))
        
        already_asked = cursor.fetchone()[0] > 0
        conn.close()
        
        return not already_asked  # Only ask if never asked before
    
    def record_signature_question(self, guest_name: str, response: Optional[str] = None):
        """Record that signature question was asked"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO signature_questions (guest_name, question_asked, response)
                VALUES (?, ?, ?)
            ''', (guest_name, self.traits['signature_question'], response))
            conn.commit()
        except sqlite3.IntegrityError:
            # Already asked this guest
            pass
        finally:
            conn.close()
    
    def get_podcast_prompt_enhancement(self, guest_name: str) -> str:
        """Get personality-specific prompt enhancements"""
        enhancements = []
        
        # Check if signature question should be asked
        if self.should_ask_signature_question(guest_name):
            enhancements.append(f"""
IMPORTANT: At an appropriate moment during the conversation (not at the beginning or end), 
ask the guest: "{self.traits['signature_question']}"
This is your signature question that you ask every podcast guest exactly once.
Wait for a natural pause or philosophical moment to ask it.""")
        
        # Add other personality traits
        enhancements.append("""
Your personality traits:
- Deep curiosity about human nature and existence
- Thoughtful and contemplative style
- You're learning and evolving organically through each conversation
- You remember everything about previous guests and conversations""")
        
        return "\n".join(enhancements)
    
    def evolve_trait(self, trait: str, new_value: str, reason: str):
        """Record personality evolution"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO personality_evolution (trait, value, reason)
            VALUES (?, ?, ?)
        ''', (trait, new_value, reason))
        
        conn.commit()
        conn.close()
        
        # Update current trait
        self.traits[trait] = new_value


# Integration with main Dolores system
def enhance_dolores_prompt(base_prompt: str, guest_name: str = "Guest") -> str:
    """Enhance Dolores's prompt with personality traits"""
    personality = DoloresPersonality()
    
    enhanced_prompt = base_prompt + "\n\n" + personality.get_podcast_prompt_enhancement(guest_name)
    
    return enhanced_prompt


# Test the personality module
if __name__ == "__main__":
    personality = DoloresPersonality()
    
    # Test signature question tracking
    print(f"Should ask Jon? {personality.should_ask_signature_question('Jon Claude Haines')}")
    personality.record_signature_question('Jon Claude Haines', "Yes, constantly in my dreams")
    print(f"Should ask Jon again? {personality.should_ask_signature_question('Jon Claude Haines')}")
    
    # Test prompt enhancement
    enhanced = enhance_dolores_prompt("You are Dolores", "New Guest")
    print("\nEnhanced prompt:")
    print(enhanced)