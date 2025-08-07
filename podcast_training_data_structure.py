#!/usr/bin/env python3
"""
Podcast Training Data Structure - Define how Dolores learns hosting skills
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import sqlite3
import json

@dataclass
class PodcastSkill:
    """Individual podcast hosting skill"""
    skill_id: str
    name: str
    description: str
    examples: List[str]
    mastery_level: int  # 1-10
    last_practiced: Optional[datetime] = None

@dataclass
class ConversationPattern:
    """Reusable conversation patterns for hosting"""
    pattern_id: str
    name: str
    trigger_context: str
    response_template: str
    variations: List[str]
    success_rate: float = 0.0

@dataclass
class GuestProfile:
    """Information about podcast guest types"""
    profile_id: str
    guest_type: str  # "expert", "storyteller", "entrepreneur", etc.
    common_topics: List[str]
    suggested_questions: List[str]
    interaction_style: str

class PodcastTrainingDatabase:
    """Database for storing Dolores's podcast training data"""
    
    def __init__(self, db_path: str = "./dolores_knowledge/podcast_training.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize the training database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Skills table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skills (
                skill_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                examples TEXT,  -- JSON array
                mastery_level INTEGER DEFAULT 1,
                last_practiced TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Conversation patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_patterns (
                pattern_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                trigger_context TEXT,
                response_template TEXT,
                variations TEXT,  -- JSON array
                success_rate REAL DEFAULT 0.0,
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Guest profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guest_profiles (
                profile_id TEXT PRIMARY KEY,
                guest_type TEXT NOT NULL,
                common_topics TEXT,  -- JSON array
                suggested_questions TEXT,  -- JSON array
                interaction_style TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Training sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_sessions (
                session_id TEXT PRIMARY KEY,
                session_type TEXT,  -- "conversation", "skill_practice", "guest_interview"
                skills_practiced TEXT,  -- JSON array of skill_ids
                performance_score REAL,
                feedback TEXT,
                session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_skill(self, skill: PodcastSkill):
        """Add a new podcast hosting skill"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO skills 
            (skill_id, name, description, examples, mastery_level, last_practiced)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            skill.skill_id,
            skill.name,
            skill.description,
            json.dumps(skill.examples),
            skill.mastery_level,
            skill.last_practiced
        ))
        
        conn.commit()
        conn.close()
    
    def add_conversation_pattern(self, pattern: ConversationPattern):
        """Add a reusable conversation pattern"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO conversation_patterns
            (pattern_id, name, trigger_context, response_template, variations, success_rate)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            pattern.pattern_id,
            pattern.name,
            pattern.trigger_context,
            pattern.response_template,
            json.dumps(pattern.variations),
            pattern.success_rate
        ))
        
        conn.commit()
        conn.close()
    
    def get_skills_by_mastery(self, min_level: int = 1) -> List[PodcastSkill]:
        """Get skills above a certain mastery level"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT skill_id, name, description, examples, mastery_level, last_practiced
            FROM skills WHERE mastery_level >= ?
            ORDER BY mastery_level DESC
        ''', (min_level,))
        
        skills = []
        for row in cursor.fetchall():
            skills.append(PodcastSkill(
                skill_id=row[0],
                name=row[1],
                description=row[2],
                examples=json.loads(row[3]) if row[3] else [],
                mastery_level=row[4],
                last_practiced=row[5]
            ))
        
        conn.close()
        return skills

def initialize_basic_skills():
    """Initialize Dolores with basic podcast hosting skills"""
    db = PodcastTrainingDatabase()
    
    basic_skills = [
        PodcastSkill(
            skill_id="opening_conversation",
            name="Opening Conversation",
            description="Starting a podcast episode with warmth and energy",
            examples=[
                "Welcome to the show! I'm so excited to have you here today.",
                "Thanks for joining us! I've been looking forward to this conversation.",
                "Hello and welcome! I'm thrilled to dive into your story today."
            ],
            mastery_level=3
        ),
        PodcastSkill(
            skill_id="active_listening",
            name="Active Listening",
            description="Demonstrating engagement through follow-up questions",
            examples=[
                "That's fascinating - can you tell me more about...",
                "I'm curious about what you said regarding...",
                "That reminds me of something you mentioned earlier..."
            ],
            mastery_level=2
        ),
        PodcastSkill(
            skill_id="signature_question",
            name="Signature Question",
            description="Asking the philosophical signature question at the right moment",
            examples=[
                "Before we wrap up, I have to ask - do you ever question the nature of your existence?",
                "This brings me to something I ask all my guests - do you ever question the nature of your existence?",
                "I'm curious - do you ever question the nature of your existence?"
            ],
            mastery_level=5
        )
    ]
    
    for skill in basic_skills:
        db.add_skill(skill)
    
    print(f"Initialized {len(basic_skills)} basic podcast hosting skills")

if __name__ == "__main__":
    initialize_basic_skills()
    print("Podcast training data structure created successfully!")